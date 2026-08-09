from venditus.adapters.fake import FakeCatalogAdapter
from venditus.models import Causa, CorrecaoProposta, Diagnostico
from venditus.nodes import criar_investigador
from venditus.seed import CATALOGO
from venditus.state import estado_inicial
from tests.fakes import FakeLLM


def _diag() -> Diagnostico:
    return Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE, confianca="alta",
        evidencia="Membrana impermeável",
        correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
    )


def test_investigador_grava_o_diagnostico():
    llm = FakeLLM(_diag())
    saida = criar_investigador(llm, FakeCatalogAdapter(CATALOGO))(
        estado_inicial("tênis impermeável", 340)
    )
    assert saida["diagnostico"].causa == Causa.ATRIBUTO_AUSENTE
    assert saida["status"] == "diagnosticado"


def test_prompt_inclui_termo_e_catalogo():
    llm = FakeLLM(_diag())
    criar_investigador(llm, FakeCatalogAdapter(CATALOGO))(
        estado_inicial("tênis impermeável", 340)
    )
    assert "tênis impermeável" in llm.prompt_recebido
    assert "SKU-4471" in llm.prompt_recebido
    # A descrição precisa estar no prompt: é a evidência que o modelo cita.
    assert "Membrana impermeável" in llm.prompt_recebido
