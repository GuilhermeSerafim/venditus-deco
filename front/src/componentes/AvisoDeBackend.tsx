import { useEffect, useState } from "react";

const COMANDO = ".\\.venv\\Scripts\\langgraph.exe dev --no-browser --port 2024";

/** Faixa de indisponibilidade do servico.
 *
 * Trata SO falha de infraestrutura — nao "catalogo ja corrigido", que e
 * operacao normal e mora inline, junto da execucao. Misturar as duas fazia a
 * faixa aparecer depois de um "Rejeitar" bem-sucedido, sem relacao nenhuma
 * com o que o usuario acabara de fazer.
 */
export function AvisoDeBackend() {
  const [noAr, setNoAr] = useState<boolean | null>(null);

  useEffect(() => {
    let vivo = true;
    fetch("/api/ok")
      .then((r) => {
        if (vivo) setNoAr(r.ok);
      })
      .catch(() => {
        if (vivo) setNoAr(false);
      });
    return () => {
      vivo = false;
    };
  }, []);

  if (noAr === false) {
    return (
      <div role="alert" className="border-b border-perigo bg-[#1E0E0E] px-5 py-2">
        <p className="text-xs font-semibold text-[#FF6B6B]">
          Não foi possível falar com o serviço do Venditus.
        </p>
        {/* O comando fica porque, quando esta faixa aparece, quem esta na
            frente da tela e quem opera a demo — e nao ha nada a fazer pela
            interface. Some assim que o servico responde. */}
        <code className="mt-1 block font-mono text-[10.5px] text-texto-fraco">
          {COMANDO}
        </code>
      </div>
    );
  }

  return null;
}
