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

/** Espelho de metrics.py :: resumo_kpis, com a mesma assinatura.
 *
 * `cobertura_de_atributo` fica de fora: exige catalogo.listar_produtos(), que
 * o backend nao serve por HTTP. No lugar dela vai o antes/depois da busca,
 * que ja vem no estado.
 *
 * REGRA: quem decide se houve escrita e `escreveu`, nunca `status`.
 */
export function indicadores(estados: EstadoVenditus[]): Indicadores {
  const escritos = estados.filter((e) => e.escreveu);
  const bloqueados = estados.filter((e) => e.status === STATUS_BLOQUEADO).length;
  const ultimoEscrito = escritos.at(-1) ?? null;

  const soma = escritos.reduce((total, e) => total + (e.perda_estimada ?? 0), 0);

  return {
    receitaRecuperada: Math.round(soma * 100) / 100,
    bloqueados,
    execucoes: estados.length,
    taxaDeBloqueio: estados.length === 0 ? 0 : bloqueados / estados.length,
    resultadosAntes: ultimoEscrito?.resultados_antes ?? null,
    resultadosDepois: ultimoEscrito?.resultados_depois ?? null,
  };
}
