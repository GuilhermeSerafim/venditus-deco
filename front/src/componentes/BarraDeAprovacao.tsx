import type { EstadoVenditus } from "../dados/contrato";
import { CONVERSAO_ASSUMIDA, TICKET_MEDIO_BRL } from "../dados/espelho";
import { moeda } from "../logica/formato";
import { BlocoDaCorrecao } from "./BlocoDaCorrecao";

function IconeEscudo() {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className="size-4 shrink-0 fill-none stroke-gold-claro stroke-2 [stroke-linecap:round] [stroke-linejoin:round]"
    >
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

/** A pausa para decisao humana. Nada e escrito no catalogo sem passar aqui.
 *
 * Este componente aparece quando o grafo esta suspenso no interrupt() do no
 * `aprovacao`. A escrita mora no no seguinte, e e idempotente — retomar de um
 * interrupt re-executa o no inteiro.
 */
export function BarraDeAprovacao({
  estado,
  ocupado,
  aoResponder,
}: {
  estado: EstadoVenditus;
  ocupado: boolean;
  aoResponder: (aprovado: boolean) => void;
}) {
  const correcao = estado.diagnostico?.correcao ?? null;
  const guarda = estado.decisao_guarda;

  return (
    <section className="mb-3 rounded-lg border border-gold-escuro bg-cartao p-3.5">
      <h2 className="flex items-center gap-2 text-sm font-bold">
        <IconeEscudo />
        Liberado pelo pós-venda
      </h2>

      {guarda?.justificativa ? (
        <p className="mt-1 text-[11.5px] leading-relaxed text-texto-fraco">
          {guarda.justificativa}
        </p>
      ) : null}

      {correcao ? (
        <div className="mt-3">
          <BlocoDaCorrecao
            correcao={correcao}
            termo={estado.termo}
            destino="loja Shopify"
          />
        </div>
      ) : null}

      {/* O dinheiro pesa mais que os botoes: a decisao e sobre ele. */}
      <p className="mt-3.5 flex flex-wrap items-end gap-x-3">
        <span className="text-[34px] font-extrabold leading-none tracking-tight text-gold-claro tabular-nums">
          {moeda(estado.perda_estimada)}
        </span>
        <span className="pb-0.5 text-[15px] font-semibold text-texto-fraco">
          / mês
        </span>
      </p>
      <p className="mt-1.5 text-xs text-[#D4D4D4]">
        é o que essa busca deixa de vender enquanto não acha nada.
      </p>
      {/* ESTIMATIVA, com a formula na tela — exigencia do HANDOFF. */}
      <p className="mt-0.5 text-[10.5px] leading-relaxed text-[#6B6B6B]">
        estimativa · {estado.volume} buscas × {CONVERSAO_ASSUMIDA * 100}% de
        conversão × {moeda(TICKET_MEDIO_BRL)} de ticket médio (ABComm 2026)
      </p>

      <div className="mt-4 flex flex-wrap gap-2.5 border-t border-borda pt-3.5">
        <button
          type="button"
          disabled={ocupado}
          onClick={() => aoResponder(true)}
          className="min-h-11 cursor-pointer rounded-lg bg-gold px-5 py-2.5 text-[13px] font-bold text-[#171717] shadow-[0_0_22px_rgba(217,165,32,0.25)] transition-opacity duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold-claro disabled:cursor-not-allowed disabled:opacity-50"
        >
          {ocupado ? "Gravando…" : "Aprovar e gravar no catálogo"}
        </button>
        <button
          type="button"
          disabled={ocupado}
          onClick={() => aoResponder(false)}
          className="min-h-11 cursor-pointer rounded-lg border border-borda px-5 py-2.5 text-[13px] font-bold text-texto-fraco transition-colors duration-200 hover:bg-secundario focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-50"
        >
          Rejeitar
        </button>
      </div>
    </section>
  );
}
