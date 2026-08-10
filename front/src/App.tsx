import { useCallback, useMemo, useState } from "react";
import type { EstadoVenditus } from "./dados/contrato";
import { STATUS_TERMINAIS } from "./dados/contrato";
import { usarExecucao } from "./ganchos/usarExecucao";
import { indicadores } from "./logica/indicadores";
import { AvisoDeBackend } from "./componentes/AvisoDeBackend";
import { BarraDeAprovacao } from "./componentes/BarraDeAprovacao";
import { BlocoDeRecusa } from "./componentes/BlocoDeRecusa";
import { BlocoDeResultado } from "./componentes/BlocoDeResultado";
import { Cabecalho } from "./componentes/Cabecalho";
import { CartaoDeDiagnostico } from "./componentes/CartaoDeDiagnostico";
import { EstadoVazio } from "./componentes/EstadoVazio";
import { FaixaDeIndicadores } from "./componentes/FaixaDeIndicadores";
import { LinhaDoTempo } from "./componentes/LinhaDoTempo";
import { ListaDeBuscas } from "./componentes/ListaDeBuscas";

export default function App() {
  /** As execucoes que chegaram ao fim, indexadas pelo termo.
   *
   * Rodar o mesmo termo de novo substitui o resultado anterior, em vez de
   * empilhar — senao os indicadores contariam a mesma busca duas vezes.
   */
  const [encerradas, setEncerradas] = useState<Record<string, EstadoVenditus>>({});

  const aoEncerrar = useCallback((estado: EstadoVenditus) => {
    setEncerradas((atuais) => ({ ...atuais, [estado.termo]: estado }));
  }, []);

  const execucao = usarExecucao(aoEncerrar);
  const { estado, carregando, erro } = execucao;

  const dados = useMemo(
    () => indicadores(Object.values(encerradas)),
    [encerradas],
  );

  const terminou =
    estado !== undefined &&
    estado?.status !== undefined &&
    STATUS_TERMINAIS.includes(estado.status) &&
    !carregando;

  const bloqueado = estado?.decisao_guarda?.permitir === false;
  const esperandoVoce = estado?.status === "aprovado_pelo_guarda" && !carregando;

  return (
    <div className="min-h-dvh">
      {/* Responsivo mobile esta fora de escopo. Avisar e melhor que quebrar
          em silencio numa tela estreita. */}
      <p className="border-b border-aviso bg-[#1F1A0A] px-5 py-2 text-xs text-aviso lg:hidden">
        O Venditus foi desenhado para tela larga. Abaixo de 1024px o layout não
        acompanha — use um monitor.
      </p>

      <Cabecalho>
        <FaixaDeIndicadores dados={dados} />
      </Cabecalho>

      <AvisoDeBackend
        jaCorrigido={Object.values(encerradas).some((e) => e.resultados_antes > 0)}
      />

      <div className="flex min-w-[960px]">
        <ListaDeBuscas
          encerradas={encerradas}
          termoAtual={execucao.termoAtual}
          ocupado={carregando}
          aoEscolher={execucao.iniciar}
        />

        <main className="flex-1 p-4">
          {execucao.termoAtual === null ? (
            <EstadoVazio />
          ) : (
            <>
              {erro ? (
                <p
                  role="alert"
                  className="mb-3 rounded-lg border border-perigo bg-[#1E0E0E] px-3 py-2 text-xs leading-relaxed text-[#FF6B6B]"
                >
                  A execução falhou: {String(erro)}. Clique no termo de novo para
                  tentar outra vez.
                </p>
              ) : null}

              <LinhaDoTempo status={estado?.status} segundos={execucao.segundos} />

              {estado?.diagnostico ? (
                <CartaoDeDiagnostico
                  diagnostico={estado.diagnostico}
                  termo={estado.termo}
                />
              ) : null}

              {esperandoVoce && estado ? (
                <BarraDeAprovacao
                  estado={estado}
                  ocupado={carregando}
                  aoResponder={execucao.responder}
                />
              ) : null}

              {bloqueado && estado ? <BlocoDeRecusa estado={estado} /> : null}

              {terminou && estado && !bloqueado ? (
                <BlocoDeResultado estado={estado} />
              ) : null}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
