"""Auditor de despesas baseado em regras carregadas do blueprint."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .blueprint_parser import BlueprintRules
from .tools import normalize_category


@dataclass
class AuditResult:
    status: str
    reason: str
    response: str
    rules_used: BlueprintRules


class ExpenseAuditor:
    def __init__(self, rules: BlueprintRules):
        self.rules = rules

    def audit(self, expense: Dict[str, Any]) -> AuditResult:
        category = normalize_category(expense.get("category"))
        amount = float(expense.get("amount", 0))
        metadata = expense.get("metadata", {})

        # Fallback for unknown categories
        if category not in {"alimentacao", "hospedagem"}:
            status = self.rules.fallback_status
            reason = f"Categoria desconhecida: {category}" if category else "Categoria não informada"
            response = self._build_response(status, reason, approved=False)
            return AuditResult(status=status, reason=reason, response=response, rules_used=self.rules)

        if category == "alimentacao":
            return self._audit_alimentacao(amount)

        if category == "hospedagem":
            cep = metadata.get("cep")
            return self._audit_hospedagem(amount, cep)

        # Should not reach here
        return AuditResult(status=self.rules.fallback_status, reason="Regra não aplicada", response="", rules_used=self.rules)

    def _audit_alimentacao(self, amount: float) -> AuditResult:
        limit = self.rules.alimentacao_limite
        if limit is None:
            status = self.rules.fallback_status
            reason = "Limite de alimentação não definido no Blueprint."
            return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=False), rules_used=self.rules)

        if amount <= limit:
            status = "APROVADA"
            reason = f"Valor dentro do limite de R$ {limit:.2f}."
            return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=True), rules_used=self.rules)

        status = "REPROVADA - O valor excede o limite estabelecido no Blueprint"
        reason = f"Despesa de R$ {amount:.2f} excede o limite de R$ {limit:.2f}."
        return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=False), rules_used=self.rules)

    def _audit_hospedagem(self, amount: float, cep: Optional[str]) -> AuditResult:
        if not self.rules.hospedagem_deve_usar_cep:
            status = self.rules.fallback_status
            reason = "Regra de hospedagem não está configurada corretamente."
            return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=False), rules_used=self.rules)

        if not cep:
            status = "REPROVADA"
            reason = "CEP não informado para cálculo do limite de hospedagem."
            return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=False), rules_used=self.rules)

        # Ferramenta simulada de busca por CEP.
        avg = self._get_media_regional_por_cep(cep)
        limit = avg * (self.rules.hospedagem_multiplicador or 1.0)

        if amount <= limit:
            status = "APROVADA"
            reason = f"Valor dentro do limite de R$ {limit:.2f} (média regional: R$ {avg:.2f})."
            return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=True), rules_used=self.rules)

        status = "REPROVADA"
        reason = f"Despesa de R$ {amount:.2f} excede o limite de R$ {limit:.2f} (média regional: R$ {avg:.2f})."
        return AuditResult(status=status, reason=reason, response=self._build_response(status, reason, approved=False), rules_used=self.rules)

    def _get_media_regional_por_cep(self, cep: str) -> float:
        """Simula ferramenta de busca de média de hospedagem por CEP.

        A ideia é que qualquer alteração em `blueprint.md` que mencione CEP
        deve acionar esta 'ferramenta'.
        """
        # Determinista: derivamos um valor da string do CEP para testes.
        digits = "".join(ch for ch in cep if ch.isdigit())
        if not digits:
            return 200.0
        base = sum(int(d) for d in digits) % 120 + 80
        return float(base)

    def _build_response(self, status: str, reason: str, approved: bool) -> str:
        if approved:
            tone = self.rules.personalidade_aprovada
            template = "Despesa aprovada com base nas políticas internas."
        else:
            tone = self.rules.personalidade_reprovada
            template = "Despesa reprovada conforme as regras do Blueprint."

        return (
            f"Status: {status}\n"
            f"Motivo: {reason}\n"
            f"Estilo: {tone}\n"
            f"{template}"
        )
