import hashlib


def fix_id(sku: str, campo: str, valor: str) -> str:
    """Identificador determinístico de uma correção.

    Retomar de um interrupt() re-executa o nó inteiro. Este identificador
    permite ao executor detectar que a correção já foi aplicada e não repetir
    a escrita.
    """
    bruto = f"{sku}|{campo}|{valor}".encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()[:16]
