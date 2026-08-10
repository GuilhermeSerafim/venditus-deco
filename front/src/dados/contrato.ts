/** Tipos espelhando back/src/venditus/state.py e models.py.
 *
 * E exatamente o que chega no useStream. Se o backend mudar, este arquivo
 * muda junto.
 */

export type Causa =
  | "typo"
  | "sinonimo"
  | "atributo_ausente"
  | "categorizacao_errada"
  | "sem_estoque"
  | "sem_sortimento";

export type Confianca = "alta" | "media" | "baixa";

export interface CorrecaoProposta {
  sku: string;
  campo: string;
  valor: string;
}

export interface Diagnostico {
  causa: Causa;
  confianca: Confianca;
  /** Trecho literal do catalogo que sustenta o diagnostico. */
  evidencia: string;
  /** Nula quando a causa nao gera escrita (sem_estoque, sem_sortimento). */
  correcao: CorrecaoProposta | null;
}

export interface DecisaoGuarda {
  permitir: boolean;
  justificativa: string;
  devolucoes_contraditorias: number;
}

export interface Devolucao {
  sku: string;
  motivo: string;
  dias_atras: number;
}

export type Status =
  | "novo"
  | "diagnosticando"
  | "diagnosticado"
  | "aprovado_pelo_guarda"
  | "bloqueado_pelo_guarda"
  | "quarentena"
  | "aprovado"
  | "rejeitado"
  | "aplicado"
  | "sem_correcao";

/** Os status em que o grafo parou de vez.
 *
 * `sem_correcao` NAO esta aqui de proposito: o executor o define (nodes.py:46),
 * mas a aresta executor -> verificador roda em seguida e o verificador o
 * sobrescreve com "aplicado" (nodes.py:67). Ele so e observavel no meio do
 * stream, nunca no estado final.
 */
export const STATUS_TERMINAIS: Status[] = ["quarentena", "rejeitado", "aplicado"];

export interface EstadoVenditus {
  termo: string;
  volume: number;
  perda_estimada: number;
  diagnostico: Diagnostico | null;
  decisao_guarda: DecisaoGuarda | null;
  /** As devolucoes que o guarda leu para decidir. Sao a tela de recusa. */
  devolucoes_consultadas: Devolucao[];
  fix_id: string | null;
  resultados_antes: number;
  resultados_depois: number;
  status: Status;
  /** QUEM DECIDE SE HOUVE ESCRITA. Nunca use `status` para isso. */
  escreveu: boolean;
}
