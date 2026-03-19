"""Utilities used by the auditor."""

import unicodedata
from typing import Optional


def mask_sensitive(value: Optional[str], keep: int = 4) -> str:
    """Mask all but the last `keep` characters."""
    if not value:
        return ""
    s = str(value).strip()
    if len(s) <= keep:
        return s
    return "*" * (len(s) - keep) + s[-keep:]


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).strip().lower()
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def normalize_category(category: Optional[str]) -> str:
    normalized = _normalize_text(category)
    if not normalized:
        return ""

    alimentacao_aliases = {
        "alimentacao",
        "almoco de negocios",
        "almoco negocios",
        "jantar de negocios",
        "jantar negocios",
    }
    hospedagem_aliases = {
        "hospedagem",
        "viagem",
    }

    if normalized in alimentacao_aliases:
        return "alimentacao"
    if normalized in hospedagem_aliases:
        return "hospedagem"
    return normalized
