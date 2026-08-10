/** ESPELHO DECLARADO DO BACKEND.
 *
 * O `langgraph dev` expoe apenas a API do grafo — nao ha rota que sirva a
 * fila de buscas, o catalogo ou a formula da estimativa. Ver o spec em
 * docs/superpowers/specs/2026-08-09-venditus-front-design.md, secao 1.
 *
 * Cada bloco abaixo aponta para o arquivo-fonte no backend. Se o back mudar,
 * este arquivo muda junto. E o unico lugar do front com dado duplicado.
 */

/** Fonte: back/src/venditus/estimate.py
 *
 * PREMISSAS DECLARADAS, nao medicoes. Precisam aparecer na tela junto do R$
 * sempre que ele for exibido.
 */
export const CONVERSAO_ASSUMIDA = 0.02;
export const TICKET_MEDIO_BRL = 564.96;

/** Fonte: back/src/venditus/estimate.py :: perda_estimada
 *
 * O front PRECISA calcular isto e enviar no input do run. O no `aprovacao` le
 * state["perda_estimada"] direto (graph.py:40), e quem preenche o campo e
 * estado_inicial() (state.py:32), que e funcao Python e nao passa por HTTP.
 * Sem enviar, o run quebra com KeyError no no da pausa — depois de duas
 * chamadas de LLM ja pagas.
 */
export function perdaEstimada(volume: number): number {
  return Math.round(volume * CONVERSAO_ASSUMIDA * TICKET_MEDIO_BRL * 100) / 100;
}

export interface BuscaFalha {
  termo: string;
  volume: number;
}

/** Fonte: back/src/venditus/seed.py :: BUSCAS */
export const BUSCAS: BuscaFalha[] = [
  { termo: "tênis impermeável", volume: 340 },
  { termo: "capa de chuva impermeável", volume: 128 },
  { termo: "mochila cargueira 80 litros", volume: 64 },
];

/** Fonte: back/src/venditus/seed.py :: CATALOGO — apenas os titulos.
 *
 * O estado carrega diagnostico.correcao.sku, nunca o titulo do produto.
 */
export const TITULOS: Record<string, string> = {
  "SKU-4471": "Tênis Trilha Alpha",
  "SKU-8802": "Capa de Chuva Leve Nimbus",
  "SKU-1100": "Meia Térmica Merino",
  "SKU-1201": "Mochila Cargueira 60L",
  "SKU-1305": "Lanterna de Cabeça Lumen",
};

/** Fonte: back/src/venditus/adapters/fake.py :: VALORES_VERDADEIROS */
export const VALORES_VERDADEIROS = new Set(["true", "sim", "1", "verdadeiro"]);
