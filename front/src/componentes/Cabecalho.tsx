import type { ReactNode } from "react";

export function Cabecalho({ children }: { children: ReactNode }) {
  return (
    <header className="flex items-center gap-4 border-b border-borda px-5 py-3">
      <img src="/logo-venditus.png" alt="Venditus" className="h-7 w-auto" />
      <span className="font-titulo text-xs font-extrabold tracking-[0.14em] text-gold-claro">
        VENDITUS
      </span>
      <div className="ml-auto">{children}</div>
    </header>
  );
}
