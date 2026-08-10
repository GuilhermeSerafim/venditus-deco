export function EstadoVazio() {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center gap-1.5 px-8 text-center">
      <p className="text-sm font-semibold">Escolha uma busca à esquerda.</p>
      <p className="max-w-md text-xs leading-relaxed text-texto-fraco">
        O Venditus lê a busca que falhou, investiga a causa no catálogo e audita
        as devoluções do produto antes de propor qualquer escrita.
      </p>
    </div>
  );
}
