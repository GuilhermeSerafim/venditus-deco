import type { Status } from "../dados/contrato";

export type EstadoPasso =
  | "pendente"
  | "ativo"
  | "concluido"
  | "bloqueado"
  | "inalcancavel";

export interface Passo {
  /** Nome do no no grafo — exibido em mono, pequeno. */
  no: string;
  /** O que o no faz, em portugues — exibido grande. */
  rotulo: string;
  estado: EstadoPasso;
}

/** Seis passos, nao sete.
 *
 * `quarentena` nao e etapa do caminho, e o fim dele: aparece como rotulo de
 * status no rodape do bloco de recusa. Como setimo passo, sugeriria um
 * caminho que passa por ela e continua.
 */
const CAMINHO = [
  { no: "ingest", rotulo: "Mede a busca" },
  { no: "investigador", rotulo: "Investiga a causa" },
  { no: "guarda", rotulo: "Audita as devoluções" },
  { no: "aprovacao", rotulo: "Sua aprovação" },
  { no: "executor", rotulo: "Grava no catálogo" },
  { no: "verificador", rotulo: "Refaz a busca" },
] as const;

/** Quantos passos ja concluiram, e qual e o corrente, para cada status. */
const MAPA: Record<Status, { concluidos: number; corrente: EstadoPasso | null }> = {
  novo: { concluidos: 0, corrente: "ativo" },
  diagnosticando: { concluidos: 1, corrente: "ativo" },
  diagnosticado: { concluidos: 2, corrente: "ativo" },
  bloqueado_pelo_guarda: { concluidos: 2, corrente: "bloqueado" },
  quarentena: { concluidos: 2, corrente: "bloqueado" },
  aprovado_pelo_guarda: { concluidos: 3, corrente: "ativo" },
  aprovado: { concluidos: 4, corrente: "ativo" },
  rejeitado: { concluidos: 4, corrente: null },
  sem_correcao: { concluidos: 5, corrente: "ativo" },
  aplicado: { concluidos: 6, corrente: null },
};

/** O status do estado vira o desenho da linha do tempo.
 *
 * Quando o guarda bloqueia, os passos seguintes viram `inalcancavel` — nao
 * `pendente`. E a tese do produto virando pixel: o caminho ate a escrita
 * deixa de existir.
 */
export function derivarPassos(status: Status | undefined): Passo[] {
  const { concluidos, corrente } = MAPA[status ?? "novo"];
  const interrompido = corrente === "bloqueado" || status === "rejeitado";

  return CAMINHO.map((passo, indice) => {
    let estado: EstadoPasso;
    if (indice < concluidos) {
      estado = "concluido";
    } else if (indice === concluidos && corrente !== null) {
      estado = corrente;
    } else {
      estado = interrompido ? "inalcancavel" : "pendente";
    }
    return { ...passo, estado };
  });
}
