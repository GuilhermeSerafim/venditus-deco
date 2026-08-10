import type { EstadoVenditus } from "../dados/contrato";

/** Fonte: back/src/venditus/metrics.py:11 */
const STATUS_BLOQUEADO = "quarentena";

export interface Indicadores {
  receitaRecuperada: number;
  bloqueados: number;
  execucoes: number;
  taxaDeBloqueio: number;
  /** Da ultima execucao que escreveu; null enquanto nenhuma escreveu. */
  resultadosAntes: number | null;
  resultadosDepois: number | null;
}

/** Uma execucao so conta como receita se a busca REALMENTE melhorou.
 *
 * Divergencia deliberada de metrics.py:38, que soma toda execucao com
 * `escreveu`. Aquilo mede intencao; o rotulo na tela diz "recuperado", que e
 * efeito. Existe escrita que acontece e nao recupera nada — o caso real: o
 * investigador propos marcar uma mochila de 60L como "80 litros", o guarda
 * nao tinha devolucao daquele SKU para contradizer, a escrita foi aplicada, e
 * a busca continuou em zero. Contar aquilo como R$ 723 recuperados seria a
 * interface afirmando algo que ela mesma acabou de medir como falso.
 */
function recuperou(e: EstadoVenditus): boolean {
  return e.escreveu && e.resultados_depois > e.resultados_antes;
}

/** Espelho de metrics.py :: resumo_kpis, com a mesma assinatura.
 *
 * `cobertura_de_atributo` fica de fora: exige catalogo.listar_produtos(), que
 * o backend nao serve por HTTP. No lugar dela vai o antes/depois da busca,
 * que ja vem no estado.
 *
 * REGRA: quem decide se houve escrita e `escreveu`, nunca `status`.
 */
export function indicadores(estados: EstadoVenditus[]): Indicadores {
  const recuperadas = estados.filter(recuperou);
  const bloqueados = estados.filter((e) => e.status === STATUS_BLOQUEADO).length;

  const soma = recuperadas.reduce((total, e) => total + (e.perda_estimada ?? 0), 0);

  // Agregado, e nao a ultima escrita: com "ultima", rodar um caso que nao
  // melhora a busca apagava da tela o 0 -> 1 de um caso anterior que melhorou.
  const antes = recuperadas.reduce((t, e) => t + e.resultados_antes, 0);
  const depois = recuperadas.reduce((t, e) => t + e.resultados_depois, 0);

  return {
    receitaRecuperada: Math.round(soma * 100) / 100,
    bloqueados,
    execucoes: estados.length,
    taxaDeBloqueio: estados.length === 0 ? 0 : bloqueados / estados.length,
    resultadosAntes: recuperadas.length === 0 ? null : antes,
    resultadosDepois: recuperadas.length === 0 ? null : depois,
  };
}
