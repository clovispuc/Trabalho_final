"""Cérebro do agente: lê o blueprint a cada análise e simula chamada de LLM."""

from pathlib import Path
from typing import Any, Dict, Optional

from .auditor import ExpenseAuditor, AuditResult
from .blueprint_parser import load_blueprint
from .validators import mascarar_dados_sensiveis


class AgentCore:
    def __init__(self, blueprint_path: Path):
        self.blueprint_path = blueprint_path

    def analyze_expense(self, expense: Dict[str, Any]) -> Dict[str, Any]:
        """Analisa uma despesa lendo o blueprint do disco sempre que chamado."""
        blueprint_text = self.blueprint_path.read_text(encoding="utf-8")
        rules = load_blueprint(self.blueprint_path)

        # Aplica regras com auditor (hot-reload: nova instância a cada chamada).
        auditor = ExpenseAuditor(rules)
        result: AuditResult = auditor.audit(expense)

        # Se for hospedagem, inclui resultado do mock de CEP.
        media_cep: Optional[float] = None
        if str(expense.get("category", "")).strip().lower() == "hospedagem":
            cep = expense.get("metadata", {}).get("cep", "")
            if cep:
                # Mantem o debug do prompt alinhado com a regra efetiva do auditor.
                media_cep = auditor._get_media_regional_por_cep(cep)

        prompt = self._build_prompt(blueprint_text, expense, media_cep)
        llm_response = self._simulate_llm(prompt)

        return {
            "audit_result": result,
            "llm_prompt": prompt,
            "llm_response": llm_response,
        }

    def _build_prompt(self, blueprint_text: str, expense: Dict[str, Any], media_cep: Optional[float]) -> str:
        expense_copy = dict(expense)
        sensitive_card = expense_copy.get("sensitive", {}).get("card", "")
        if sensitive_card:
            expense_copy["sensitive"]["card"] = mascarar_dados_sensiveis(sensitive_card)

        prompt_parts = [
            "# Blueprint (Conteúdo atual do arquivo)",
            blueprint_text.strip(),
            "",
            "# Despesa a ser analisada",
            str(expense_copy),
        ]

        if media_cep is not None:
            prompt_parts.append("")
            prompt_parts.append("# Resultado do mock de CEP")
            prompt_parts.append(f"Média de hospedagem encontrada (mock): R$ {media_cep:.2f}")

        prompt_parts.append("")
        prompt_parts.append("# Instruções para o LLM")
        prompt_parts.append(
            "Baseie-se nas regras do Blueprint para decidir se a despesa deve ser APROVADA ou REPROVADA. "
            "Explique claramente a regra violada, se houver."
        )

        return "\n".join(prompt_parts)

    def _simulate_llm(self, prompt: str) -> str:
        """Simula uma chamada de LLM retornando uma resposta baseada no prompt."""
        # Para manter o mock simples, retornamos um resumo das regras em 1 frase.
        # Em um sistema real, aqui você chamaria a API do OpenAI/Google/etc.
        return (
            "[LLM SIMULADO] Eu li as regras no blueprint, analisei a despesa e "
            "determinei o status com base nas políticas definidas. "
            "(Prompt gerado para a LLM em anexo.)"
        )
