from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


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

    @model_validator(mode="after")
    def _causas_sem_escrita_nao_propoem_correcao(self) -> "Diagnostico":
        """Impede, por schema, que SEM_ESTOQUE ou SEM_SORTIMENTO tragam correção.

        Sem isto, a regra vive só no texto do prompt: um LLM que alucinasse essa
        combinação passaria pelo guarda e chegaria ao executor, que escreveria.
        """
        if self.causa in CAUSAS_SEM_ESCRITA and self.correcao is not None:
            raise ValueError(
                f"causa {self.causa.value} nunca gera correção — o problema não "
                "é o catálogo, é estoque ou sortimento"
            )
        return self


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
