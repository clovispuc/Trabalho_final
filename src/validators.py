"""Validacoes de seguranca e mascaramento de dados sensiveis."""

from copy import deepcopy
import re
from typing import Any, Dict


CARD_PATTERN = re.compile(r"(?:\d[ -]?){13,19}\d")
CPF_PATTERN = re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")


def _mask_digits_preserving_format(block: str, keep: int = 4) -> str:
    digits = [c for c in block if c.isdigit()]
    if len(digits) <= keep:
        return block

    masked_digits = []
    for idx, digit in enumerate(digits):
        if idx < len(digits) - keep:
            masked_digits.append("*")
        else:
            masked_digits.append(digit)

    rebuilt = []
    digit_idx = 0
    for ch in block:
        if ch.isdigit():
            rebuilt.append(masked_digits[digit_idx])
            digit_idx += 1
        else:
            rebuilt.append(ch)
    return "".join(rebuilt)


def mascarar_dados_sensiveis(texto: str) -> str:
    """Ofusca cartoes e CPF, preservando o formato visual original."""
    if not texto:
        return ""

    masked = CARD_PATTERN.sub(lambda match: _mask_digits_preserving_format(match.group(0), keep=4), texto)
    masked = CPF_PATTERN.sub(lambda match: _mask_digits_preserving_format(match.group(0), keep=2), masked)
    return masked


def sanitizar_despesa_para_llm(expense: Dict[str, Any]) -> Dict[str, Any]:
    """Cria uma copia segura da despesa para envio ao provedor externo."""
    sanitized = deepcopy(expense)

    def _walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: _walk(item) for key, item in value.items()}
        if isinstance(value, list):
            return [_walk(item) for item in value]
        if isinstance(value, str):
            return mascarar_dados_sensiveis(value)
        return value

    return _walk(sanitized)


def validar_decisao_llm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Valida e normaliza a estrutura JSON retornada pela IA."""
    required_fields = {
        "status",
        "reason",
        "response",
        "confidence",
        "needs_manual_review",
        "policy_summary",
    }

    missing = required_fields.difference(payload.keys())
    if missing:
        raise ValueError(f"Campos obrigatorios ausentes na resposta da IA: {sorted(missing)}")

    normalized = dict(payload)
    normalized["status"] = str(normalized["status"]).strip()
    normalized["reason"] = mascarar_dados_sensiveis(str(normalized["reason"]).strip())
    normalized["response"] = mascarar_dados_sensiveis(str(normalized["response"]).strip())
    normalized["policy_summary"] = mascarar_dados_sensiveis(str(normalized["policy_summary"]).strip())
    normalized["confidence"] = float(normalized["confidence"])
    normalized["needs_manual_review"] = bool(normalized["needs_manual_review"])
    normalized["used_cep_tool"] = bool(normalized.get("used_cep_tool", False))

    allowed_statuses = {
        "APROVADA",
        "REPROVADA",
        "REPROVADA - O valor excede o limite estabelecido no Blueprint",
        "REVISAO MANUAL",
        "REVISÃO MANUAL",
    }
    if normalized["status"] not in allowed_statuses:
        raise ValueError(f"Status invalido retornado pela IA: {normalized['status']}")

    if not 0.0 <= normalized["confidence"] <= 1.0:
        raise ValueError("O campo confidence deve estar entre 0.0 e 1.0")

    return normalized
