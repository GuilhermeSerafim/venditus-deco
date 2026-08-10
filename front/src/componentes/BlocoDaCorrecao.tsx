import type { CorrecaoProposta } from "../dados/contrato";
import { fraseDaCorrecao } from "../logica/formato";

/** A correcao proposta, em duas camadas.
 *
 * A frase em portugues manda; o par `campo = valor` fica embaixo, em mono
 * cinza, como prova. Exibir so o par cru faz o leitor processar chave-valor
 * em vez de ler a frase — e o jurado do pitch tem cinco segundos.
 *
 * Mesmo padrao dos nomes dos nos na linha do tempo: rotulo humano grande,
 * verdade tecnica pequena.
 *
 * Vive num componente proprio porque aparece no diagnostico E na barra de
 * aprovacao. Duas copias divergiriam.
 */
export function BlocoDaCorrecao({
  correcao,
  termo,
  destino,
}: {
  correcao: CorrecaoProposta;
  termo: string;
  /** Onde a escrita vai cair, quando vale a pena dizer. Ex.: "loja Shopify". */
  destino?: string;
}) {
  return (
    <div className="rounded-lg border-l-[3px] border-gold-escuro bg-[#191919] px-3 py-2.5">
      <p className="text-[15px] font-semibold leading-snug">
        {fraseDaCorrecao(correcao, termo)}
      </p>
      <p className="mt-1.5 font-mono text-[10.5px] text-[#6B6B6B]">
        atributo {correcao.campo} = &quot;{correcao.valor}&quot; · {correcao.sku}
        {destino ? ` · ${destino}` : ""}
      </p>
    </div>
  );
}
