"""Utilities used by the auditor."""

from typing import Optional


def mask_sensitive(value: Optional[str], keep: int = 4) -> str:
    """Mask all but the last `keep` characters."""
    if not value:
        return ""
    s = str(value).strip()
    if len(s) <= keep:
        return s
    return "*" * (len(s) - keep) + s[-keep:]


def normalize_category(category: Optional[str]) -> str:
    if not category:
        return ""
    return category.strip().lower()
