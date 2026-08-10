import type { Causa, Diagnostico } from "../dados/contrato";
import { TITULOS } from "../dados/espelho";
import { BlocoDaCorrecao } from "./BlocoDaCorrecao";

/** As seis causas de models.py, em linguagem de gente.
 *
 * O jurado do pitch le "atributo_ausente" e nao entende nada; le "Atributo
 * faltando" e entende tudo.
 */
const CAUSA_EM_PORTUGUES: Record<Causa, string> = {
  typo: "Erro de digitação na busca",
  sinonimo: "Sinônimo que o catálogo não usa",
  atributo_ausente: "Atributo faltando",
  categorizacao_errada: "Categoria errada",
  sem_estoque: "Produto sem estoque",
  sem_sortimento: "A loja não vende isso",
};

function IconeLupa() {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className="size-4 shrink-0 fill-none stroke-gold stroke-2 [stroke-linecap:round]"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

export function CartaoDeDiagnostico({
  diagnostico,
  termo,
}: {
  diagnostico: Diagnostico;
  termo: string;
}) {
  const correcao = diagnostico.correcao;

  return (
    <section className="mb-3 rounded-lg border border-borda bg-cartao p-3.5">
      <h2 className="flex flex-wrap items-center gap-2 text-sm font-bold">
        <IconeLupa />
        {CAUSA_EM_PORTUGUES[diagnostico.causa]}
        <span className="rounded border border-borda bg-secundario px-1.5 py-0.5 text-[9.5px] uppercase tracking-wider text-texto-fraco">
          confiança {diagnostico.confianca}
        </span>
      </h2>

      {correcao ? (
        <p className="mt-1 text-[11.5px] text-texto-fraco">
          {correcao.sku} · {TITULOS[correcao.sku] ?? "produto fora do espelho"}
        </p>
      ) : null}

      <h3 className="mt-3 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        o que o catálogo diz hoje
      </h3>
      {/* A evidencia e o trecho literal que o investigador citou. E ela que
          sustenta o diagnostico — sem ela, o cartao seria so uma afirmacao. */}
      <blockquote className="border-l-2 border-[#333] pl-3 text-[12.5px] italic leading-relaxed text-[#D4D4D4]">
        &ldquo;{diagnostico.evidencia}&rdquo;
      </blockquote>

      {correcao ? (
        <>
          <h3 className="mb-1 mt-3.5 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
            a correção proposta
          </h3>
          <BlocoDaCorrecao correcao={correcao} termo={termo} />
        </>
      ) : (
        <p className="mt-3.5 text-[13px] leading-relaxed">
          Nenhuma correção de catálogo se aplica — o problema não está no texto
          do produto.
        </p>
      )}
    </section>
  );
}
