import type { EstadoVenditus } from "../dados/contrato";
import { dias } from "../logica/formato";

function IconeProibido() {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className="size-4 shrink-0 fill-none stroke-current stroke-2 [stroke-linecap:round]"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="m4.9 4.9 14.2 14.2" />
    </svg>
  );
}

/** A tela de recusa. E o climax do pitch, nao um estado de erro.
 *
 * O backend NAO informa QUAIS devolucoes contradizem — so quantas. E esta
 * certo em nao informar: fazer o LLM reescrever as frases lhe daria a chance
 * de parafrasear o cliente, e o comentario em nodes.py:179 registra que essa
 * foi uma decisao consciente.
 *
 * Por isso a lista aqui e rotulada pelo que ela e — o que o guarda leu — com
 * o contador no titulo. Filtrar por palavra-chave no front seria inventar uma
 * inferencia que o backend nao fez. E ver onze reclamacoes seguidas, das quais
 * oito falam de agua, e mais forte que ver oito marcadas.
 */
export function BlocoDeRecusa({ estado }: { estado: EstadoVenditus }) {
  const guarda = estado.decisao_guarda;
  const lidas = estado.devolucoes_consultadas ?? [];

  const ordenadas = [...lidas].sort((a, b) => a.dias_atras - b.dias_atras);

  return (
    <section className="mb-3 rounded-lg border border-perigo bg-gradient-to-b from-[#1A0E0E] to-cartao p-3.5">
      <h2 className="flex items-center gap-2 text-sm font-bold text-[#FF6B6B]">
        <IconeProibido />
        {/* A palavra acompanha a cor. Comunicar o bloqueio so pelo vermelho
            excluiria quem nao distingue a cor — e o icone sozinho tambem. */}
        CORREÇÃO RECUSADA
      </h2>

      <p className="mt-1 text-[11.5px] leading-relaxed text-texto-fraco">
        <strong className="text-[#FF9B9B]">
          {guarda?.devolucoes_contraditorias} das {lidas.length} devoluções
          contradizem
        </strong>{" "}
        o atributo que seria gravado.
      </p>

      <h3 className="pt-3 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        as {lidas.length} devoluções que o guarda leu
      </h3>

      <ul className="my-2 max-h-56 overflow-y-auto pr-1">
        {ordenadas.map((devolucao, indice) => (
          <li
            key={`${devolucao.sku}-${devolucao.dias_atras}-${indice}`}
            className="my-1.5 flex items-baseline justify-between gap-3 border-l-2 border-[#7F1D1D] px-3 py-1"
          >
            {/* As frases sao o payload: maiores que o corpo do texto.
                "8 devolucoes contradizem" e uma afirmacao; ler o que o
                cliente escreveu e prova. */}
            <q className="text-[13px] italic leading-relaxed text-[#F0F0F0]">
              {devolucao.motivo}
            </q>
            <span className="shrink-0 text-[10px] tabular-nums text-[#737373]">
              {dias(devolucao.dias_atras)}
            </span>
          </li>
        ))}
      </ul>

      {guarda?.justificativa ? (
        <div className="rounded-md bg-[#191919] px-3 py-2.5">
          <h3 className="pb-1 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
            justificativa do guarda
          </h3>
          <p className="text-xs leading-relaxed text-[#C4C4C4]">
            {guarda.justificativa}
          </p>
        </div>
      ) : null}

      <p className="mt-3 text-[13.5px] font-semibold">
        O catálogo continua como estava.
      </p>

      {/* O fato em destaque; o encaminhamento como narrativa declarada.
          "Quarentena" sozinha prometeria uma acao que nao acontece: o no nao
          retira o produto do ar nem abre chamado, ele encerra o grafo. Numa
          interface cuja tese e "a gente recusa quando nao sabe", exagerar o
          que o sistema faz seria o erro mais caro possivel. */}
      <p className="mt-2.5 border-t border-borda pt-2.5 text-[10.5px] leading-relaxed text-[#737373]">
        O caso vira hipótese para o time de qualidade — o Venditus não abre
        chamado, ele para e mostra o porquê.{" "}
        <span className="font-mono text-[#5C5C5C]">status: {estado.status}</span>
      </p>
    </section>
  );
}
