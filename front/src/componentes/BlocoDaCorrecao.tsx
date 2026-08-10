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
      {/* A linha de baixo diz ONDE a escrita cai, nao o que ela vale — o
          valor ja esta na frase de cima ("como impermeavel", "como 80"), e
          repeti-lo como `= "true"` so trazia sintaxe de codigo para uma tela
          que um lojista le. */}
      <p className="mt-1.5 text-[10.5px] text-[#6B6B6B]">
        no produto <span className="text-[#8A8A8A]">{correcao.sku}</span> · campo{" "}
        <span className="font-mono text-[#8A8A8A]">{correcao.campo}</span>
        {destino ? ` · ${destino}` : ""}
      </p>
    </div>
  );
}
