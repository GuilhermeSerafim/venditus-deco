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
