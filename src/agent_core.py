"""Cerebro do agente: combina regras locais com decisao final pelo Gemini."""

from pathlib import Path
import re
from typing import Any, Dict, Optional

from .auditor import ExpenseAuditor, AuditResult
from .blueprint_parser import BlueprintRules, load_blueprint
from .gemini_client import GeminiDecisionError, GeminiExpenseDecisionClient
from .validators import mascarar_dados_sensiveis, sanitizar_despesa_para_llm, validar_decisao_llm


MANUAL_REVIEW_LABELS = {"REVISÃO MANUAL", "REVISAO MANUAL"}


class AgentCore:
    def __init__(self, blueprint_path: Path, gemini_client: GeminiExpenseDecisionClient | None = None):
        self.blueprint_path = blueprint_path
        self.gemini_client = gemini_client or GeminiExpenseDecisionClient()

    def analyze_expense(self, expense: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa uma despesa, priorizando Gemini e usando fallback local quando preciso."""
        blueprint_text = self.blueprint_path.read_text(encoding="utf-8")
        rules = load_blueprint(self.blueprint_path)
        auditor = ExpenseAuditor(rules)
        fallback_result = auditor.audit(expense)

        media_cep: Optional[float] = None
        if str(expense.get("category", "")).strip().lower() == "hospedagem":
            cep = expense.get("metadata", {}).get("cep", "")
            if cep:
                media_cep = auditor._get_media_regional_por_cep(cep)

        prompt = self._build_prompt(blueprint_text, expense, media_cep, fallback_result)

        try:
            llm_payload = self.gemini_client.analyze(prompt)
            validated_payload = validar_decisao_llm(llm_payload)
            audit_result = self._build_result_from_gemini(validated_payload, rules, fallback_result)
            decision_source = "gemini"
            decision_detail = "Analise concluida com apoio do motor principal de decisao."
        except (GeminiDecisionError, ValueError, RuntimeError) as exc:
            audit_result = self._build_polished_fallback_result(fallback_result)
            decision_source = "fallback_local"
            decision_detail = f"Analise concluida pelo fluxo local de contingencia: {exc}"

        return {
            "audit_result": audit_result,
            "decision_source": decision_source,
            "decision_detail": decision_detail,
            "gemini_enabled": self.gemini_client.is_configured(),
        }

    def is_gemini_configured(self) -> bool:
        return self.gemini_client.is_configured()

    def _build_prompt(
        self,
        blueprint_text: str,
        expense: Dict[str, Any],
        media_cep: Optional[float],
        fallback_result: AuditResult,
    ) -> str:
        safe_expense = sanitizar_despesa_para_llm(expense)
        prompt_parts = [
            "Voce e um auditor corporativo especialista em reembolso de despesas.",
            "Sua decisao final deve respeitar diretrizes corporativas textuais e criterios operacionais objetivos.",
            "Responda somente em JSON valido seguindo exatamente o schema solicitado.",
            "A comunicacao para o usuario final deve ser polida, profissional, clara e comercial.",
            "Nao mencione blueprint, prompt, modelo, IA, fallback, ferramenta interna, arquivo, sistema ou mecanismo interno.",
            "",
            "# Diretrizes corporativas vigentes",
            blueprint_text.strip(),
            "",
            "# Despesa a ser analisada",
            str(safe_expense),
            "",
            "# Referencias operacionais de apoio",
            f"status_local_sugerido={fallback_result.status}",
            f"motivo_local_sugerido={fallback_result.reason}",
        ]

        if media_cep is not None:
            prompt_parts.extend(
                [
                    f"referencia_hospedagem_regional={media_cep:.2f}",
                    "Considere essa referencia regional no criterio de hospedagem.",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "# Regras obrigatorias para sua resposta",
                "1. Nunca exponha numero completo de cartao, CPF, chave ou segredo.",
                "2. Se estiver incerto, se faltar contexto, ou se a resposta nao puder ser confiavel, marque needs_manual_review=true.",
                "3. Use status APROVADA, REPROVADA, REPROVADA - O valor excede o limite estabelecido no Blueprint, ou REVISÃO MANUAL.",
                "4. confidence deve ser um numero entre 0 e 1.",
                "5. used_cep_tool deve ser true apenas quando a analise de hospedagem considerar a referencia regional.",
                "6. response deve ser uma mensagem curta em portugues, com tom executivo, cordial e comercial.",
                "7. reason e policy_summary devem explicar o criterio de negocio sem citar arquivos, engenharia interna ou governanca tecnica.",
            ]
        )

        return "\n".join(prompt_parts)

    def _build_result_from_gemini(
        self,
        payload: Dict[str, Any],
        rules: BlueprintRules,
        fallback_result: AuditResult,
    ) -> AuditResult:
        status = payload["status"]
        confidence = payload["confidence"]

        if payload["needs_manual_review"] or confidence < 0.75 or status in MANUAL_REVIEW_LABELS:
            return self._manual_review_result(rules, payload)

        if (
            fallback_result.status == "REPROVADA - O valor excede o limite estabelecido no Blueprint"
            and status == "REPROVADA"
        ):
            status = fallback_result.status

        reason = self._polish_business_text(payload["reason"])
        policy_summary = self._polish_business_text(payload["policy_summary"])
        user_response = self._polish_business_text(payload["response"])

        composed_response = (
            f"Status: {status}\n"
            f"Motivo: {reason}\n"
            f"Criterio aplicado: {policy_summary}\n"
            f"Mensagem ao solicitante: {user_response}"
        )

        return AuditResult(
            status=status,
            reason=reason,
            response=mascarar_dados_sensiveis(composed_response),
            rules_used=rules,
        )

    def _manual_review_result(self, rules: BlueprintRules, payload: Dict[str, Any]) -> AuditResult:
        reason = self._polish_business_text(
            payload.get("reason") or "Nao houve elementos suficientes para concluir a analise com seguranca."
        )
        response = (
            f"Status: {rules.fallback_status}\n"
            f"Motivo: {reason}\n"
            "Mensagem ao solicitante: Sua despesa foi encaminhada para uma revisao complementar, a fim de garantir uma avaliacao precisa e segura."
        )
        return AuditResult(
            status=rules.fallback_status,
            reason=reason,
            response=mascarar_dados_sensiveis(response),
            rules_used=rules,
        )

    def _build_polished_fallback_result(self, fallback_result: AuditResult) -> AuditResult:
        status = fallback_result.status
        reason = self._polish_business_text(fallback_result.reason)

        if status == "APROVADA":
            message = "Sua despesa esta em conformidade com os criterios vigentes e foi aprovada para continuidade do processo."
            criterion = "Valor e informacoes apresentados dentro dos parametros esperados para a categoria."
        elif status == "REPROVADA - O valor excede o limite estabelecido no Blueprint":
            message = "No momento, nao foi possivel aprovar a despesa, pois o valor informado excede o limite previsto para esta categoria."
            criterion = "Valor acima do teto financeiro aplicavel a esta solicitacao."
        elif status == "REPROVADA":
            message = "No momento, nao foi possivel aprovar a despesa com as informacoes apresentadas."
            criterion = "A solicitacao nao atende integralmente aos criterios exigidos para aprovacao."
        else:
            message = "Sua despesa foi direcionada para revisao complementar, garantindo uma avaliacao mais segura e precisa."
            criterion = "Foi necessario encaminhamento para avaliacao adicional."

        response = (
            f"Status: {status}\n"
            f"Motivo: {reason}\n"
            f"Criterio aplicado: {criterion}\n"
            f"Mensagem ao solicitante: {message}"
        )

        return AuditResult(
            status=status,
            reason=reason,
            response=mascarar_dados_sensiveis(response),
            rules_used=fallback_result.rules_used,
        )

    def _polish_business_text(self, text: str) -> str:
        polished = mascarar_dados_sensiveis(str(text).strip())
        replacements = [
            (r"\bBlueprint\b", "politica corporativa"),
            (r"\bblueprint\b", "politica corporativa"),
            (r"\bprompt\b", "analise"),
            (r"\bfallback\b", "contingencia"),
            (r"\btool\b", "consulta de referencia"),
            (r"\bferramenta\b", "consulta de referencia"),
            (r"\bmodelo\b", "processo de analise"),
            (r"\bIA\b", "analise automatizada"),
            (r"\bia\b", "analise automatizada"),
            (r"\bsistema\b", "processo"),
            (r"\barquivo\b", "diretriz corporativa"),
        ]
        for pattern, replacement in replacements:
            polished = re.sub(pattern, replacement, polished)

        polished = re.sub(r"\s+", " ", polished).strip()
        return polished
