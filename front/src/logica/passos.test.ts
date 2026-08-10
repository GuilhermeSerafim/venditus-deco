import { describe, expect, it } from "vitest";
import { derivarPassos } from "./passos";

const estados = (status: Parameters<typeof derivarPassos>[0]) =>
  derivarPassos(status).map((p) => p.estado);

describe("derivarPassos", () => {
  it("devolve sempre os seis passos, na ordem do grafo", () => {
    const nos = derivarPassos("novo").map((p) => p.no);
    expect(nos).toEqual([
      "ingest", "investigador", "guarda", "aprovacao", "executor", "verificador",
    ]);
  });

  it("traduz cada no para um rotulo em portugues", () => {
    const rotulos = derivarPassos("novo").map((p) => p.rotulo);
    expect(rotulos).toEqual([
      "Mede a busca",
      "Investiga a causa",
      "Audita as devoluções",
      "Sua aprovação",
      "Grava no catálogo",
      "Refaz a busca",
    ]);
  });

  it("sem estado ainda, deixa o primeiro passo ativo", () => {
    expect(estados(undefined)).toEqual([
      "ativo", "pendente", "pendente", "pendente", "pendente", "pendente",
    ]);
  });

  it("em diagnosticando, o ingest concluiu e o investigador roda", () => {
    expect(estados("diagnosticando")).toEqual([
      "concluido", "ativo", "pendente", "pendente", "pendente", "pendente",
    ]);
  });

  it("em diagnosticado, o guarda roda", () => {
    expect(estados("diagnosticado")).toEqual([
      "concluido", "concluido", "ativo", "pendente", "pendente", "pendente",
    ]);
  });

  it("bloqueado: o guarda fica em bloqueado e o resto vira inalcancavel", () => {
    expect(estados("bloqueado_pelo_guarda")).toEqual([
      "concluido", "concluido", "bloqueado",
      "inalcancavel", "inalcancavel", "inalcancavel",
    ]);
  });

  it("quarentena tem a mesma forma do bloqueio — e o fim dele", () => {
    expect(estados("quarentena")).toEqual(estados("bloqueado_pelo_guarda"));
  });

  it("aprovado_pelo_guarda deixa a aprovacao ativa, esperando o humano", () => {
    expect(estados("aprovado_pelo_guarda")).toEqual([
      "concluido", "concluido", "concluido", "ativo", "pendente", "pendente",
    ]);
  });

  it("aprovado poe o executor para rodar", () => {
    expect(estados("aprovado")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "ativo", "pendente",
    ]);
  });

  it("rejeitado encerra na aprovacao: escrita e verificacao ficam inalcancaveis", () => {
    expect(estados("rejeitado")).toEqual([
      "concluido", "concluido", "concluido", "concluido",
      "inalcancavel", "inalcancavel",
    ]);
  });

  it("sem_correcao e transitorio: o executor passou, o verificador roda", () => {
    expect(estados("sem_correcao")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "concluido", "ativo",
    ]);
  });

  it("aplicado conclui os seis", () => {
    expect(estados("aplicado")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "concluido", "concluido",
    ]);
  });
});
