"""Parse and represent rules from blueprint.md.

O parser aqui é intencionalmente simples: ele extrai valores e regras
baseadas em padrões textuais presentes no arquivo. O importante é que o
comportamento mude quando `blueprint.md` for editado;
"""

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class BlueprintRules:
    alimentacao_limite: Optional[float] = None
    hospedagem_multiplicador: Optional[float] = None
    hospedagem_deve_usar_cep: bool = False
    personalidade_aprovada: str = "formal e educada"
    personalidade_reprovada: str = "empática, mas firme"
    lgpd_mask_digits: int = 4
    fallback_status: str = "REVISÃO MANUAL"


def _float_from_str(s: str) -> Optional[float]:
    if not s:
        return None
    s = s.replace("R$", "").replace("$", "").replace(" ", "")
    s = s.replace("/", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def _normalize(text: str) -> str:
    """Normaliza texto para facilitar matching robusto."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def load_blueprint(path: Path) -> BlueprintRules:
    text = path.read_text(encoding="utf-8")
    normalized = _normalize(text).lower()
    rules = BlueprintRules()

    # Alimentacao: permite formatos narrativos diversos no blueprint.
    m = re.search(r"alimentacao.{0,180}?r\$\s*([0-9]+(?:[.,][0-9]{1,2})?)", normalized, re.DOTALL)
    if m:
        rules.alimentacao_limite = _float_from_str(m.group(1))

    # Hospedagem: exige uso de CEP + percentual acima da media.
    if "hospedagem" in normalized and "cep" in normalized:
        rules.hospedagem_deve_usar_cep = True
    m2 = re.search(r"([0-9]{1,3})\s*%\s*acima da media", normalized)
    if m2:
        rules.hospedagem_multiplicador = 1 + float(m2.group(1)) / 100.0

    # Personalidade: suporta formato "Aprovada ... Reprovada ...".
    m3 = re.search(r"aprovad[a-z].{0,200}?formal.{0,80}?educad[a-z]", normalized, re.DOTALL)
    if m3:
        rules.personalidade_aprovada = "formal e educada"
    m3b = re.search(r"reprovad[a-z].{0,200}?empatic[a-z].{0,80}?firme", normalized, re.DOTALL)
    if m3b:
        rules.personalidade_reprovada = "empática, mas firme"

    # Segurança (LGPD)
    if "lgpd" in normalized:
        m_digits = re.search(r"(\d+)\s+ultim", normalized)
        if m_digits:
            rules.lgpd_mask_digits = int(m_digits.group(1))

    # Fallback
    m4 = re.search(r"`([^`]+)`", text)
    if m4 and "REVIS" in m4.group(1).upper():
        rules.fallback_status = m4.group(1)
    m4b = re.search(r"fallback.{0,180}?revis[a-z ]*manual", normalized, re.DOTALL)
    if m4b:
        rules.fallback_status = "REVISÃO MANUAL"
    m4c = re.search(r"Fallback: Se a categoria for desconhecida, classificar como '(.+?)'", text)
    if m4c:
        rules.fallback_status = m4c.group(1)

    return rules
