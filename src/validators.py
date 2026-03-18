"""Validações de segurança e mascaramento de dados sensíveis."""

import re


CARD_PATTERN = re.compile(r"(?:\d[ -]?){13,19}\d")


def mascarar_dados_sensiveis(texto: str) -> str:
    """Ofusca números de cartão de crédito deixando apenas os últimos 4 dígitos.

    Exemplo:
        "Cartão 4532 1111 2222 3333" -> "Cartão **** **** **** 3333"

    A função preserva espaços e hífens do formato original.
    """

    def _mask_match(match: re.Match) -> str:
        block = match.group(0)
        digits = [c for c in block if c.isdigit()]
        keep = 4
        masked_digits = []
        for i, d in enumerate(digits):
            if i < len(digits) - keep:
                masked_digits.append("*")
            else:
                masked_digits.append(d)

        # Reconstruct mantendo separadores (espaços/hífens)
        result = []
        digit_idx = 0
        for ch in block:
            if ch.isdigit():
                result.append(masked_digits[digit_idx])
                digit_idx += 1
            else:
                result.append(ch)
        return "".join(result)

    return CARD_PATTERN.sub(_mask_match, texto)
