import { describe, expect, it } from "vitest";
import { campoAcentuado, dias, fraseDaCorrecao, moeda } from "./formato";

/** pt-BR usa espaco NAO-QUEBRAVEL (U+00A0) depois do "R$". Comparar com espaco
 *  comum falha de um jeito que consome vinte minutos para achar. */
const semNbsp = (t: string) => t.replace(/\u00a0/g, " ");

describe("moeda", () => {
  it("formata em real brasileiro", () => {
    expect(semNbsp(moeda(3841.73))).toBe("R$ 3.841,73");
  });

  it("mantem duas casas em valor redondo", () => {
    expect(semNbsp(moeda(723.1))).toBe("R$ 723,10");
  });
});

describe("dias", () => {
  it("usa singular em 1", () => {
    expect(dias(1)).toBe("1 dia");
  });

  it("usa plural nos demais", () => {
    expect(dias(14)).toBe("14 dias");
  });
});

describe("campoAcentuado", () => {
  it("devolve a palavra acentuada que o cliente buscou", () => {
    expect(campoAcentuado("impermeavel", "tênis impermeável")).toBe("impermeável");
  });

  it("devolve o campo cru quando nenhum token casa", () => {
    expect(campoAcentuado("voltagem", "air fryer 220v")).toBe("voltagem");
  });
});

describe("fraseDaCorrecao", () => {
  it("vira 'Marcar X como Y' quando o valor e verdadeiro", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-4471", campo: "impermeavel", valor: "true" },
      "tênis impermeável"
    );
    expect(frase).toBe("Marcar “Tênis Trilha Alpha” como impermeável no catálogo");
  });

  it("vira 'Definir campo como valor' nos demais valores", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-1201", campo: "litragem", valor: "80" },
      "mochila cargueira 80 litros"
    );
    expect(frase).toBe("Definir litragem de “Mochila Cargueira 60L” como 80");
  });

  it("cai no SKU quando o titulo nao esta no espelho", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-9999", campo: "impermeavel", valor: "true" },
      "tênis impermeável"
    );
    expect(frase).toBe("Marcar “SKU-9999” como impermeável no catálogo");
  });
});
