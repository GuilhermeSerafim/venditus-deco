import { useCallback, useEffect, useRef, useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import type { EstadoVenditus } from "../dados/contrato";
import { STATUS_TERMINAIS } from "../dados/contrato";
import { perdaEstimada } from "../dados/espelho";

/** `/api` e o proxy do Vite para 127.0.0.1:2024 — nunca a origem direta. */
const URL_API = "/api";

/** A chave de `graphs` em back/langgraph.json. Nao e o nome do modulo. */
const ASSISTENTE = "venditus";

/** Uma execucao do grafo, do clique ate o estado terminal.
 *
 * `aoEncerrar` recebe o estado final de cada execucao que chegou ao fim. E o
 * que alimenta os indicadores do painel, espelhando a assinatura de
 * metrics.py, que opera sobre uma lista de estados finais.
 */
export function usarExecucao(aoEncerrar: (estado: EstadoVenditus) => void) {
  const [termoAtual, setTermoAtual] = useState<string | null>(null);
  const [segundos, setSegundos] = useState(0);

  // O callback vive numa ref porque o useStream captura as opcoes na criacao;
  // sem isso, um `aoEncerrar` recriado a cada render deixaria o hook chamando
  // a versao velha, com o estado velho fechado dentro.
  const encerrar = useRef(aoEncerrar);
  encerrar.current = aoEncerrar;

  const fluxo = useStream<EstadoVenditus>({
    apiUrl: URL_API,
    assistantId: ASSISTENTE,
    onFinish: (snapshot) => {
      // onFinish dispara ao fim de CADA run, e o caso aprovado tem dois: o
      // primeiro para na pausa com status "aprovado_pelo_guarda", que nao e
      // terminal. Sem este filtro, o painel contaria a mesma execucao duas
      // vezes e a taxa de recusa sairia errada.
      const estado = snapshot?.values;
      if (estado && STATUS_TERMINAIS.includes(estado.status)) {
        encerrar.current(estado);
      }
    },
  });

  const estado = fluxo.values;
  const carregando = fluxo.isLoading;

  /** Relogio do passo ativo.
   *
   * Os dois nos de LLM levam de 15 a 40s (reasoning_effort medium e high).
   * Sem o contador, a tela parece travada — e travado e a leitura errada de
   * um agente raciocinando.
   */
  useEffect(() => {
    if (!carregando) return;
    setSegundos(0);
    const inicio = Date.now();
    const relogio = setInterval(
      () => setSegundos(Math.floor((Date.now() - inicio) / 1000)),
      1000,
    );
    return () => clearInterval(relogio);
  }, [carregando, estado?.status]);

  const iniciar = useCallback(
    (termo: string, volume: number) => {
      setTermoAtual(termo);
      setSegundos(0);
      // perda_estimada e obrigatoria: `aprovacao` le state["perda_estimada"]
      // direto (graph.py:40) e nenhum no a calcula. Sem ela, o run quebra com
      // KeyError na pausa, depois de duas chamadas de LLM ja pagas.
      void fluxo.submit({ termo, volume, perda_estimada: perdaEstimada(volume) });
    },
    [fluxo],
  );

  const responder = useCallback(
    (aprovado: boolean) => {
      setSegundos(0);
      void fluxo.submit(undefined, { command: { resume: { aprovado } } });
    },
    [fluxo],
  );

  return {
    fluxo,
    estado,
    carregando,
    erro: fluxo.error,
    iniciar,
    responder,
    termoAtual,
    segundos,
  };
}
