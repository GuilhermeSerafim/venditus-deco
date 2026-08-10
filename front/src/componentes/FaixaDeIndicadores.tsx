import type { Indicadores } from "../logica/indicadores";
import { moeda } from "../logica/formato";

function Numero({
  valor,
  rotulo,
  destaque = false,
}: {
  valor: string;
  rotulo: string;
  destaque?: boolean;
}) {
  return (
    <div
      className={`min-w-[128px] rounded-lg border px-3 py-1.5 text-right ${
        destaque ? "border-gold-escuro bg-[#17130A]" : "border-borda bg-cartao"
      }`}
    >
      <b
        className={`block text-lg font-bold tabular-nums leading-tight ${
          destaque ? "text-gold-claro" : "text-texto"
        }`}
      >
        {valor}
      </b>
      <span className="text-[8.5px] uppercase tracking-[0.09em] text-texto-fraco">
        {rotulo}
      </span>
    </div>
  );
}

export function FaixaDeIndicadores({ dados }: { dados: Indicadores }) {
  const vazio = dados.execucoes === 0;

  return (
    <div className="flex gap-2">
      <Numero
        valor={vazio ? "—" : moeda(dados.receitaRecuperada)}
        rotulo="recuperado/mês"
      />
      {/* "Correcoes recusadas" recebe o mesmo peso visual do R$, como o
          HANDOFF pede: e a metrica que nenhum concorrente calcula, porque
          nenhum tem o sinal de pre-venda e o de pos-venda no mesmo motor. */}
      <Numero
        valor={vazio ? "—" : `${dados.bloqueados} de ${dados.execucoes}`}
        rotulo="correções recusadas"
        destaque
      />
      <Numero
        valor={
          dados.resultadosAntes === null
            ? "—"
            : `${dados.resultadosAntes} → ${dados.resultadosDepois}`
        }
        rotulo="a busca acha"
      />
    </div>
  );
}
