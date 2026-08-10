import type { EstadoVenditus } from "../dados/contrato";

export function BlocoDeResultado({ estado }: { estado: EstadoVenditus }) {
  /* `escreveu` decide, nunca `status`: o verificador sobrescreve o
     "sem_correcao" do executor com "aplicado" (nodes.py:67), entao existe
     estado final com status="aplicado" e nenhuma escrita. */
  if (!estado.escreveu) {
    return (
      <section className="rounded-lg border border-borda bg-cartao p-3.5">
        <p className="text-[13.5px] font-semibold">Nada foi gravado.</p>
        <p className="mt-1 text-[11.5px] text-texto-fraco">
          {estado.status === "rejeitado"
            ? "Você rejeitou a correção. O catálogo continua como estava."
            : "O diagnóstico não propôs correção de catálogo — o problema não está no texto do produto."}
        </p>
      </section>
    );
  }

  /* Escrita registrada e busca inalterada nao e sucesso — e anomalia.
     Anunciar "achava 0, agora acha 0" em corpo 20 parece defeito do produto,
     quando o que houve foi a escrita ser pulada (o executor considera a
     correcao ja aplicada) ou a alteracao ainda nao ter propagado. */
  if (estado.resultados_depois <= estado.resultados_antes) {
    return (
      <section className="rounded-lg border border-aviso bg-[#1F1A0A] p-3.5">
        <p className="text-[15px] font-semibold text-aviso">
          A correção foi registrada, mas a busca não mudou.
        </p>
        <p className="mt-1 text-[11.5px] leading-relaxed text-texto-fraco">
          Continua com{" "}
          <strong className="text-texto">
            {estado.resultados_depois}{" "}
            {estado.resultados_depois === 1 ? "resultado" : "resultados"}
          </strong>
          . O atributo já constava no catálogo, ou a alteração ainda não
          propagou na loja.
        </p>
        <p className="mt-2 font-mono text-[10.5px] text-[#6B6B6B]">
          fix_id {estado.fix_id}
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-gold-escuro bg-cartao p-3.5">
      <p className="text-xl font-bold">
        A busca achava{" "}
        <span className="tabular-nums text-texto-fraco">{estado.resultados_antes}</span>.{" "}
        Agora acha{" "}
        <span className="tabular-nums text-gold-claro">{estado.resultados_depois}</span>.
      </p>
      <p className="mt-2 font-mono text-[10.5px] text-[#6B6B6B]">
        fix_id {estado.fix_id} · determinístico, para o executor não gravar duas vezes
      </p>
    </section>
  );
}
