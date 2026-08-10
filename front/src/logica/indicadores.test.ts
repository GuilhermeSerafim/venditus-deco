import { describe, expect, it } from "vitest";
import type { EstadoVenditus } from "../dados/contrato";
import { indicadores } from "./indicadores";

function estado(parcial: Partial<EstadoVenditus>): EstadoVenditus {
  return {
    termo: "termo",
    volume: 100,
    perda_estimada: 1129.92,
    diagnostico: null,
    decisao_guarda: null,
    devolucoes_consultadas: [],
    fix_id: null,
    resultados_antes: 0,
    resultados_depois: 0,
    status: "aplicado",
    escreveu: false,
    ...parcial,
  };
}

describe("indicadores", () => {
  it("sem execucoes, zera tudo e nao divide por zero", () => {
    const r = indicadores([]);
    expect(r.execucoes).toBe(0);
    expect(r.taxaDeBloqueio).toBe(0);
    expect(r.receitaRecuperada).toBe(0);
    expect(r.resultadosAntes).toBeNull();
  });

  it("soma a perda estimada apenas das execucoes que melhoraram a busca", () => {
    const r = indicadores([
      estado({
        perda_estimada: 3841.73,
        escreveu: true,
        resultados_antes: 0,
        resultados_depois: 1,
      }),
      estado({ perda_estimada: 1446.3, escreveu: false, status: "quarentena" }),
    ]);
    expect(r.receitaRecuperada).toBe(3841.73);
  });

  it("escrita que nao melhorou a busca NAO conta como receita", () => {
    // Caso real: o investigador propos marcar uma mochila de 60L como
    // "80 litros"; o guarda nao tinha devolucao daquele SKU para contradizer;
    // a escrita foi aplicada e a busca continuou em zero. Contar isso como
    // receita seria afirmar o contrario do que a propria execucao mediu.
    const r = indicadores([
      estado({
        perda_estimada: 723.15,
        escreveu: true,
        resultados_antes: 0,
        resultados_depois: 0,
      }),
    ]);
    expect(r.receitaRecuperada).toBe(0);
    expect(r.execucoes).toBe(1);
  });

  it("ARMADILHA: status 'aplicado' com escreveu=false NAO conta receita", () => {
    // E o caminho sem_correcao: o executor devolve status="sem_correcao" e
    // escreveu=false (nodes.py:46), mas o verificador roda em seguida e
    // sobrescreve o status com "aplicado" (nodes.py:67). Quem decide e
    // escreveu, como metrics.py:38 ja faz.
    const r = indicadores([
      estado({ perda_estimada: 723.15, status: "aplicado", escreveu: false }),
    ]);
    expect(r.receitaRecuperada).toBe(0);
    expect(r.execucoes).toBe(1);
  });

  it("conta bloqueados pelo status quarentena", () => {
    const r = indicadores([
      estado({ status: "quarentena" }),
      estado({ status: "aplicado", escreveu: true }),
    ]);
    expect(r.bloqueados).toBe(1);
    expect(r.taxaDeBloqueio).toBe(0.5);
  });

  it("bloqueado_pelo_guarda NAO conta — o terminal e quarentena", () => {
    // metrics.py:11 fixa STATUS_BLOQUEADO = "quarentena".
    const r = indicadores([estado({ status: "bloqueado_pelo_guarda" })]);
    expect(r.bloqueados).toBe(0);
  });

  it("o antes/depois ignora execucoes que nao melhoraram a busca", () => {
    const r = indicadores([
      estado({ escreveu: true, resultados_antes: 0, resultados_depois: 1 }),
      estado({ status: "quarentena", resultados_antes: 0, resultados_depois: 0 }),
    ]);
    expect(r.resultadosAntes).toBe(0);
    expect(r.resultadosDepois).toBe(1);
  });

  it("uma execucao sem ganho nao apaga da tela o ganho de outra", () => {
    // Com "a ultima que escreveu", rodar a mochila depois do tenis trocava o
    // 0 -> 1 da tela por 0 -> 0, e o resultado bom sumia.
    const r = indicadores([
      estado({ escreveu: true, resultados_antes: 0, resultados_depois: 1 }),
      estado({ escreveu: true, resultados_antes: 0, resultados_depois: 0 }),
    ]);
    expect(r.resultadosAntes).toBe(0);
    expect(r.resultadosDepois).toBe(1);
  });

  it("arredonda a receita em duas casas", () => {
    const r = indicadores([
      estado({
        perda_estimada: 3841.73,
        escreveu: true,
        resultados_antes: 0,
        resultados_depois: 1,
      }),
      estado({
        perda_estimada: 723.15,
        escreveu: true,
        resultados_antes: 1,
        resultados_depois: 2,
      }),
    ]);
    expect(r.receitaRecuperada).toBe(4564.88);
  });
});
