import type { Status } from "../dados/contrato";
import { derivarPassos, type EstadoPasso } from "../logica/passos";

const CAIXA: Record<EstadoPasso, string> = {
  pendente: "border-borda bg-cartao",
  ativo: "border-gold bg-[#211B0C]",
  concluido: "border-gold-fraco bg-[#17130A]",
  bloqueado: "border-perigo bg-[#1E0E0E]",
  inalcancavel: "border-borda bg-cartao opacity-30",
};

const ROTULO: Record<EstadoPasso, string> = {
  pendente: "text-[#D4D4D4]",
  ativo: "text-gold-claro",
  concluido: "text-gold-claro",
  bloqueado: "text-[#FCA5A5]",
  inalcancavel: "text-[#D4D4D4] line-through",
};

/** Uma bolinha que pulsa, para o passo ativo nao parecer congelado. */
function Pulso() {
  return (
    <span
      aria-hidden="true"
      className="inline-block size-1.5 animate-pulse rounded-full bg-gold-claro motion-reduce:animate-none"
    />
  );
}

/** Os seis nos do grafo, acendendo conforme a execucao avanca.
 *
 * O momento que importa: quando o guarda bloqueia, os passos seguintes ficam
 * riscados e a 30%. Nao e decoracao — e a tese do produto virando pixel. O
 * caminho ate a escrita deixa de existir, e isso e topologia do grafo, nao
 * uma sugestao ao modelo.
 */
export function LinhaDoTempo({
  status,
  segundos,
}: {
  status: Status | undefined;
  segundos: number;
}) {
  const passos = derivarPassos(status);

  return (
    <ol className="mb-4 flex gap-1">
      {passos.map((passo) => {
        const ativo = passo.estado === "ativo";
        return (
          <li
            key={passo.no}
            aria-current={ativo ? "step" : undefined}
            className={`flex-1 rounded-md border px-2 py-1.5 transition-all duration-200 motion-reduce:transition-none ${CAIXA[passo.estado]}`}
          >
            <span
              className={`flex items-center gap-1.5 text-[11px] font-semibold leading-tight ${ROTULO[passo.estado]}`}
            >
              {ativo ? <Pulso /> : null}
              {passo.rotulo}
            </span>
            <span className="mt-0.5 block font-mono text-[8.5px] text-[#5C5C5C]">
              {/* O relogio so no passo ativo. Os dois nos de LLM levam de 15 a
                  40s; sem o contador a tela parece travada, e travado e a
                  leitura errada de um agente raciocinando. */}
              {ativo && segundos > 0 ? `${passo.no} · ${segundos}s` : passo.no}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
