/** Nota inline: a busca ja retornava resultado antes desta execucao.
 *
 * Nao e erro, e contexto — e informacao que o lojista quer. Se a busca ja
 * achava o produto, ou o atributo foi preenchido antes, ou o catalogo mudou
 * desde que este termo entrou na lista. Nos dois casos, o ganho medido nao e
 * o ganho real, e quem le precisa saber disso ao decidir.
 *
 * Vive junto da execucao, e nao numa faixa global, porque fala de UMA busca.
 * Como faixa, aparecia solta no topo depois de qualquer acao — inclusive de
 * um "Rejeitar" que nao tinha relacao nenhuma com isso.
 */
export function NotaDeCatalogo({ resultadosAntes }: { resultadosAntes: number }) {
  if (resultadosAntes <= 0) return null;

  return (
    <p className="mb-3 rounded-lg border border-borda bg-secundario px-3 py-2 text-[11.5px] leading-relaxed text-texto-fraco">
      Esta busca já retornava{" "}
      <strong className="text-texto">
        {resultadosAntes} {resultadosAntes === 1 ? "resultado" : "resultados"}
      </strong>{" "}
      antes desta execução — o atributo pode ter sido preenchido antes, ou o
      catálogo mudou. O ganho medido aqui não reflete a correção sozinha.
    </p>
  );
}
