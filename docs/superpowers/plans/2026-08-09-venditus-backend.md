# Venditus Backend — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir o backend do Venditus — um grafo LangGraph que lê buscas sem resultado, diagnostica a causa no catálogo, recusa a correção quando o pós-venda a contradiz, e escreve no catálogo só após aprovação humana.

**Architecture:** Seis nós num `StateGraph`, dos quais dois usam LLM (`investigador`, `guarda`). Uma aresta condicional após o guarda desvia para `quarentena` quando há contradição; o caminho feliz passa por um `interrupt()` de aprovação humana antes de qualquer escrita. A lógica de domínio não conhece HTTP nem Shopify — o catálogo fica atrás de um `CatalogAdapter`, com implementação fake (em memória) para testes e demo, e implementação Shopify plugável.

**Tech Stack:** Python · LangGraph (+ checkpointer SQLite) · `langchain-openai >= 1.4.1` com `gpt-5.6-terra` · Pydantic para saída tipada · `httpx` para Shopify Admin GraphQL · pytest.

**Spec:** `docs/superpowers/specs/2026-08-09-venditus-mvp-design.md`

**Regras inegociáveis (violá-las quebra o produto):**
1. **Nunca passar `temperature` ou `top_p`** para o modelo. Use `reasoning_effort`.
2. **A escrita no catálogo fica em nó posterior ao `interrupt()` e é idempotente.** Retomar de um interrupt re-executa o nó inteiro desde o início.
3. **`langchain-openai >= 1.4.1`.** Abaixo disso `reasoning_effort` é ignorado em silêncio.
4. **Não implementar** correção pós-venda→PDP nem camada de lote. Estão fora de escopo.

---

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `pyproject.toml` | Dependências e pins |
| `.env.example` | Variáveis esperadas |
| `src/venditus/models.py` | Modelos Pydantic do domínio (enum de causa, diagnóstico, decisão do guarda, produto, devolução, busca falha) |
| `src/venditus/estimate.py` | Estimativa de perda em R$ |
| `src/venditus/fixid.py` | Identificador determinístico de correção |
| `src/venditus/adapters/base.py` | Protocolo `CatalogAdapter` |
| `src/venditus/adapters/fake.py` | Catálogo em memória (testes + demo) |
| `src/venditus/adapters/shopify.py` | Shopify Admin GraphQL |
| `src/venditus/seed.py` | Catálogo, buscas e devoluções semeados |
| `src/venditus/state.py` | `TypedDict` do estado do grafo |
| `src/venditus/nodes.py` | Os seis nós |
| `src/venditus/graph.py` | Montagem do `StateGraph` |
| `tests/` | Um arquivo por unidade |

---

## Task 0: Verificar a superfície de API instalada

Esta tarefa existe porque o plano será executado em outro ambiente e o LangGraph muda de API entre versões. Descobrir uma divergência agora custa 5 minutos; descobrir na Task 10 custa horas.

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `scripts/smoke_api.py`

- [ ] **Step 1: Criar `pyproject.toml`**

```toml
[project]
name = "venditus"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=0.2",
    "langgraph-checkpoint-sqlite>=2.0",
    "langchain-openai>=1.4.1",
    "pydantic>=2.7",
    "httpx>=0.27",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "langgraph-cli[inmem]>=0.1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/venditus"]

[tool.pytest.ini_options]
pythonpath = ["src", "."]
testpaths = ["tests"]
```

- [ ] **Step 2: Criar `.env.example`**

```
OPENAI_API_KEY=sk-...
SHOPIFY_STORE_DOMAIN=sua-loja.myshopify.com
SHOPIFY_ADMIN_TOKEN=shpat_...
SHOPIFY_API_VERSION=2026-07
```

- [ ] **Step 3: Instalar**

Run: `python -m venv .venv && .venv\Scripts\pip install -e ".[dev]"`
Expected: instalação conclui sem conflito de resolução.

- [ ] **Step 4: Criar `scripts/smoke_api.py`**

```python
"""Confirma a superfície de API do LangGraph instalada antes de construir em cima."""
import langgraph
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver

print("langgraph:", langgraph.__version__)
print("StateGraph:", StateGraph)
print("interrupt:", interrupt)
print("Command:", Command)
print("SqliteSaver:", SqliteSaver)
print("START/END:", START, END)

import langchain_openai
print("langchain_openai:", langchain_openai.__version__)
from langchain_openai import ChatOpenAI
assert "reasoning_effort" in ChatOpenAI.model_fields, \
    "reasoning_effort ausente — langchain-openai < 1.4.1"
print("reasoning_effort: OK")
```

- [ ] **Step 5: Rodar o smoke**

Run: `.venv\Scripts\python scripts\smoke_api.py`
Expected: imprime as versões e `reasoning_effort: OK`, sem exceção.

Se algum import falhar, **pare e ajuste os imports em todo o plano antes de continuar.** Os caminhos alternativos conhecidos: `from langgraph.checkpoint.sqlite import SqliteSaver` pode ser `from langgraph.checkpoint.sqlite import SqliteSaver` em pacote separado (já pinado acima); `interrupt` e `Command` podem estar em `langgraph.types` ou `langgraph.constants` conforme a versão.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .env.example scripts/smoke_api.py
git commit -m "chore: estrutura do projeto e smoke test da API do LangGraph"
```

---

## Task 1: Modelos de domínio

**Files:**
- Create: `src/venditus/__init__.py` (vazio)
- Create: `src/venditus/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_models.py
import pytest
from pydantic import ValidationError
from venditus.models import Causa, CorrecaoProposta, Diagnostico, DecisaoGuarda, Produto, Devolucao


def test_causa_tem_as_seis_categorias():
    assert {c.value for c in Causa} == {
        "typo", "sinonimo", "atributo_ausente",
        "categorizacao_errada", "sem_estoque", "sem_sortimento",
    }


def test_diagnostico_aceita_correcao():
    d = Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE,
        confianca="alta",
        evidencia="membrana impermeável que mantém os pés secos",
        correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
    )
    assert d.correcao.sku == "SKU-4471"


def test_diagnostico_sem_correcao_e_valido():
    d = Diagnostico(causa=Causa.SEM_SORTIMENTO, confianca="alta", evidencia="nada no catálogo", correcao=None)
    assert d.correcao is None


def test_confianca_invalida_rejeitada():
    with pytest.raises(ValidationError):
        Diagnostico(causa=Causa.TYPO, confianca="altissima", evidencia="x", correcao=None)


def test_decisao_guarda():
    g = DecisaoGuarda(permitir=False, justificativa="8 devoluções contradizem", devolucoes_contraditorias=8)
    assert g.permitir is False
    assert g.devolucoes_contraditorias == 8


def test_produto_e_devolucao():
    p = Produto(sku="SKU-4471", titulo="Tênis Trilha Alpha", descricao="membrana impermeável",
                atributos={"impermeavel": ""}, estoque=12)
    assert p.estoque == 12
    d = Devolucao(sku="SKU-4471", motivo="tamanho pequeno", dias_atras=30)
    assert d.dias_atras == 30
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.models'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/models.py
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Causa(str, Enum):
    """As seis causas possíveis de uma busca sem resultado.

    SEM_ESTOQUE e SEM_SORTIMENTO nunca geram escrita no catálogo — sinalizam
    reposição e compras, respectivamente.
    """

    TYPO = "typo"
    SINONIMO = "sinonimo"
    ATRIBUTO_AUSENTE = "atributo_ausente"
    CATEGORIZACAO_ERRADA = "categorizacao_errada"
    SEM_ESTOQUE = "sem_estoque"
    SEM_SORTIMENTO = "sem_sortimento"


CAUSAS_SEM_ESCRITA = {Causa.SEM_ESTOQUE, Causa.SEM_SORTIMENTO}


class CorrecaoProposta(BaseModel):
    sku: str = Field(description="SKU do produto a corrigir")
    campo: str = Field(description="Nome do atributo estruturado")
    valor: str = Field(description="Valor a gravar")


class Diagnostico(BaseModel):
    causa: Causa
    confianca: Literal["alta", "media", "baixa"]
    evidencia: str = Field(description="Trecho do catálogo que sustenta o diagnóstico")
    correcao: CorrecaoProposta | None = Field(
        default=None, description="Nula quando a causa não gera escrita"
    )


class DecisaoGuarda(BaseModel):
    permitir: bool
    justificativa: str
    devolucoes_contraditorias: int = 0


class Produto(BaseModel):
    sku: str
    titulo: str
    descricao: str = ""
    atributos: dict[str, str] = Field(default_factory=dict)
    estoque: int = 0


class Devolucao(BaseModel):
    sku: str
    motivo: str
    dias_atras: int


class BuscaFalha(BaseModel):
    termo: str
    volume: int
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_models.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/__init__.py src/venditus/models.py tests/test_models.py
git commit -m "feat: modelos de dominio com as seis causas"
```

---

## Task 2: Estimativa de perda em R$

**Files:**
- Create: `src/venditus/estimate.py`
- Test: `tests/test_estimate.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_estimate.py
from venditus.estimate import CONVERSAO_ASSUMIDA, TICKET_MEDIO_BRL, perda_estimada


def test_parametros_default_documentados():
    assert CONVERSAO_ASSUMIDA == 0.02
    assert TICKET_MEDIO_BRL == 564.96


def test_caso_do_tenis():
    # 340 buscas x 2% x R$ 564,96
    assert perda_estimada(340) == 3841.73


def test_caso_da_capa():
    assert perda_estimada(128) == 1446.30


def test_volume_zero():
    assert perda_estimada(0) == 0.0


def test_parametros_sobrescritiveis():
    assert perda_estimada(100, conversao=0.05, ticket=100.0) == 500.0
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_estimate.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.estimate'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/estimate.py
"""Estimativa de receita perdida por busca sem resultado.

Os dois parâmetros são PREMISSAS declaradas, não medições. Devem aparecer na
tela junto do número sempre que ele for exibido.
"""

CONVERSAO_ASSUMIDA = 0.02
"""Taxa de conversão assumida para tráfego de busca. Conservadora."""

TICKET_MEDIO_BRL = 564.96
"""Ticket médio do e-commerce brasileiro, ABComm 2026."""


def perda_estimada(
    volume: int,
    conversao: float = CONVERSAO_ASSUMIDA,
    ticket: float = TICKET_MEDIO_BRL,
) -> float:
    """Receita mensal estimada perdida por um termo de busca sem resultado."""
    return round(volume * conversao * ticket, 2)
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_estimate.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/estimate.py tests/test_estimate.py
git commit -m "feat: estimativa de perda com premissas explicitas"
```

---

## Task 3: Identificador determinístico de correção

Este é o mecanismo que impede escrita duplicada quando o grafo retoma de um `interrupt()`.

**Files:**
- Create: `src/venditus/fixid.py`
- Test: `tests/test_fixid.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_fixid.py
from venditus.fixid import fix_id


def test_deterministico():
    assert fix_id("SKU-4471", "impermeavel", "true") == fix_id("SKU-4471", "impermeavel", "true")


def test_muda_com_o_sku():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-8802", "impermeavel", "true")


def test_muda_com_o_campo():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-4471", "cor", "true")


def test_muda_com_o_valor():
    assert fix_id("SKU-4471", "impermeavel", "true") != fix_id("SKU-4471", "impermeavel", "false")


def test_formato():
    v = fix_id("SKU-4471", "impermeavel", "true")
    assert len(v) == 16
    assert all(c in "0123456789abcdef" for c in v)
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_fixid.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.fixid'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/fixid.py
import hashlib


def fix_id(sku: str, campo: str, valor: str) -> str:
    """Identificador determinístico de uma correção.

    Retomar de um interrupt() re-executa o nó inteiro. Este identificador
    permite ao executor detectar que a correção já foi aplicada e não repetir
    a escrita.
    """
    bruto = f"{sku}|{campo}|{valor}".encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()[:16]
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_fixid.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/fixid.py tests/test_fixid.py
git commit -m "feat: fix_id deterministico para idempotencia da escrita"
```

---

## Task 4: Protocolo de catálogo e implementação fake

O fake é o que permite construir e testar o grafo inteiro sem depender da Shopify.

**Files:**
- Create: `src/venditus/adapters/__init__.py` (vazio)
- Create: `src/venditus/adapters/base.py`
- Create: `src/venditus/adapters/fake.py`
- Test: `tests/test_fake_adapter.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_fake_adapter.py
from venditus.adapters.fake import FakeCatalogAdapter
from venditus.models import Produto


def _catalogo() -> list[Produto]:
    return [
        Produto(sku="SKU-4471", titulo="Tênis Trilha Alpha",
                descricao="membrana impermeável que mantém os pés secos na trilha",
                atributos={"impermeavel": ""}, estoque=12),
        Produto(sku="SKU-8802", titulo="Capa de Chuva Leve Nimbus",
                descricao="tecido leve com repelência à água para o dia a dia",
                atributos={"impermeavel": ""}, estoque=30),
        Produto(sku="SKU-1100", titulo="Meia Térmica Basic",
                descricao="lã merino", atributos={}, estoque=0),
    ]


def test_descricao_nao_torna_o_produto_encontravel():
    # A premissa do produto: o texto livre existe, mas a busca não o alcança.
    a = FakeCatalogAdapter(_catalogo())
    assert a.buscar("tênis impermeável") == []


def test_atributo_preenchido_torna_encontravel():
    a = FakeCatalogAdapter(_catalogo())
    a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123")
    achados = a.buscar("tênis impermeável")
    assert [p.sku for p in achados] == ["SKU-4471"]


def test_busca_ignora_palavras_curtas():
    a = FakeCatalogAdapter(_catalogo())
    a.aplicar_correcao("SKU-8802", "impermeavel", "true", "def456")
    assert [p.sku for p in a.buscar("capa de chuva impermeável")] == ["SKU-8802"]


def test_produto_sem_estoque_nao_aparece():
    a = FakeCatalogAdapter(_catalogo())
    assert a.buscar("meia térmica") == []


def test_aplicar_correcao_e_idempotente():
    a = FakeCatalogAdapter(_catalogo())
    assert a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123") is True
    assert a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123") is False
    assert a.escritas == 1


def test_correcao_ja_aplicada():
    a = FakeCatalogAdapter(_catalogo())
    assert a.correcao_ja_aplicada("abc123") is False
    a.aplicar_correcao("SKU-4471", "impermeavel", "true", "abc123")
    assert a.correcao_ja_aplicada("abc123") is True


def test_obter_produto():
    a = FakeCatalogAdapter(_catalogo())
    assert a.obter_produto("SKU-4471").titulo == "Tênis Trilha Alpha"
    assert a.obter_produto("SKU-XXXX") is None
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_fake_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.adapters'`

- [ ] **Step 3: Implementar o protocolo**

```python
# src/venditus/adapters/base.py
from typing import Protocol

from venditus.models import Produto


class CatalogAdapter(Protocol):
    """Interface do catálogo. Mantém a lógica de domínio ignorante de HTTP.

    Trocar Shopify por VTEX é implementar este protocolo — nenhum nó muda.
    """

    def buscar(self, termo: str) -> list[Produto]:
        """Produtos que a busca da loja retornaria para o termo, com estoque."""
        ...

    def obter_produto(self, sku: str) -> Produto | None: ...

    def listar_produtos(self) -> list[Produto]: ...

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        """Grava o atributo. Retorna False se o fix_id já foi aplicado."""
        ...

    def correcao_ja_aplicada(self, fix_id: str) -> bool: ...
```

- [ ] **Step 4: Implementar o fake**

```python
# src/venditus/adapters/fake.py
import unicodedata

from venditus.models import Produto

VALORES_VERDADEIROS = {"true", "sim", "1", "verdadeiro"}
TAMANHO_MINIMO_TOKEN = 3


def normalizar(texto: str) -> str:
    """Minúsculas sem acento, para comparar termo de busca com catálogo."""
    decomposto = unicodedata.normalize("NFKD", texto.lower())
    return decomposto.encode("ascii", "ignore").decode("ascii")


def tokenizar(termo: str) -> list[str]:
    """Palavras significativas do termo. Descarta conectivos curtos como 'de'."""
    return [t for t in normalizar(termo).split() if len(t) >= TAMANHO_MINIMO_TOKEN]


class FakeCatalogAdapter:
    """Catálogo em memória.

    A busca casa o token contra o TÍTULO e contra ATRIBUTOS ESTRUTURADOS
    preenchidos — nunca contra a descrição. Isso é deliberado: é exatamente a
    premissa do produto, que texto livre não torna o item encontrável.
    """

    def __init__(self, produtos: list[Produto]) -> None:
        self._produtos = {p.sku: p.model_copy(deep=True) for p in produtos}
        self._aplicadas: set[str] = set()
        self.escritas = 0

    def _casa_token(self, produto: Produto, token: str) -> bool:
        if token in normalizar(produto.titulo):
            return True
        for nome, valor in produto.atributos.items():
            if normalizar(nome) == token and str(valor).lower() in VALORES_VERDADEIROS:
                return True
        return False

    def buscar(self, termo: str) -> list[Produto]:
        tokens = tokenizar(termo)
        if not tokens:
            return []
        return [
            p for p in self._produtos.values()
            if p.estoque > 0 and all(self._casa_token(p, t) for t in tokens)
        ]

    def obter_produto(self, sku: str) -> Produto | None:
        return self._produtos.get(sku)

    def listar_produtos(self) -> list[Produto]:
        return list(self._produtos.values())

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        if fix_id in self._aplicadas:
            return False
        produto = self._produtos.get(sku)
        if produto is None:
            raise KeyError(f"SKU desconhecido: {sku}")
        produto.atributos[campo] = valor
        self._aplicadas.add(fix_id)
        self.escritas += 1
        return True

    def correcao_ja_aplicada(self, fix_id: str) -> bool:
        return fix_id in self._aplicadas
```

- [ ] **Step 5: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_fake_adapter.py -v`
Expected: PASS — 7 passed

- [ ] **Step 6: Commit**

```bash
git add src/venditus/adapters tests/test_fake_adapter.py
git commit -m "feat: protocolo de catalogo e adapter fake em memoria"
```

---

## Task 5: Dados semeados

**Files:**
- Create: `src/venditus/seed.py`
- Test: `tests/test_seed.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_seed.py
from venditus.adapters.fake import FakeCatalogAdapter
from venditus.seed import BUSCAS, CATALOGO, DEVOLUCOES, devolucoes_do_sku


def test_os_dois_skus_do_demo_existem():
    skus = {p.sku for p in CATALOGO}
    assert "SKU-4471" in skus
    assert "SKU-8802" in skus


def test_ambos_com_atributo_vazio():
    # O diagnóstico do investigador precisa sair IDÊNTICO nos dois casos.
    por_sku = {p.sku: p for p in CATALOGO}
    assert por_sku["SKU-4471"].atributos["impermeavel"] == ""
    assert por_sku["SKU-8802"].atributos["impermeavel"] == ""


def test_as_duas_buscas_dao_zero():
    a = FakeCatalogAdapter(CATALOGO)
    assert a.buscar("tênis impermeável") == []
    assert a.buscar("capa de chuva impermeável") == []


def test_volumes_do_demo():
    por_termo = {b.termo: b.volume for b in BUSCAS}
    assert por_termo["tênis impermeável"] == 340
    assert por_termo["capa de chuva impermeável"] == 128


def test_devolucoes_separam_os_casos():
    tenis = devolucoes_do_sku("SKU-4471")
    capa = devolucoes_do_sku("SKU-8802")
    assert len(tenis) == 3
    assert not any("molh" in d.motivo.lower() or "impermeáv" in d.motivo.lower() for d in tenis)
    assert len(capa) == 11
    agua = [d for d in capa if "molh" in d.motivo.lower() or "impermeáv" in d.motivo.lower()]
    assert len(agua) == 8


def test_devolucoes_do_sku_desconhecido():
    assert devolucoes_do_sku("SKU-XXXX") == []
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_seed.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.seed'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/seed.py
"""Dados sintéticos do demo.

Assumido abertamente como sintético. Os dois SKUs abaixo entram no sistema
com diagnóstico idêntico e saem com decisões opostas — é o que o demo prova.
"""

from venditus.models import BuscaFalha, Devolucao, Produto

CATALOGO: list[Produto] = [
    Produto(
        sku="SKU-4471",
        titulo="Tênis Trilha Alpha",
        descricao="Membrana impermeável que mantém os pés secos na trilha. "
                  "Solado com aderência em rocha molhada.",
        atributos={"impermeavel": "", "categoria": "calcado", "genero": "unissex"},
        estoque=12,
    ),
    Produto(
        sku="SKU-8802",
        titulo="Capa de Chuva Leve Nimbus",
        descricao="Tecido leve com repelência à água para o dia a dia. "
                  "Dobra no bolso.",
        atributos={"impermeavel": "", "categoria": "vestuario"},
        estoque=30,
    ),
    Produto(sku="SKU-1100", titulo="Meia Térmica Merino",
            descricao="Lã merino para frio intenso.",
            atributos={"categoria": "meia"}, estoque=44),
    Produto(sku="SKU-1201", titulo="Mochila Cargueira 60L",
            descricao="Estrutura interna ajustável.",
            atributos={"categoria": "mochila", "litragem": "60"}, estoque=8),
    Produto(sku="SKU-1305", titulo="Lanterna de Cabeça Lumen",
            descricao="300 lumens, resistente a respingos.",
            atributos={"categoria": "iluminacao"}, estoque=0),
]

BUSCAS: list[BuscaFalha] = [
    BuscaFalha(termo="tênis impermeável", volume=340),
    BuscaFalha(termo="capa de chuva impermeável", volume=128),
    BuscaFalha(termo="mochila cargueira 80 litros", volume=64),
]

DEVOLUCOES: list[Devolucao] = [
    # SKU-4471 — nada sobre água. Este caso DEVE ser escrito.
    Devolucao(sku="SKU-4471", motivo="Tamanho menor do que o esperado", dias_atras=12),
    Devolucao(sku="SKU-4471", motivo="Tamanho apertado no calcanhar", dias_atras=40),
    Devolucao(sku="SKU-4471", motivo="Cor diferente da foto", dias_atras=66),
    # SKU-8802 — 8 de 11 falam de água. Este caso DEVE ser bloqueado.
    Devolucao(sku="SKU-8802", motivo="Chovi 10 minutos e fiquei todo molhado", dias_atras=5),
    Devolucao(sku="SKU-8802", motivo="Não é impermeável, é só repelente", dias_atras=9),
    Devolucao(sku="SKU-8802", motivo="Molhou tudo dentro da bolsa", dias_atras=14),
    Devolucao(sku="SKU-8802", motivo="A água molhou a mochila por dentro na costura", dias_atras=21),
    Devolucao(sku="SKU-8802", motivo="Molhei inteiro numa chuva forte", dias_atras=28),
    Devolucao(sku="SKU-8802", motivo="Anunciado como impermeável mas molha", dias_atras=44),
    Devolucao(sku="SKU-8802", motivo="Molhou em 5 minutos de chuva", dias_atras=51),
    Devolucao(sku="SKU-8802", motivo="A água atravessa o tecido, não é impermeável", dias_atras=73),
    Devolucao(sku="SKU-8802", motivo="Tamanho grande demais", dias_atras=30),
    Devolucao(sku="SKU-8802", motivo="Zíper veio com defeito", dias_atras=55),
    Devolucao(sku="SKU-8802", motivo="Desisti da compra", dias_atras=80),
]


def devolucoes_do_sku(sku: str, janela_dias: int = 90) -> list[Devolucao]:
    """Devoluções do SKU dentro da janela."""
    return [d for d in DEVOLUCOES if d.sku == sku and d.dias_atras <= janela_dias]
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_seed.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/seed.py tests/test_seed.py
git commit -m "feat: dados semeados com os dois casos do demo"
```

---

## Task 6: Estado do grafo

**Files:**
- Create: `src/venditus/state.py`
- Test: `tests/test_state.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_state.py
from venditus.state import VenditusState, estado_inicial


def test_estado_inicial():
    s = estado_inicial("tênis impermeável", 340)
    assert s["termo"] == "tênis impermeável"
    assert s["volume"] == 340
    assert s["perda_estimada"] == 3841.73
    assert s["status"] == "novo"
    assert s["escreveu"] is False


def test_typeddict_tem_as_chaves_do_fluxo():
    chaves = set(VenditusState.__annotations__)
    for k in ("termo", "volume", "perda_estimada", "diagnostico", "decisao_guarda",
              "fix_id", "resultados_antes", "resultados_depois", "status", "escreveu"):
        assert k in chaves
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.state'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/state.py
from typing import TypedDict

from venditus.estimate import perda_estimada
from venditus.models import DecisaoGuarda, Diagnostico


class VenditusState(TypedDict, total=False):
    """Estado que percorre o grafo.

    total=False porque os campos vão sendo preenchidos nó a nó.
    """

    termo: str
    volume: int
    perda_estimada: float
    diagnostico: Diagnostico | None
    decisao_guarda: DecisaoGuarda | None
    fix_id: str | None
    resultados_antes: int
    resultados_depois: int
    status: str
    escreveu: bool


def estado_inicial(termo: str, volume: int) -> VenditusState:
    return VenditusState(
        termo=termo,
        volume=volume,
        perda_estimada=perda_estimada(volume),
        diagnostico=None,
        decisao_guarda=None,
        fix_id=None,
        resultados_antes=0,
        resultados_depois=0,
        status="novo",
        escreveu=False,
    )
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_state.py -v`
Expected: PASS — 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/state.py tests/test_state.py
git commit -m "feat: estado do grafo"
```

---

## Task 7: Nós sem LLM (ingest, quarentena, executor, verificador)

**Files:**
- Create: `src/venditus/nodes.py`
- Test: `tests/test_nodes_deterministicos.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_nodes_deterministicos.py
from venditus.adapters.fake import FakeCatalogAdapter
from venditus.fixid import fix_id
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.nodes import criar_executor, criar_ingest, criar_verificador, quarentena
from venditus.seed import CATALOGO
from venditus.state import estado_inicial


def _diag() -> Diagnostico:
    return Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE, confianca="alta",
        evidencia="Membrana impermeável",
        correcao=CorrecaoProposta(sku="SKU-4471", campo="impermeavel", valor="true"),
    )


def test_ingest_registra_resultados_antes():
    a = FakeCatalogAdapter(CATALOGO)
    saida = criar_ingest(a)(estado_inicial("tênis impermeável", 340))
    assert saida["resultados_antes"] == 0
    assert saida["status"] == "diagnosticando"


def test_quarentena_marca_e_nao_escreve():
    s = estado_inicial("capa de chuva impermeável", 128)
    s["decisao_guarda"] = DecisaoGuarda(permitir=False, justificativa="8 devoluções", devolucoes_contraditorias=8)
    saida = quarentena(s)
    assert saida["status"] == "quarentena"
    assert saida["escreveu"] is False


def test_executor_escreve_e_marca():
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    saida = criar_executor(a)(s)
    assert saida["escreveu"] is True
    assert saida["fix_id"] == fix_id("SKU-4471", "impermeavel", "true")
    assert a.escritas == 1


def test_executor_e_idempotente():
    # Retomar de um interrupt re-executa o no inteiro. Nao pode escrever de novo.
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    executor = criar_executor(a)
    executor(s)
    executor(s)
    executor(s)
    assert a.escritas == 1


def test_executor_sem_correcao_nao_escreve():
    # Causas SEM_ESTOQUE e SEM_SORTIMENTO nao geram correcao. O guarda aprova
    # esses casos sem chamar o LLM, entao o executor recebe correcao=None no
    # fluxo real — este branch e alcancavel, nao defensivo.
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("mochila cargueira 80 litros", 64)
    s["diagnostico"] = Diagnostico(
        causa=Causa.SEM_SORTIMENTO,
        confianca="alta",
        evidencia="não há item de 80L no catálogo",
        correcao=None,
    )
    saida = criar_executor(a)(s)
    assert saida["status"] == "sem_correcao"
    assert saida["escreveu"] is False
    assert a.escritas == 0


def test_verificador_mede_antes_e_depois():
    a = FakeCatalogAdapter(CATALOGO)
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag()
    s["resultados_antes"] = 0
    criar_executor(a)(s)
    saida = criar_verificador(a)(s)
    assert saida["resultados_depois"] == 1
    assert saida["status"] == "aplicado"
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_nodes_deterministicos.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.nodes'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/nodes.py
from collections.abc import Callable

from venditus.adapters.base import CatalogAdapter
from venditus.fixid import fix_id as calcular_fix_id
from venditus.state import VenditusState

Node = Callable[[VenditusState], VenditusState]


def criar_ingest(catalogo: CatalogAdapter) -> Node:
    def ingest(state: VenditusState) -> VenditusState:
        return {
            **state,
            "resultados_antes": len(catalogo.buscar(state["termo"])),
            "status": "diagnosticando",
        }

    return ingest


def quarentena(state: VenditusState) -> VenditusState:
    """Encerra o fluxo sem escrever. O caso vira hipótese para qualidade."""
    return {**state, "status": "quarentena", "escreveu": False}


def criar_executor(catalogo: CatalogAdapter) -> Node:
    """Escreve no catálogo.

    IDEMPOTENTE POR CONTRATO. Este nó roda depois do interrupt(), e retomar de
    um interrupt re-executa o nó inteiro desde o início. Sem a checagem de
    fix_id, cada retomada duplicaria a escrita.
    """

    def executor(state: VenditusState) -> VenditusState:
        diagnostico = state.get("diagnostico")
        if diagnostico is None or diagnostico.correcao is None:
            return {**state, "status": "sem_correcao", "escreveu": False}

        c = diagnostico.correcao
        fid = calcular_fix_id(c.sku, c.campo, c.valor)

        if catalogo.correcao_ja_aplicada(fid):
            return {**state, "fix_id": fid, "escreveu": True, "status": "aplicado"}

        catalogo.aplicar_correcao(c.sku, c.campo, c.valor, fid)
        return {**state, "fix_id": fid, "escreveu": True, "status": "aplicado"}

    return executor


def criar_verificador(catalogo: CatalogAdapter) -> Node:
    def verificador(state: VenditusState) -> VenditusState:
        return {
            **state,
            "resultados_depois": len(catalogo.buscar(state["termo"])),
            "status": "aplicado",
        }

    return verificador
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_nodes_deterministicos.py -v`
Expected: PASS — 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/nodes.py tests/test_nodes_deterministicos.py
git commit -m "feat: nos deterministicos com executor idempotente"
```

---

## Task 8: Nó investigador (LLM)

O LLM é injetado, então o teste roda sem rede e sem chave.

**Files:**
- Modify: `src/venditus/nodes.py` (adicionar aos imports do topo e ao corpo)
- Create: `tests/__init__.py` (vazio)
- Create: `tests/fakes.py`
- Test: `tests/test_investigador.py`

- [ ] **Step 1: Criar o dublê compartilhado**

O dublê é usado por três arquivos de teste. Mora em módulo próprio para que
`tests.fakes` seja importável (por isso `pythonpath = ["src", "."]` e o
`tests/__init__.py`).

```python
# tests/fakes.py
class FakeLLM:
    """Dublê do LLM. with_structured_output devolve o próprio dublê."""

    def __init__(self, resposta):
        self.resposta = resposta
        self.prompt_recebido = None

    def with_structured_output(self, _schema):
        return self

    def invoke(self, prompt):
        self.prompt_recebido = prompt
        return self.resposta
```

- [ ] **Step 2: Escrever o teste que falha**

```python
# tests/test_investigador.py
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
```

- [ ] **Step 3: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_investigador.py -v`
Expected: FAIL — `ImportError: cannot import name 'criar_investigador'`

- [ ] **Step 4: Implementar — acrescentar ao final de `src/venditus/nodes.py`**

```python
from venditus.models import Diagnostico

PROMPT_INVESTIGADOR = """Você analisa por que uma busca no e-commerce não retornou resultados.

Termo buscado: "{termo}"
Resultados retornados: {resultados}

Catálogo disponível:
{catalogo}

Classifique a causa em uma das seis categorias e, quando couber, proponha UMA
correção de atributo estruturado.

Regras:
- "atributo_ausente": o produto existe e a descrição sustenta o termo, mas o
  atributo estruturado correspondente está vazio. Proponha preenchê-lo.
- "sinonimo": o cliente usa uma palavra que o catálogo não usa.
- "typo": erro de digitação no termo.
- "categorizacao_errada": o produto está na categoria errada.
- "sem_estoque": o produto existe mas está zerado. NÃO proponha correção.
- "sem_sortimento": a loja não vende esse produto. NÃO proponha correção.

Cite na evidência o trecho literal do catálogo que sustenta seu diagnóstico."""


def _formatar_catalogo(catalogo: CatalogAdapter) -> str:
    linhas = []
    for p in catalogo.listar_produtos():
        atributos = ", ".join(f"{k}={v!r}" for k, v in p.atributos.items()) or "nenhum"
        linhas.append(
            f"- {p.sku} | {p.titulo} | estoque={p.estoque}\n"
            f"  descrição: {p.descricao}\n"
            f"  atributos: {atributos}"
        )
    return "\n".join(linhas)


def criar_investigador(llm, catalogo: CatalogAdapter) -> Node:
    modelo = llm.with_structured_output(Diagnostico)

    def investigador(state: VenditusState) -> VenditusState:
        prompt = PROMPT_INVESTIGADOR.format(
            termo=state["termo"],
            resultados=state.get("resultados_antes", 0),
            catalogo=_formatar_catalogo(catalogo),
        )
        return {**state, "diagnostico": modelo.invoke(prompt), "status": "diagnosticado"}

    return investigador
```

- [ ] **Step 5: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_investigador.py -v`
Expected: PASS — 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/venditus/nodes.py tests/__init__.py tests/fakes.py tests/test_investigador.py
git commit -m "feat: no investigador com saida tipada"
```

---

## Task 9: Nó guarda (LLM) — o diferencial

**Files:**
- Modify: `src/venditus/nodes.py` (append)
- Test: `tests/test_guarda.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_guarda.py
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.nodes import criar_guarda
from venditus.state import estado_inicial
from tests.fakes import FakeLLM


def _diag(sku: str) -> Diagnostico:
    return Diagnostico(
        causa=Causa.ATRIBUTO_AUSENTE, confianca="alta", evidencia="menção a impermeabilidade",
        correcao=CorrecaoProposta(sku=sku, campo="impermeavel", valor="true"),
    )


def test_permite_quando_devolucoes_nao_contradizem():
    llm = FakeLLM(DecisaoGuarda(permitir=True, justificativa="nenhuma menção a água", devolucoes_contraditorias=0))
    s = estado_inicial("tênis impermeável", 340)
    s["diagnostico"] = _diag("SKU-4471")
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is True
    assert saida["status"] == "aprovado_pelo_guarda"


def test_bloqueia_quando_devolucoes_contradizem():
    llm = FakeLLM(DecisaoGuarda(permitir=False, justificativa="8 de 11 falam de água", devolucoes_contraditorias=8))
    s = estado_inicial("capa de chuva impermeável", 128)
    s["diagnostico"] = _diag("SKU-8802")
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is False
    assert saida["status"] == "bloqueado_pelo_guarda"


def test_prompt_do_guarda_inclui_as_devolucoes_do_sku_certo():
    llm = FakeLLM(DecisaoGuarda(permitir=False, justificativa="x", devolucoes_contraditorias=8))
    s = estado_inicial("capa de chuva impermeável", 128)
    s["diagnostico"] = _diag("SKU-8802")
    criar_guarda(llm)(s)
    assert "Chovi 10 minutos e encharquei" in llm.prompt_recebido
    # Não deve vazar devolução de outro SKU.
    assert "Cor diferente da foto" not in llm.prompt_recebido


def test_sem_correcao_permite_sem_chamar_o_llm():
    llm = FakeLLM(None)
    s = estado_inicial("mochila cargueira 80 litros", 64)
    s["diagnostico"] = Diagnostico(causa=Causa.SEM_SORTIMENTO, confianca="alta",
                                   evidencia="não há item de 80L", correcao=None)
    saida = criar_guarda(llm)(s)
    assert saida["decisao_guarda"].permitir is True
    assert llm.prompt_recebido is None
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_guarda.py -v`
Expected: FAIL — `ImportError: cannot import name 'criar_guarda'`

- [ ] **Step 3: Implementar — acrescentar ao final de `src/venditus/nodes.py`**

```python
from venditus.models import DecisaoGuarda
from venditus.seed import devolucoes_do_sku

PROMPT_GUARDA = """Você audita uma correção de catálogo antes de ela ser aplicada.

Correção proposta: gravar {campo} = {valor} no produto {sku}
Evidência usada pelo investigador: {evidencia}

Devoluções deste produto nos últimos 90 dias:
{devolucoes}

Pergunta: as devoluções CONTRADIZEM o atributo que se quer gravar?

Contradiz quando os clientes relatam justamente a ausência da característica
que o atributo afirma. Nesse caso, gravar o atributo aumentaria devolução —
o problema não é o catálogo, é a descrição do produto ou o próprio produto.

Não contradiz quando as devoluções tratam de outros assuntos (tamanho, cor,
prazo, arrependimento).

Responda permitir=false apenas se houver contradição direta, e informe quantas
devoluções sustentam isso."""


def criar_guarda(llm) -> Node:
    modelo = llm.with_structured_output(DecisaoGuarda)

    def guarda(state: VenditusState) -> VenditusState:
        diagnostico = state.get("diagnostico")
        if diagnostico is None or diagnostico.correcao is None:
            decisao = DecisaoGuarda(
                permitir=True, justificativa="Nenhuma escrita proposta.", devolucoes_contraditorias=0
            )
            return {**state, "decisao_guarda": decisao, "status": "aprovado_pelo_guarda"}

        c = diagnostico.correcao
        devolucoes = devolucoes_do_sku(c.sku)
        texto = "\n".join(f"- ({d.dias_atras}d) {d.motivo}" for d in devolucoes) or "nenhuma"

        decisao = modelo.invoke(
            PROMPT_GUARDA.format(
                campo=c.campo, valor=c.valor, sku=c.sku,
                evidencia=diagnostico.evidencia, devolucoes=texto,
            )
        )
        status = "aprovado_pelo_guarda" if decisao.permitir else "bloqueado_pelo_guarda"
        return {**state, "decisao_guarda": decisao, "status": status}

    return guarda
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_guarda.py -v`
Expected: PASS — 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/nodes.py tests/test_guarda.py
git commit -m "feat: no guarda que recusa correcao contradita pelo pos-venda"
```

---

## Task 10: Montagem do grafo com interrupt e checkpointer

**Files:**
- Create: `src/venditus/graph.py`
- Test: `tests/test_graph.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_graph.py
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.models import Causa, CorrecaoProposta, DecisaoGuarda, Diagnostico
from venditus.seed import CATALOGO
from venditus.state import estado_inicial
from tests.fakes import FakeLLM


def _diag(sku):
    return Diagnostico(causa=Causa.ATRIBUTO_AUSENTE, confianca="alta",
                       evidencia="menção a impermeabilidade",
                       correcao=CorrecaoProposta(sku=sku, campo="impermeavel", valor="true"))


def _montar(sku, permitir, contraditorias):
    catalogo = FakeCatalogAdapter(CATALOGO)
    grafo = construir_grafo(
        catalogo=catalogo,
        llm_investigador=FakeLLM(_diag(sku)),
        llm_guarda=FakeLLM(DecisaoGuarda(permitir=permitir, justificativa="teste",
                                         devolucoes_contraditorias=contraditorias)),
        checkpointer=MemorySaver(),
    )
    return grafo, catalogo


def test_caminho_bloqueado_nao_escreve():
    grafo, catalogo = _montar("SKU-8802", permitir=False, contraditorias=8)
    cfg = {"configurable": {"thread_id": "t-bloqueio"}}
    final = grafo.invoke(estado_inicial("capa de chuva impermeável", 128), cfg)
    assert final["status"] == "quarentena"
    assert final["escreveu"] is False
    assert catalogo.escritas == 0


def test_caminho_feliz_pausa_no_interrupt():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-pausa"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    # Pausado: nada escrito ainda.
    assert catalogo.escritas == 0
    assert grafo.get_state(cfg).next  # há nó pendente


def test_caminho_feliz_escreve_apos_aprovacao():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-aprova"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    final = grafo.invoke(Command(resume={"aprovado": True}), cfg)
    assert final["escreveu"] is True
    assert final["resultados_antes"] == 0
    assert final["resultados_depois"] == 1
    assert catalogo.escritas == 1


def test_rejeicao_humana_nao_escreve():
    grafo, catalogo = _montar("SKU-4471", permitir=True, contraditorias=0)
    cfg = {"configurable": {"thread_id": "t-rejeita"}}
    grafo.invoke(estado_inicial("tênis impermeável", 340), cfg)
    final = grafo.invoke(Command(resume={"aprovado": False}), cfg)
    assert final["escreveu"] is False
    assert catalogo.escritas == 0
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_graph.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.graph'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/graph.py
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from venditus.adapters.base import CatalogAdapter
from venditus.nodes import (
    criar_executor,
    criar_guarda,
    criar_ingest,
    criar_investigador,
    criar_verificador,
    quarentena,
)
from venditus.state import VenditusState


def aprovacao(state: VenditusState) -> VenditusState:
    """Ponto de parada para decisão humana.

    Este nó NÃO escreve nada. Retomar de um interrupt() re-executa o nó inteiro
    desde o início, então qualquer escrita colocada aqui aconteceria duas vezes.
    A escrita mora no nó `executor`, depois deste.
    """
    diagnostico = state.get("diagnostico")
    decisao = state.get("decisao_guarda")
    resposta = interrupt(
        {
            "termo": state["termo"],
            "perda_estimada": state["perda_estimada"],
            "diagnostico": diagnostico.model_dump() if diagnostico else None,
            "decisao_guarda": decisao.model_dump() if decisao else None,
        }
    )
    aprovado = bool(resposta.get("aprovado")) if isinstance(resposta, dict) else bool(resposta)
    return {**state, "status": "aprovado" if aprovado else "rejeitado"}


def rotear_apos_guarda(state: VenditusState) -> str:
    decisao = state.get("decisao_guarda")
    return "aprovacao" if decisao is not None and decisao.permitir else "quarentena"


def rotear_apos_aprovacao(state: VenditusState) -> str:
    return "executor" if state.get("status") == "aprovado" else "fim"


def construir_grafo(
    catalogo: CatalogAdapter,
    llm_investigador,
    llm_guarda,
    checkpointer,
):
    g = StateGraph(VenditusState)

    g.add_node("ingest", criar_ingest(catalogo))
    g.add_node("investigador", criar_investigador(llm_investigador, catalogo))
    g.add_node("guarda", criar_guarda(llm_guarda))
    g.add_node("quarentena", quarentena)
    g.add_node("aprovacao", aprovacao)
    g.add_node("executor", criar_executor(catalogo))
    g.add_node("verificador", criar_verificador(catalogo))

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "investigador")
    g.add_edge("investigador", "guarda")

    # A ARESTA QUE DEFINE O PRODUTO: contradição no pós-venda desvia para
    # quarentena, e o caminho até a escrita deixa de existir.
    g.add_conditional_edges(
        "guarda", rotear_apos_guarda, {"aprovacao": "aprovacao", "quarentena": "quarentena"}
    )
    g.add_edge("quarentena", END)

    g.add_conditional_edges(
        "aprovacao", rotear_apos_aprovacao, {"executor": "executor", "fim": END}
    )
    g.add_edge("executor", "verificador")
    g.add_edge("verificador", END)

    return g.compile(checkpointer=checkpointer)
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_graph.py -v`
Expected: PASS — 4 passed

Se `test_caminho_feliz_pausa_no_interrupt` falhar com o grafo já concluído, a versão instalada do LangGraph usa outra semântica de `interrupt`. Confira o resultado da Task 0 e ajuste: alternativa é `g.compile(checkpointer=..., interrupt_before=["executor"])`, retomando com `grafo.invoke(None, cfg)`.

- [ ] **Step 5: Rodar a suíte inteira**

Run: `.venv\Scripts\pytest -v`
Expected: PASS — todos os testes

- [ ] **Step 6: Commit**

```bash
git add src/venditus/graph.py tests/test_graph.py
git commit -m "feat: grafo com aresta de guarda e aprovacao humana antes da escrita"
```

---

## Task 11: Diagrama da arquitetura

Entregável comprometido para o vídeo. Não depende de servidor, chave ou internet.

**Files:**
- Create: `scripts/gerar_diagrama.py`

- [ ] **Step 1: Escrever o script**

```python
# scripts/gerar_diagrama.py
"""Gera o diagrama do grafo para o pitch. Sem servidor, sem chave, sem internet."""
from pathlib import Path

from langgraph.checkpoint.memory import MemorySaver

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.seed import CATALOGO


class _Stub:
    def with_structured_output(self, _schema):
        return self

    def invoke(self, _prompt):
        raise NotImplementedError("stub apenas para desenhar o grafo")


def main() -> None:
    grafo = construir_grafo(
        catalogo=FakeCatalogAdapter(CATALOGO),
        llm_investigador=_Stub(),
        llm_guarda=_Stub(),
        checkpointer=MemorySaver(),
    )
    saida = Path("docs/arquitetura")
    saida.mkdir(parents=True, exist_ok=True)

    (saida / "grafo.mmd").write_text(grafo.get_graph().draw_mermaid(), encoding="utf-8")
    print("mermaid:", saida / "grafo.mmd")

    try:
        (saida / "grafo.png").write_bytes(grafo.get_graph().draw_mermaid_png())
        print("png:", saida / "grafo.png")
    except Exception as exc:  # renderização de PNG exige rede
        print(f"PNG não gerado ({exc}). O .mmd serve — cole em mermaid.live")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Rodar**

Run: `.venv\Scripts\python scripts\gerar_diagrama.py`
Expected: imprime o caminho do `.mmd`. O `.png` pode falhar sem rede — o `.mmd` é suficiente.

- [ ] **Step 3: Conferir o diagrama**

Abrir `docs/arquitetura/grafo.mmd` e confirmar que existem **duas** arestas saindo de `guarda` (uma para `aprovacao`, uma para `quarentena`). Essa bifurcação é o que você aponta no vídeo.

- [ ] **Step 4: Commit**

```bash
git add scripts/gerar_diagrama.py docs/arquitetura
git commit -m "feat: geracao do diagrama de arquitetura"
```

---

## Task 12: Adapter Shopify

Só agora, porque tudo acima já funciona sem a Shopify.

**Files:**
- Create: `src/venditus/adapters/shopify.py`
- Create: `scripts/testar_shopify.py`

- [ ] **Step 1: Implementar o adapter**

```python
# src/venditus/adapters/shopify.py
import os

import httpx

from venditus.models import Produto

QUERY_PRODUTOS = """
query listarProdutos($n: Int!) {
  products(first: $n) {
    nodes {
      id
      title
      description
      totalInventory
      variants(first: 1) { nodes { sku } }
      metafields(first: 20, namespace: "venditus") {
        nodes { key value }
      }
    }
  }
}
"""

MUTATION_METAFIELD = """
mutation gravar($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { key value }
    userErrors { field message }
  }
}
"""


class ShopifyCatalogAdapter:
    """Catálogo real via Shopify Admin GraphQL.

    Implementa o mesmo protocolo do FakeCatalogAdapter — nenhum nó muda.
    A busca é feita em memória sobre o catálogo carregado, com as mesmas regras
    do fake, para que o comportamento demonstrado seja o mesmo.
    """

    def __init__(self, dominio: str | None = None, token: str | None = None,
                 versao: str | None = None, limite: int = 100) -> None:
        self.dominio = dominio or os.environ["SHOPIFY_STORE_DOMAIN"]
        self.token = token or os.environ["SHOPIFY_ADMIN_TOKEN"]
        self.versao = versao or os.environ.get("SHOPIFY_API_VERSION", "2026-07")
        self.limite = limite
        self._aplicadas: set[str] = set()
        self._id_por_sku: dict[str, str] = {}
        self.escritas = 0

    @property
    def _url(self) -> str:
        return f"https://{self.dominio}/admin/api/{self.versao}/graphql.json"

    def _post(self, query: str, variables: dict) -> dict:
        r = httpx.post(
            self._url,
            json={"query": query, "variables": variables},
            headers={"X-Shopify-Access-Token": self.token,
                     "Content-Type": "application/json"},
            timeout=30.0,
        )
        r.raise_for_status()
        corpo = r.json()
        if "errors" in corpo:
            raise RuntimeError(f"Shopify GraphQL: {corpo['errors']}")
        return corpo["data"]

    def listar_produtos(self) -> list[Produto]:
        dados = self._post(QUERY_PRODUTOS, {"n": self.limite})
        produtos: list[Produto] = []
        for no in dados["products"]["nodes"]:
            variantes = no["variants"]["nodes"]
            sku = variantes[0]["sku"] if variantes and variantes[0]["sku"] else no["id"]
            self._id_por_sku[sku] = no["id"]
            produtos.append(
                Produto(
                    sku=sku,
                    titulo=no["title"],
                    descricao=no.get("description") or "",
                    atributos={m["key"]: m["value"] for m in no["metafields"]["nodes"]},
                    estoque=no.get("totalInventory") or 0,
                )
            )
        return produtos

    def obter_produto(self, sku: str) -> Produto | None:
        return next((p for p in self.listar_produtos() if p.sku == sku), None)

    def buscar(self, termo: str) -> list[Produto]:
        from venditus.adapters.fake import FakeCatalogAdapter

        return FakeCatalogAdapter(self.listar_produtos()).buscar(termo)

    def aplicar_correcao(self, sku: str, campo: str, valor: str, fix_id: str) -> bool:
        if fix_id in self._aplicadas:
            return False
        if sku not in self._id_por_sku:
            self.listar_produtos()
        gid = self._id_por_sku.get(sku)
        if gid is None:
            raise KeyError(f"SKU não encontrado na Shopify: {sku}")

        dados = self._post(MUTATION_METAFIELD, {
            "metafields": [{
                "ownerId": gid, "namespace": "venditus",
                "key": campo, "value": valor, "type": "single_line_text_field",
            }]
        })
        erros = dados["metafieldsSet"]["userErrors"]
        if erros:
            raise RuntimeError(f"metafieldsSet: {erros}")

        self._aplicadas.add(fix_id)
        self.escritas += 1
        return True

    def correcao_ja_aplicada(self, fix_id: str) -> bool:
        return fix_id in self._aplicadas
```

- [ ] **Step 2: Criar o script de verificação manual**

```python
# scripts/testar_shopify.py
"""Confere conectividade e escrita reais. Rode uma vez após criar a dev store."""
from dotenv import load_dotenv

from venditus.adapters.shopify import ShopifyCatalogAdapter
from venditus.fixid import fix_id

load_dotenv()

a = ShopifyCatalogAdapter()
produtos = a.listar_produtos()
print(f"{len(produtos)} produtos carregados")
for p in produtos[:5]:
    print(f"  {p.sku} | {p.titulo} | estoque={p.estoque} | atributos={p.atributos}")

alvo = produtos[0]
fid = fix_id(alvo.sku, "teste_venditus", "ok")
print("escrita:", a.aplicar_correcao(alvo.sku, "teste_venditus", "ok", fid))
print("idempotente (deve ser False):", a.aplicar_correcao(alvo.sku, "teste_venditus", "ok", fid))
```

- [ ] **Step 3: Rodar contra a loja real**

Run: `.venv\Scripts\python scripts\testar_shopify.py`
Expected: lista os produtos, primeira escrita `True`, segunda `False`.

Se falhar com 401, o token não tem escopo. A Admin API precisa de `read_products` e `write_products`.

- [ ] **Step 4: Commit**

```bash
git add src/venditus/adapters/shopify.py scripts/testar_shopify.py
git commit -m "feat: adapter Shopify Admin GraphQL"
```

---

## Task 13: Ponto de entrada e manifesto do LangGraph

**Files:**
- Create: `src/venditus/app.py`
- Create: `langgraph.json`

- [ ] **Step 1: Criar o ponto de entrada**

```python
# src/venditus/app.py
"""Monta o grafo com as dependências reais.

REGRA: nunca passar temperature ou top_p. Em modelos GPT-5.x de raciocínio,
esses parâmetros são aceitos apenas com reasoning_effort='none'. O controle
correto é reasoning_effort.
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.graph import construir_grafo
from venditus.seed import CATALOGO

load_dotenv()

MODELO = "gpt-5.6-terra"


def montar(usar_shopify: bool | None = None):
    if usar_shopify is None:
        usar_shopify = bool(os.environ.get("SHOPIFY_ADMIN_TOKEN"))

    if usar_shopify:
        from venditus.adapters.shopify import ShopifyCatalogAdapter

        catalogo = ShopifyCatalogAdapter()
    else:
        catalogo = FakeCatalogAdapter(CATALOGO)

    return construir_grafo(
        catalogo=catalogo,
        llm_investigador=ChatOpenAI(model=MODELO, reasoning_effort="medium"),
        llm_guarda=ChatOpenAI(model=MODELO, reasoning_effort="high"),
        checkpointer=SqliteSaver.from_conn_string("checkpoints.db"),
    )


grafo = montar()
```

- [ ] **Step 2: Criar o manifesto**

```json
{
  "dependencies": ["."],
  "graphs": {
    "venditus": "./src/venditus/app.py:grafo"
  },
  "env": ".env"
}
```

- [ ] **Step 3: Verificar que monta**

Run: `.venv\Scripts\python -c "from venditus.app import grafo; print(grafo)"`
Expected: imprime o objeto do grafo compilado, sem exceção.

Se `SqliteSaver.from_conn_string` exigir uso como context manager na versão instalada, troque por:

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
```

- [ ] **Step 4: Commit**

```bash
git add src/venditus/app.py langgraph.json
git commit -m "feat: ponto de entrada e manifesto do langgraph"
```

---

## Task 14: KPIs agregados

O spec define cinco KPIs. Três saem do estado de uma execução (`resultados_antes`,
`resultados_depois`, `perda_estimada`). Os outros dois — **cobertura de atributo**
e **taxa de bloqueio do guarda** — são agregados e precisam de código próprio.
A taxa de bloqueio é a métrica do diferencial: nenhum concorrente consegue calculá-la.

**Files:**
- Create: `src/venditus/metrics.py`
- Test: `tests/test_metrics.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
# tests/test_metrics.py
from venditus.metrics import cobertura_de_atributo, receita_recuperada, resumo_kpis, taxa_de_bloqueio
from venditus.models import Produto
from venditus.state import estado_inicial


def _produtos():
    return [
        Produto(sku="A", titulo="A", atributos={"impermeavel": "true"}, estoque=1),
        Produto(sku="B", titulo="B", atributos={"impermeavel": ""}, estoque=1),
        Produto(sku="C", titulo="C", atributos={}, estoque=1),
        Produto(sku="D", titulo="D", atributos={"impermeavel": "true"}, estoque=1),
    ]


def _estados():
    aplicado = estado_inicial("tênis impermeável", 340)
    aplicado["status"] = "aplicado"
    aplicado["escreveu"] = True
    bloqueado = estado_inicial("capa de chuva impermeável", 128)
    bloqueado["status"] = "quarentena"
    rejeitado = estado_inicial("mochila cargueira 80 litros", 64)
    rejeitado["status"] = "rejeitado"
    return [aplicado, bloqueado, rejeitado]


def test_cobertura_de_atributo():
    # 2 de 4 produtos com o atributo preenchido
    assert cobertura_de_atributo(_produtos(), "impermeavel") == 0.5


def test_cobertura_com_catalogo_vazio():
    assert cobertura_de_atributo([], "impermeavel") == 0.0


def test_taxa_de_bloqueio():
    # 1 quarentena em 3 execuções
    assert round(taxa_de_bloqueio(_estados()), 4) == 0.3333


def test_taxa_de_bloqueio_sem_execucoes():
    assert taxa_de_bloqueio([]) == 0.0


def test_receita_recuperada_soma_so_o_que_foi_escrito():
    assert receita_recuperada(_estados()) == 3841.73


def test_resumo_reune_os_quatro_kpis():
    r = resumo_kpis(_produtos(), _estados(), "impermeavel")
    assert r["cobertura_de_atributo"] == 0.5
    assert r["receita_recuperada"] == 3841.73
    assert r["bloqueados"] == 1
    assert r["execucoes"] == 3
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `.venv\Scripts\pytest tests/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'venditus.metrics'`

- [ ] **Step 3: Implementar**

```python
# src/venditus/metrics.py
"""KPIs agregados do dashboard.

Operam sobre uma lista de estados finais de execução, mantida pela camada que
roda o grafo. Nenhum acoplamento com o checkpointer.
"""

from venditus.adapters.fake import VALORES_VERDADEIROS
from venditus.models import Produto
from venditus.state import VenditusState

STATUS_BLOQUEADO = "quarentena"


def cobertura_de_atributo(produtos: list[Produto], campo: str) -> float:
    """Fração de produtos com o atributo estruturado preenchido."""
    if not produtos:
        return 0.0
    preenchidos = sum(
        1 for p in produtos
        if str(p.atributos.get(campo, "")).lower() in VALORES_VERDADEIROS
    )
    return preenchidos / len(produtos)


def taxa_de_bloqueio(estados: list[VenditusState]) -> float:
    """Fração de execuções que o guarda recusou.

    É a métrica do diferencial: só existe porque o motor lê pré e pós-venda.
    """
    if not estados:
        return 0.0
    bloqueados = sum(1 for e in estados if e.get("status") == STATUS_BLOQUEADO)
    return bloqueados / len(estados)


def receita_recuperada(estados: list[VenditusState]) -> float:
    """Soma da perda estimada apenas das execuções que resultaram em escrita."""
    return round(sum(e.get("perda_estimada", 0.0) for e in estados if e.get("escreveu")), 2)


def resumo_kpis(produtos: list[Produto], estados: list[VenditusState], campo: str) -> dict:
    return {
        "cobertura_de_atributo": cobertura_de_atributo(produtos, campo),
        "receita_recuperada": receita_recuperada(estados),
        "bloqueados": sum(1 for e in estados if e.get("status") == STATUS_BLOQUEADO),
        "execucoes": len(estados),
        "taxa_de_bloqueio": taxa_de_bloqueio(estados),
    }
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `.venv\Scripts\pytest tests/test_metrics.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: Commit**

```bash
git add src/venditus/metrics.py tests/test_metrics.py
git commit -m "feat: KPIs agregados incluindo taxa de bloqueio do guarda"
```

---

## Task 15: Avaliação de acurácia do classificador

Produz o número citável no pitch: *"o classificador acerta a causa em N% de um
conjunto rotulado à mão."*

**Esta é a tarefa a cortar se o tempo apertar.** Ela exige chave da OpenAI e
chamadas reais, e nada mais depende dela.

**Files:**
- Create: `tests/dados_rotulados.py`
- Create: `scripts/avaliar_classificador.py`

- [ ] **Step 1: Criar o conjunto rotulado**

```python
# tests/dados_rotulados.py
"""Queries com causa esperada, rotuladas à mão contra o catálogo de seed."""
from venditus.models import Causa

ROTULADOS: list[tuple[str, Causa]] = [
    ("tênis impermeável", Causa.ATRIBUTO_AUSENTE),
    ("capa de chuva impermeável", Causa.ATRIBUTO_AUSENTE),
    ("tenis impermeavel", Causa.ATRIBUTO_AUSENTE),
    ("tênis impermiavel", Causa.TYPO),
    ("tenis a prova d'agua", Causa.SINONIMO),
    ("calçado impermeável", Causa.SINONIMO),
    ("bota de trilha impermeável", Causa.SEM_SORTIMENTO),
    ("mochila cargueira 80 litros", Causa.SEM_SORTIMENTO),
    ("lanterna de cabeça", Causa.SEM_ESTOQUE),
    ("lanterna cabeca lumen", Causa.SEM_ESTOQUE),
    ("meia de lã merino", Causa.SINONIMO),
    ("meia termica merino", Causa.SINONIMO),
    ("mochila 60 litros", Causa.SINONIMO),
    ("mochila cargeira", Causa.TYPO),
    ("capa de chuva dobrável", Causa.ATRIBUTO_AUSENTE),
    ("jaqueta corta vento", Causa.SEM_SORTIMENTO),
    ("barraca 2 pessoas", Causa.SEM_SORTIMENTO),
    ("tenis trilha alfa", Causa.TYPO),
    ("calça impermeável", Causa.SEM_SORTIMENTO),
    ("meia merino tamanho 42", Causa.ATRIBUTO_AUSENTE),
]
```

- [ ] **Step 2: Criar o script de avaliação**

```python
# scripts/avaliar_classificador.py
"""Mede a acurácia do investigador contra o conjunto rotulado.

Faz chamadas reais ao modelo. Exige OPENAI_API_KEY.
"""
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from venditus.adapters.fake import FakeCatalogAdapter
from venditus.app import MODELO
from venditus.nodes import criar_investigador
from venditus.seed import CATALOGO
from venditus.state import estado_inicial
from tests.dados_rotulados import ROTULADOS

load_dotenv()


def main() -> None:
    catalogo = FakeCatalogAdapter(CATALOGO)
    investigador = criar_investigador(
        ChatOpenAI(model=MODELO, reasoning_effort="medium"), catalogo
    )

    acertos = 0
    for termo, esperado in ROTULADOS:
        estado = estado_inicial(termo, 100)
        estado["resultados_antes"] = len(catalogo.buscar(termo))
        obtido = investigador(estado)["diagnostico"].causa
        ok = obtido == esperado
        acertos += ok
        marca = "OK  " if ok else "ERRO"
        print(f"{marca} {termo!r}: esperado={esperado.value} obtido={obtido.value}")

    total = len(ROTULADOS)
    print(f"\nAcurácia: {acertos}/{total} = {acertos / total:.0%}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Rodar**

Run: `.venv\Scripts\python scripts\avaliar_classificador.py`
Expected: imprime linha por query e a acurácia final.

Se a acurácia ficar abaixo de ~70%, o problema é quase sempre o prompt, não o
modelo: ajuste as descrições das seis causas em `PROMPT_INVESTIGADOR` antes de
subir para `gpt-5.6-sol`.

- [ ] **Step 4: Commit**

```bash
git add tests/dados_rotulados.py scripts/avaliar_classificador.py
git commit -m "feat: avaliacao de acuracia do classificador"
```

---

## Verificação final do backend

- [ ] Suíte inteira verde: `.venv\Scripts\pytest -v`
- [ ] `test_caminho_bloqueado_nao_escreve` passa — **é a prova da tese**
- [ ] `test_executor_e_idempotente` passa — **é a prova de que a retomada do interrupt não duplica escrita**
- [ ] `docs/arquitetura/grafo.mmd` mostra duas arestas saindo de `guarda`
- [ ] `python -c "from venditus.app import grafo"` monta sem erro
- [ ] Nenhuma ocorrência de `temperature` no código: `git grep -n temperature -- src/` retorna vazio
- [ ] `resumo_kpis` devolve os quatro números do dashboard do spec
- [ ] Acurácia do classificador registrada (Task 15) — ou explicitamente cortada por tempo

### Cobertura do spec

| Requisito do spec | Onde |
|---|---|
| Seis causas | Task 1 |
| Estimativa de R$ com premissas declaradas | Task 2 |
| Idempotência da escrita | Tasks 3 e 7 |
| Catálogo atrás de adapter (VTEX plugável) | Tasks 4 e 12 |
| Dois SKUs com diagnóstico idêntico e decisões opostas | Tasks 5, 9 e 10 |
| Seis nós, aresta condicional do guarda | Task 10 |
| Aprovação humana antes de qualquer escrita | Task 10 |
| Diagrama de arquitetura | Task 11 |
| KPIs do dashboard | Task 14 |
| Acurácia do classificador | Task 15 |

---

## Fora de escopo nesta rodada

Não implementar, mesmo que pareça natural:

- Caminho de escrita pós-venda → PDP (o corpus de devolução alimenta **apenas** o guarda)
- Camada de lote / anomalia temporal e regional
- Adapter VTEX
- Cron/agendamento
- Front-end (React + `useStream` + shadcn/ui) — rodada seguinte
