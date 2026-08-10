import type { CorrecaoProposta } from "../dados/contrato";
import { TITULOS, VALORES_VERDADEIROS } from "../dados/espelho";

export function moeda(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function dias(quantidade: number): string {
  return quantidade === 1 ? "1 dia" : `${quantidade} dias`;
}

/** Espelha adapters/fake.py :: normalizar — minusculas sem acento. */
function normalizar(texto: string): string {
  return texto
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "");
}

/** Devolve a palavra do cliente, COM acento.
 *
 * O prompt do investigador exige que o nome do campo seja "a propria palavra
 * que o cliente buscou", em minusculas e sem acento (nodes.py:96). Entao o
 * termo no estado carrega a versao acentuada da mesma palavra. Nada e
 * inventado aqui: e o dado que ja chegou.
 */
export function campoAcentuado(campo: string, termo: string): string {
  const token = termo.split(/\s+/).find((t) => normalizar(t) === campo);
  return token ?? campo;
}

/** A correcao em linguagem de gente.
 *
 * Exibir o par `campo = valor` cru faz o leitor processar chave-valor em vez
 * de ler a frase. O par continua na tela, em mono cinza, logo abaixo.
 */
export function fraseDaCorrecao(correcao: CorrecaoProposta, termo: string): string {
  const titulo = TITULOS[correcao.sku] ?? correcao.sku;
  if (VALORES_VERDADEIROS.has(correcao.valor.toLowerCase())) {
    return `Marcar “${titulo}” como ${campoAcentuado(correcao.campo, termo)} no catálogo`;
  }
  return `Definir ${correcao.campo} de “${titulo}” como ${correcao.valor}`;
}
