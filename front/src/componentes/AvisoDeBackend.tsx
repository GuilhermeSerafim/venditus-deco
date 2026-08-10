import { useEffect, useState } from "react";

const COMANDO = "cd back && .venv\\Scripts\\langgraph dev --no-browser --port 2024";
const RESET = "cd back && .venv\\Scripts\\python scripts/verificar_shopify.py --resetar";

export function AvisoDeBackend({ jaCorrigido }: { jaCorrigido: boolean }) {
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
          O backend não responde em 127.0.0.1:2024.
        </p>
        <code className="mt-1 block font-mono text-[10.5px] text-texto-fraco">
          {COMANDO}
        </code>
      </div>
    );
  }

  if (jaCorrigido) {
    return (
      <div role="status" className="border-b border-gold-escuro bg-[#17130A] px-5 py-2">
        <p className="text-xs font-semibold text-gold-claro">
          Esta correção já está aplicada na loja — a busca já achava o produto antes de rodar.
        </p>
        <code className="mt-1 block font-mono text-[10.5px] text-texto-fraco">
          {RESET}
        </code>
      </div>
    );
  }

  return null;
}
