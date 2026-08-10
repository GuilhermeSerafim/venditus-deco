import type { EstadoVenditus } from "../dados/contrato";
import {
  BUSCAS,
  CONVERSAO_ASSUMIDA,
  TICKET_MEDIO_BRL,
  perdaEstimada,
} from "../dados/espelho";
import { moeda } from "../logica/formato";

/** O desfecho de um termo ja executado, para o selo na lista.
 *
 * Quem decide se houve escrita e `escreveu`, nunca `status`: o verificador
 * sobrescreve o "sem_correcao" do executor com "aplicado" (nodes.py:67), entao
 * existe estado final com status="aplicado" e nenhuma escrita.
 */
function selo(estado: EstadoVenditus | undefined) {
  if (!estado) return null;
  if (estado.status === "quarentena") {
    return <span className="text-perigo">recusado</span>;
  }
  if (estado.escreveu) {
    // Verde so quando a busca melhorou de fato. Escrita aplicada que nao move
    // a busca nao e sucesso — foi o caso da mochila de 60L marcada como
    // "80 litros": gravou e a busca continuou em zero.
    if (estado.resultados_depois > estado.resultados_antes) {
      return (
        <span className="text-sucesso">
          gravado · {estado.resultados_antes} → {estado.resultados_depois}
        </span>
      );
    }
    return <span className="text-aviso">gravado · busca não mudou</span>;
  }
  if (estado.status === "rejeitado") {
    return <span className="text-texto-fraco">rejeitado por você</span>;
  }
  return <span className="text-texto-fraco">sem correção</span>;
}

export function ListaDeBuscas({
  encerradas,
  termoAtual,
  ocupado,
  aoEscolher,
}: {
  encerradas: Record<string, EstadoVenditus>;
  termoAtual: string | null;
  ocupado: boolean;
  aoEscolher: (termo: string, volume: number) => void;
}) {
  const ordenadas = [...BUSCAS].sort(
    (a, b) => perdaEstimada(b.volume) - perdaEstimada(a.volume),
  );

  return (
    <nav className="w-56 shrink-0 border-r border-borda p-2.5">
      <h2 className="px-1.5 pb-2 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        Buscas sem resultado
      </h2>

      {ordenadas.map((busca) => {
        const encerrada = encerradas[busca.termo];
        const ativa = termoAtual === busca.termo;
        return (
          <button
            key={busca.termo}
            type="button"
            disabled={ocupado}
            onClick={() => aoEscolher(busca.termo, busca.volume)}
            className={`mb-1 block min-h-11 w-full rounded-md border-l-[3px] px-2 py-2 text-left transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-50 ${
              ativa
                ? "border-l-gold bg-[#17130A]"
                : "cursor-pointer border-l-transparent hover:bg-secundario"
            }`}
          >
            <span className="block text-[12.5px] font-semibold">{busca.termo}</span>
            <span className="mt-0.5 flex justify-between gap-2 text-[10.5px] tabular-nums text-texto-fraco">
              <span>{selo(encerrada) ?? `${busca.volume} buscas/mês`}</span>
              <span>{moeda(perdaEstimada(busca.volume))}</span>
            </span>
          </button>
        );
      })}

      {/* A formula fica sempre visivel: o R$ e ESTIMATIVA, e o HANDOFF exige
          que ela apareca na tela junto do numero, rotulada como tal. */}
      <p className="mt-3 border-t border-borda px-1.5 pt-2 text-[10.5px] leading-relaxed text-[#737373]">
        estimativa · volume × {CONVERSAO_ASSUMIDA * 100}% de conversão ×{" "}
        {moeda(TICKET_MEDIO_BRL)} de ticket médio (ABComm 2026)
      </p>
    </nav>
  );
}
