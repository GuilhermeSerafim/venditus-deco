# Front do Venditus — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Objetivo:** Construir a interface que roda os dois casos do pitch ao vivo contra o `langgraph dev`, com a tela de recusa como clímax.

**Arquitetura:** SPA em Vite + React + TypeScript. Um `useStream` do `@langchain/langgraph-sdk` por execução; as execuções encerradas se acumulam num array que alimenta os indicadores, espelhando a assinatura de `metrics.py`. Toda a lógica que pode estar caladamente errada (linha do tempo, indicadores, formatação) vive em funções puras fora do React, com teste.

**Stack:** Vite 7 · React 19 · TypeScript · Tailwind v4 (plugin oficial do Vite, sem `tailwind.config.js`) · `@langchain/langgraph-sdk` · Vitest. **Sem shadcn/ui** (decisão D5 do spec).

**Spec:** [`docs/superpowers/specs/2026-08-09-venditus-front-design.md`](../specs/2026-08-09-venditus-front-design.md)

**Ambiente:** Node v22.18.0, npm 10.9.3. Todos os comandos rodam a partir de `front/`.

---

## Estrutura de arquivos

| arquivo | responsabilidade |
|---|---|
| `front/vite.config.ts` | plugins React e Tailwind; proxy `/api` → `127.0.0.1:2024` |
| `front/src/dados/contrato.ts` | tipos TS espelhando `state.py` e `models.py` |
| `front/src/dados/espelho.ts` | as 3 buscas, a fórmula da estimativa, os 5 títulos |
| `front/src/logica/formato.ts` | moeda, dias, campo acentuado, frase da correção |
| `front/src/logica/passos.ts` | `status` → os 6 passos da linha do tempo |
| `front/src/logica/indicadores.ts` | espelho de `metrics.py` |
| `front/src/ganchos/usarExecucao.ts` | embrulha o `useStream` |
| `front/src/componentes/*.tsx` | os 10 componentes de tela |
| `front/src/estilos/tema.css` | tokens gold dark; tokens light comentados |

**Fronteira:** nada fora de `front/` é modificado, exceto a linha 208 do `README.md` na Task 15.

---

### Task 0: Andaime do projeto

**Arquivos:**
- Criar: `front/package.json`, `front/vite.config.ts`, `front/tsconfig.json`, `front/tsconfig.node.json`, `front/index.html`, `front/src/main.tsx`, `front/src/App.tsx`, `front/src/estilos/tema.css`
- Preservar: `front/public/logo-venditus.png`, `front/HANDOFF.md`

- [ ] **Passo 1: Criar o projeto Vite dentro de `front/`**

O diretório `front/` já existe e tem conteúdo (`HANDOFF.md`, `public/logo-venditus.png`). Rode a partir da raiz do repositório:

```bash
cd front && npm create vite@latest . -- --template react-ts
```

Quando ele avisar que o diretório não está vazio, escolha **"Ignore files and continue"**. Ele não apaga `HANDOFF.md` nem `public/`.

- [ ] **Passo 2: Instalar as dependências**

```bash
cd front
npm install
npm install @langchain/langgraph-sdk
npm install -D tailwindcss @tailwindcss/vite vitest
```

- [ ] **Passo 3: Escrever `front/vite.config.ts`**

O proxy é a decisão D7 do spec: elimina CORS antes de ele existir.

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:2024",
        changeOrigin: true,
        rewrite: (caminho) => caminho.replace(/^\/api/, ""),
      },
    },
  },
});
```

- [ ] **Passo 4: Substituir `front/src/estilos/tema.css`**

Apague `front/src/index.css` e `front/src/App.css` gerados pelo template. Crie `front/src/estilos/tema.css`:

```css
@import "tailwindcss";

/* Tokens do HANDOFF §5. Um unico token de gold, definido uma vez. */
@theme {
  --color-fundo: #0d0d0d;
  --color-sutil: #121212;
  --color-cartao: #141414;
  --color-secundario: #1f1f1f;
  --color-borda: #262626;
  --color-texto: #ffffff;
  --color-texto-fraco: #a6a6a6;

  --color-gold: hsl(43 74% 49%);
  --color-gold-claro: hsl(45 80% 58%);
  --color-gold-escuro: hsl(40 85% 45%);
  --color-gold-fraco: hsl(43 40% 35%);

  --color-sucesso: hsl(142 71% 45%);
  --color-aviso: hsl(38 92% 50%);
  --color-perigo: hsl(0 84% 60%);

  --radius-vd: 0.625rem;
  --font-titulo: "Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif;
  --font-corpo: Inter, ui-sans-serif, system-ui, sans-serif;
}

/* Tema light do HANDOFF §5 — NAO ENTREGUE nesta rodada (decisao D6 do spec).
   Motivo: #D9A520 sobre #FFFFFF da 2,2:1, reprova em WCAG AA (4,5:1) e no piso
   de 3:1 para elemento grafico. No light o gold so pode ser preenchimento com
   texto preto (--primary-foreground 0 0% 9%) ou borda, nunca cor de texto.
   Valores preservados para a proxima rodada:
     background #FFFFFF · subtle #FAFAFA · card #FFFFFF
     secondary/muted/accent #F5F5F5 · border/input #E5E5E5
     muted-foreground #737373 · foreground #171717
     sidebar-hover #F7F4ED · gold-dark 38 80% 42% · gold-muted 43 30% 70% */

body {
  background: var(--color-fundo);
  color: var(--color-texto);
  font-family: var(--font-corpo);
  font-feature-settings: "tnum" 1;
}

h1, h2, h3 { font-family: var(--font-titulo); }
```

- [ ] **Passo 5: Escrever `front/index.html`**

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" href="/logo-venditus.png" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap"
      rel="stylesheet"
    />
    <title>Venditus</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Passo 6: Escrever `front/src/main.tsx`**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./estilos/tema.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Passo 7: Escrever um `front/src/App.tsx` mínimo**

```tsx
export default function App() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gold">Venditus</h1>
      <p className="text-texto-fraco">andaime no ar</p>
    </div>
  );
}
```

- [ ] **Passo 8: Verificar o andaime**

Em um terminal, suba o backend:

```bash
cd back && .venv/Scripts/langgraph dev --no-browser --port 2024
```

Em outro:

```bash
cd front && npm run dev
```

Abra `http://localhost:5173`. Esperado: "Venditus" em dourado sobre fundo quase preto, com a fonte Plus Jakarta Sans.

Confirme o proxy em um terceiro terminal:

```bash
curl http://localhost:5173/api/ok
```

Esperado: `{"ok":true}`. Se vier 404 ou erro de conexão, o proxy ou o backend está errado — **resolva antes de seguir.**

- [ ] **Passo 9: Commit**

```bash
git add front/
git commit -m "Andaime do front: Vite, React, Tailwind e o proxy para o langgraph dev"
```

---

### Task 1: Sonda da superfície do SDK

Esta é a Task 0 do front. `AGENTS.md` registra que a API do LangGraph muda entre versões e que descobrir isso tarde custa o plano inteiro. O mesmo vale para o SDK JavaScript. **Não pule.**

**Arquivos:**
- Criar: `front/src/Sonda.tsx`
- Modificar: `front/src/main.tsx`

- [ ] **Passo 1: Escrever a sonda**

`front/src/Sonda.tsx`:

```tsx
import { useStream } from "@langchain/langgraph-sdk/react";

export default function Sonda() {
  const fluxo = useStream<Record<string, unknown>>({
    apiUrl: "/api",
    assistantId: "venditus",
  });

  console.log("chaves do hook:", Object.keys(fluxo));
  console.log("values:", fluxo.values);
  console.log("isLoading:", fluxo.isLoading);
  console.log("interrupt:", (fluxo as Record<string, unknown>).interrupt);
  console.log("error:", fluxo.error);

  return (
    <div className="p-8 space-y-3">
      <button
        className="bg-gold text-black px-4 py-2 rounded font-bold"
        onClick={() =>
          fluxo.submit({
            termo: "tênis impermeável",
            volume: 340,
            perda_estimada: 3841.73,
          })
        }
      >
        1 · iniciar
      </button>

      <button
        className="border border-borda px-4 py-2 rounded ml-2"
        onClick={() =>
          fluxo.submit(undefined, { command: { resume: { aprovado: true } } })
        }
      >
        2 · aprovar
      </button>

      <pre className="text-xs text-texto-fraco overflow-auto max-h-[60vh]">
        {JSON.stringify(fluxo.values, null, 2)}
      </pre>
    </div>
  );
}
```

- [ ] **Passo 2: Apontar `main.tsx` para a sonda temporariamente**

Troque `import App from "./App";` por `import App from "./Sonda";` em `front/src/main.tsx`.

- [ ] **Passo 3: Rodar a sonda contra o backend real**

Com o backend no ar (`langgraph dev --no-browser --port 2024`) e `npm run dev` rodando, abra `http://localhost:5173`, abra o console do navegador e clique em **"1 · iniciar"**.

Confirme, um por um, e **anote o que divergir**:

| o que confirmar | esperado |
|---|---|
| `assistantId: "venditus"` é aceito | nenhum 404 na aba Network |
| o estado chega no `<pre>` | JSON com `termo`, `resultados_antes`, `status` |
| `status` evolui | `diagnosticando` → `diagnosticado` → `aprovado_pelo_guarda` |
| a pausa aparece | alguma chave do hook carrega o payload `{termo, perda_estimada, diagnostico, decisao_guarda}` — anote **o nome exato dessa chave** |
| `diagnostico.correcao` | `{sku, campo, valor}` com `campo: "impermeavel"` e `valor: "true"` |
| clicar em "2 · aprovar" retoma | `status` vira `aplicado` e `escreveu` vira `true` |

- [ ] **Passo 4: Rodar o caso bloqueado e confirmar as devoluções**

Recarregue a página (novo thread), troque o `termo` do botão 1 para `"capa de chuva impermeável"` e `volume` para `128`, `perda_estimada` para `1446.30`. Clique em "1 · iniciar".

Confirme:

| o que confirmar | esperado |
|---|---|
| `devolucoes_consultadas` serializa | **array com 11 objetos** `{sku, motivo, dias_atras}` |
| `decisao_guarda.permitir` | `false` |
| `decisao_guarda.devolucoes_contraditorias` | `8` |
| `status` final | `quarentena` |
| nenhuma pausa acontece | o run termina sem pedir aprovação |

Se `devolucoes_consultadas` vier vazio ou ausente, **pare e reporte** — sem ele a tela de recusa não existe, e o contorno seria espelhar o `seed.py` inteiro no front, que o spec proíbe.

- [ ] **Passo 5: Ajustar o plano se a superfície divergir**

Se o nome da chave da pausa, o formato do `command.resume` ou a assinatura do `submit` forem diferentes do que este plano assume, **corrija as Tasks 7, 11 e 12 agora**, antes de escrever qualquer componente.

- [ ] **Passo 6: Devolver `main.tsx` ao App e commitar a sonda**

Reverta o import em `main.tsx` para `import App from "./App";`. Mantenha `Sonda.tsx` no repositório — ela é útil quando algo quebrar durante a gravação.

```bash
git add front/src/Sonda.tsx front/src/main.tsx
git commit -m "Sonda da superficie do SDK, confirmada contra o backend real"
```

---

### Task 2: Contrato e espelho

**Arquivos:**
- Criar: `front/src/dados/contrato.ts`, `front/src/dados/espelho.ts`

- [ ] **Passo 1: Escrever `front/src/dados/contrato.ts`**

```ts
/** Tipos espelhando back/src/venditus/state.py e models.py. */

export type Causa =
  | "typo"
  | "sinonimo"
  | "atributo_ausente"
  | "categorizacao_errada"
  | "sem_estoque"
  | "sem_sortimento";

export type Confianca = "alta" | "media" | "baixa";

export interface CorrecaoProposta {
  sku: string;
  campo: string;
  valor: string;
}

export interface Diagnostico {
  causa: Causa;
  confianca: Confianca;
  evidencia: string;
  correcao: CorrecaoProposta | null;
}

export interface DecisaoGuarda {
  permitir: boolean;
  justificativa: string;
  devolucoes_contraditorias: number;
}

export interface Devolucao {
  sku: string;
  motivo: string;
  dias_atras: number;
}

export type Status =
  | "novo"
  | "diagnosticando"
  | "diagnosticado"
  | "aprovado_pelo_guarda"
  | "bloqueado_pelo_guarda"
  | "quarentena"
  | "aprovado"
  | "rejeitado"
  | "aplicado"
  | "sem_correcao";

/** Os status em que o grafo parou de vez.
 *
 * `sem_correcao` NAO esta aqui de proposito: o executor o define, mas a aresta
 * executor -> verificador roda em seguida e o verificador o sobrescreve com
 * "aplicado" (nodes.py:67). Ele so e observavel no meio do stream. */
export const STATUS_TERMINAIS: Status[] = ["quarentena", "rejeitado", "aplicado"];

export interface EstadoVenditus {
  termo: string;
  volume: number;
  perda_estimada: number;
  diagnostico: Diagnostico | null;
  decisao_guarda: DecisaoGuarda | null;
  devolucoes_consultadas: Devolucao[];
  fix_id: string | null;
  resultados_antes: number;
  resultados_depois: number;
  status: Status;
  escreveu: boolean;
}
```

- [ ] **Passo 2: Escrever `front/src/dados/espelho.ts`**

```ts
/** ESPELHO DECLARADO DO BACKEND.
 *
 * O `langgraph dev` expoe apenas a API do grafo — nao ha rota que sirva a fila,
 * o catalogo ou a formula da estimativa. Ver spec §1. Cada bloco abaixo aponta
 * para o arquivo-fonte. Se o back mudar, este arquivo muda junto. */

/** Fonte: back/src/venditus/estimate.py
 *  Premissas declaradas, nao medicoes — precisam aparecer na tela junto do R$. */
export const CONVERSAO_ASSUMIDA = 0.02;
export const TICKET_MEDIO_BRL = 564.96;

/** Fonte: back/src/venditus/estimate.py :: perda_estimada
 *
 * O front PRECISA calcular isto: `aprovacao` le state["perda_estimada"]
 * (graph.py:40) e quem preenche o campo e estado_inicial(), que nao passa por
 * HTTP. Sem enviar, o run quebra com KeyError no no da pausa. */
export function perdaEstimada(volume: number): number {
  return Math.round(volume * CONVERSAO_ASSUMIDA * TICKET_MEDIO_BRL * 100) / 100;
}

/** Fonte: back/src/venditus/seed.py :: BUSCAS */
export interface BuscaFalha {
  termo: string;
  volume: number;
}

export const BUSCAS: BuscaFalha[] = [
  { termo: "tênis impermeável", volume: 340 },
  { termo: "capa de chuva impermeável", volume: 128 },
  { termo: "mochila cargueira 80 litros", volume: 64 },
];

/** Fonte: back/src/venditus/seed.py :: CATALOGO — apenas os titulos.
 *  O estado carrega correcao.sku, nunca o titulo. Ver spec §1, lacuna 4. */
export const TITULOS: Record<string, string> = {
  "SKU-4471": "Tênis Trilha Alpha",
  "SKU-8802": "Capa de Chuva Leve Nimbus",
  "SKU-1100": "Meia Térmica Merino",
  "SKU-1201": "Mochila Cargueira 60L",
  "SKU-1305": "Lanterna de Cabeça Lumen",
};

/** Fonte: back/src/venditus/adapters/fake.py :: VALORES_VERDADEIROS */
export const VALORES_VERDADEIROS = new Set(["true", "sim", "1", "verdadeiro"]);
```

- [ ] **Passo 3: Verificar que compila**

```bash
cd front && npx tsc --noEmit
```

Esperado: nenhuma saída.

- [ ] **Passo 4: Commit**

```bash
git add front/src/dados/
git commit -m "Contrato do estado e o espelho declarado do backend"
```

---

### Task 3: `formato.ts` — moeda, dias e a frase da correção

**Arquivos:**
- Criar: `front/src/logica/formato.ts`, `front/src/logica/formato.test.ts`
- Modificar: `front/package.json`

- [ ] **Passo 1: Adicionar o script de teste ao `front/package.json`**

Dentro de `"scripts"`, acrescente:

```json
"test": "vitest run"
```

- [ ] **Passo 2: Escrever o teste que falha**

`front/src/logica/formato.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { campoAcentuado, dias, fraseDaCorrecao, moeda } from "./formato";

/** pt-BR usa espaco NAO-QUEBRAVEL (U+00A0) depois do "R$". Comparar com espaco
 *  comum falha de um jeito que consome vinte minutos para achar. */
const semNbsp = (t: string) => t.replace(/ /g, " ");

describe("moeda", () => {
  it("formata em real brasileiro", () => {
    expect(semNbsp(moeda(3841.73))).toBe("R$ 3.841,73");
  });

  it("mantem duas casas em valor redondo", () => {
    expect(semNbsp(moeda(723.1))).toBe("R$ 723,10");
  });
});

describe("dias", () => {
  it("usa singular em 1", () => {
    expect(dias(1)).toBe("1 dia");
  });

  it("usa plural nos demais", () => {
    expect(dias(14)).toBe("14 dias");
  });
});

describe("campoAcentuado", () => {
  it("devolve a palavra acentuada que o cliente buscou", () => {
    expect(campoAcentuado("impermeavel", "tênis impermeável")).toBe("impermeável");
  });

  it("devolve o campo cru quando nenhum token casa", () => {
    expect(campoAcentuado("voltagem", "air fryer 220v")).toBe("voltagem");
  });
});

describe("fraseDaCorrecao", () => {
  it("vira 'Marcar X como Y' quando o valor e verdadeiro", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-4471", campo: "impermeavel", valor: "true" },
      "tênis impermeável"
    );
    expect(frase).toBe("Marcar “Tênis Trilha Alpha” como impermeável no catálogo");
  });

  it("vira 'Definir campo como valor' nos demais valores", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-1201", campo: "litragem", valor: "80" },
      "mochila cargueira 80 litros"
    );
    expect(frase).toBe("Definir litragem de “Mochila Cargueira 60L” como 80");
  });

  it("cai no SKU quando o titulo nao esta no espelho", () => {
    const frase = fraseDaCorrecao(
      { sku: "SKU-9999", campo: "impermeavel", valor: "true" },
      "tênis impermeável"
    );
    expect(frase).toBe("Marcar “SKU-9999” como impermeável no catálogo");
  });
});
```

- [ ] **Passo 3: Rodar o teste para confirmar que falha**

```bash
cd front && npm test
```

Esperado: FALHA com `Failed to resolve import "./formato"`.

- [ ] **Passo 4: Escrever `front/src/logica/formato.ts`**

```ts
import type { CorrecaoProposta } from "../dados/contrato";
import { TITULOS, VALORES_VERDADEIROS } from "../dados/espelho";

export function moeda(valor: number): string {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function dias(quantidade: number): string {
  return quantidade === 1 ? "1 dia" : `${quantidade} dias`;
}

/** Espelha adapters/fake.py :: normalizar — minusculas sem acento. */
function normalizar(texto: string): string {
  return texto
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, ""); // acentos combinantes
}

/** Devolve a palavra do cliente, COM acento.
 *
 * O prompt do investigador exige que o nome do campo seja "a propria palavra
 * que o cliente buscou", em minusculas e sem acento (nodes.py:96). Entao o
 * termo no estado carrega a versao acentuada da mesma palavra. Nada e
 * inventado aqui: e o dado que ja chegou. */
export function campoAcentuado(campo: string, termo: string): string {
  const token = termo.split(/\s+/).find((t) => normalizar(t) === campo);
  return token ?? campo;
}

/** A correcao em linguagem de gente.
 *
 * Exibir o par `campo = valor` cru faz o leitor processar chave-valor em vez
 * de ler a frase. O par continua na tela, em mono cinza, logo abaixo. */
export function fraseDaCorrecao(correcao: CorrecaoProposta, termo: string): string {
  const titulo = TITULOS[correcao.sku] ?? correcao.sku;
  if (VALORES_VERDADEIROS.has(correcao.valor.toLowerCase())) {
    return `Marcar “${titulo}” como ${campoAcentuado(correcao.campo, termo)} no catálogo`;
  }
  return `Definir ${correcao.campo} de “${titulo}” como ${correcao.valor}`;
}
```

- [ ] **Passo 5: Rodar o teste para confirmar que passa**

```bash
cd front && npm test
```

Esperado: `9 passed`.

- [ ] **Passo 6: Commit**

```bash
git add front/src/logica/formato.ts front/src/logica/formato.test.ts front/package.json
git commit -m "Formatacao: moeda, dias e a correcao virando frase em portugues"
```

---

### Task 4: `passos.ts` — a linha do tempo

**Arquivos:**
- Criar: `front/src/logica/passos.ts`, `front/src/logica/passos.test.ts`

- [ ] **Passo 1: Escrever o teste que falha**

`front/src/logica/passos.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { derivarPassos } from "./passos";

const estados = (status: Parameters<typeof derivarPassos>[0]) =>
  derivarPassos(status).map((p) => p.estado);

describe("derivarPassos", () => {
  it("devolve sempre os seis passos, na ordem do grafo", () => {
    const nos = derivarPassos("novo").map((p) => p.no);
    expect(nos).toEqual([
      "ingest",
      "investigador",
      "guarda",
      "aprovacao",
      "executor",
      "verificador",
    ]);
  });

  it("traduz cada no para um rotulo em portugues", () => {
    const rotulos = derivarPassos("novo").map((p) => p.rotulo);
    expect(rotulos).toEqual([
      "Mede a busca",
      "Investiga a causa",
      "Audita as devoluções",
      "Sua aprovação",
      "Grava no catálogo",
      "Refaz a busca",
    ]);
  });

  it("sem estado ainda, deixa o primeiro passo ativo", () => {
    expect(estados(undefined)).toEqual([
      "ativo", "pendente", "pendente", "pendente", "pendente", "pendente",
    ]);
  });

  it("em diagnosticando, o ingest concluiu e o investigador roda", () => {
    expect(estados("diagnosticando")).toEqual([
      "concluido", "ativo", "pendente", "pendente", "pendente", "pendente",
    ]);
  });

  it("em diagnosticado, o guarda roda", () => {
    expect(estados("diagnosticado")).toEqual([
      "concluido", "concluido", "ativo", "pendente", "pendente", "pendente",
    ]);
  });

  it("bloqueado: o guarda fica em bloqueado e o resto vira inalcancavel", () => {
    expect(estados("bloqueado_pelo_guarda")).toEqual([
      "concluido", "concluido", "bloqueado",
      "inalcancavel", "inalcancavel", "inalcancavel",
    ]);
  });

  it("quarentena tem a mesma forma do bloqueio — e o fim dele", () => {
    expect(estados("quarentena")).toEqual(estados("bloqueado_pelo_guarda"));
  });

  it("aprovado_pelo_guarda deixa a aprovacao ativa, esperando o humano", () => {
    expect(estados("aprovado_pelo_guarda")).toEqual([
      "concluido", "concluido", "concluido", "ativo", "pendente", "pendente",
    ]);
  });

  it("aprovado poe o executor para rodar", () => {
    expect(estados("aprovado")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "ativo", "pendente",
    ]);
  });

  it("rejeitado encerra na aprovacao: escrita e verificacao ficam inalcancaveis", () => {
    expect(estados("rejeitado")).toEqual([
      "concluido", "concluido", "concluido", "concluido",
      "inalcancavel", "inalcancavel",
    ]);
  });

  it("sem_correcao e transitorio: o executor passou, o verificador roda", () => {
    expect(estados("sem_correcao")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "concluido", "ativo",
    ]);
  });

  it("aplicado conclui os seis", () => {
    expect(estados("aplicado")).toEqual([
      "concluido", "concluido", "concluido", "concluido", "concluido", "concluido",
    ]);
  });
});
```

- [ ] **Passo 2: Rodar o teste para confirmar que falha**

```bash
cd front && npm test
```

Esperado: FALHA com `Failed to resolve import "./passos"`.

- [ ] **Passo 3: Escrever `front/src/logica/passos.ts`**

```ts
import type { Status } from "../dados/contrato";

export type EstadoPasso =
  | "pendente"
  | "ativo"
  | "concluido"
  | "bloqueado"
  | "inalcancavel";

export interface Passo {
  /** Nome do no no grafo — exibido em mono, pequeno. */
  no: string;
  /** O que o no faz, em portugues — exibido grande. */
  rotulo: string;
  estado: EstadoPasso;
}

/** Seis passos, nao sete.
 *
 * `quarentena` nao e etapa do caminho, e o fim dele: aparece como rotulo de
 * status no rodape do bloco de recusa. Como setimo passo, sugeriria um caminho
 * que passa por ela e continua. */
const CAMINHO = [
  { no: "ingest", rotulo: "Mede a busca" },
  { no: "investigador", rotulo: "Investiga a causa" },
  { no: "guarda", rotulo: "Audita as devoluções" },
  { no: "aprovacao", rotulo: "Sua aprovação" },
  { no: "executor", rotulo: "Grava no catálogo" },
  { no: "verificador", rotulo: "Refaz a busca" },
] as const;

/** Quantos passos ja concluiram, e qual e o corrente, para cada status. */
const MAPA: Record<Status, { concluidos: number; corrente: EstadoPasso | null }> = {
  novo: { concluidos: 0, corrente: "ativo" },
  diagnosticando: { concluidos: 1, corrente: "ativo" },
  diagnosticado: { concluidos: 2, corrente: "ativo" },
  bloqueado_pelo_guarda: { concluidos: 2, corrente: "bloqueado" },
  quarentena: { concluidos: 2, corrente: "bloqueado" },
  aprovado_pelo_guarda: { concluidos: 3, corrente: "ativo" },
  aprovado: { concluidos: 4, corrente: "ativo" },
  rejeitado: { concluidos: 4, corrente: null },
  sem_correcao: { concluidos: 5, corrente: "ativo" },
  aplicado: { concluidos: 6, corrente: null },
};

/** O status do estado vira o desenho da linha do tempo.
 *
 * Quando o guarda bloqueia, os passos seguintes viram `inalcancavel` — nao
 * `pendente`. E a tese do produto virando pixel: o caminho ate a escrita
 * deixa de existir. */
export function derivarPassos(status: Status | undefined): Passo[] {
  const { concluidos, corrente } = MAPA[status ?? "novo"];
  const interrompido = corrente === "bloqueado" || status === "rejeitado";

  return CAMINHO.map((passo, indice) => {
    let estado: EstadoPasso;
    if (indice < concluidos) {
      estado = "concluido";
    } else if (indice === concluidos && corrente !== null) {
      estado = corrente;
    } else {
      estado = interrompido ? "inalcancavel" : "pendente";
    }
    return { ...passo, estado };
  });
}
```

- [ ] **Passo 4: Rodar o teste para confirmar que passa**

```bash
cd front && npm test
```

Esperado: `21 passed` (9 da Task 3 + 12 desta).

- [ ] **Passo 5: Commit**

```bash
git add front/src/logica/passos.ts front/src/logica/passos.test.ts
git commit -m "Linha do tempo: o status do grafo virando seis passos em portugues"
```

---

### Task 5: `indicadores.ts` — o espelho do `metrics.py`

**Arquivos:**
- Criar: `front/src/logica/indicadores.ts`, `front/src/logica/indicadores.test.ts`

- [ ] **Passo 1: Escrever o teste que falha**

`front/src/logica/indicadores.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import type { EstadoVenditus } from "../dados/contrato";
import { indicadores } from "./indicadores";

function estado(parcial: Partial<EstadoVenditus>): EstadoVenditus {
  return {
    termo: "termo",
    volume: 100,
    perda_estimada: 1129.92,
    diagnostico: null,
    decisao_guarda: null,
    devolucoes_consultadas: [],
    fix_id: null,
    resultados_antes: 0,
    resultados_depois: 0,
    status: "aplicado",
    escreveu: false,
    ...parcial,
  };
}

describe("indicadores", () => {
  it("sem execucoes, zera tudo e nao divide por zero", () => {
    const r = indicadores([]);
    expect(r.execucoes).toBe(0);
    expect(r.taxaDeBloqueio).toBe(0);
    expect(r.receitaRecuperada).toBe(0);
    expect(r.resultadosAntes).toBeNull();
  });

  it("soma a perda estimada apenas das execucoes que escreveram", () => {
    const r = indicadores([
      estado({ perda_estimada: 3841.73, escreveu: true }),
      estado({ perda_estimada: 1446.3, escreveu: false, status: "quarentena" }),
    ]);
    expect(r.receitaRecuperada).toBe(3841.73);
  });

  it("ARMADILHA: status 'aplicado' com escreveu=false NAO conta receita", () => {
    // E o caminho sem_correcao: o executor devolve status="sem_correcao" e
    // escreveu=false (nodes.py:46), mas o verificador roda em seguida e
    // sobrescreve o status com "aplicado" (nodes.py:67). Quem decide e
    // escreveu, como metrics.py:38 ja faz.
    const r = indicadores([
      estado({ perda_estimada: 723.15, status: "aplicado", escreveu: false }),
    ]);
    expect(r.receitaRecuperada).toBe(0);
    expect(r.execucoes).toBe(1);
  });

  it("conta bloqueados pelo status quarentena", () => {
    const r = indicadores([
      estado({ status: "quarentena" }),
      estado({ status: "aplicado", escreveu: true }),
    ]);
    expect(r.bloqueados).toBe(1);
    expect(r.taxaDeBloqueio).toBe(0.5);
  });

  it("bloqueado_pelo_guarda NAO conta — o terminal e quarentena", () => {
    // metrics.py:11 fixa STATUS_BLOQUEADO = "quarentena".
    const r = indicadores([estado({ status: "bloqueado_pelo_guarda" })]);
    expect(r.bloqueados).toBe(0);
  });

  it("o antes/depois vem da ultima execucao que escreveu", () => {
    const r = indicadores([
      estado({ escreveu: true, resultados_antes: 0, resultados_depois: 1 }),
      estado({ status: "quarentena", resultados_antes: 0, resultados_depois: 0 }),
    ]);
    expect(r.resultadosAntes).toBe(0);
    expect(r.resultadosDepois).toBe(1);
  });

  it("arredonda a receita em duas casas, como receita_recuperada", () => {
    const r = indicadores([
      estado({ perda_estimada: 3841.73, escreveu: true }),
      estado({ perda_estimada: 723.15, escreveu: true }),
    ]);
    expect(r.receitaRecuperada).toBe(4564.88);
  });
});
```

- [ ] **Passo 2: Rodar o teste para confirmar que falha**

```bash
cd front && npm test
```

Esperado: FALHA com `Failed to resolve import "./indicadores"`.

- [ ] **Passo 3: Escrever `front/src/logica/indicadores.ts`**

```ts
import type { EstadoVenditus } from "../dados/contrato";

/** Fonte: back/src/venditus/metrics.py:11 */
const STATUS_BLOQUEADO = "quarentena";

export interface Indicadores {
  receitaRecuperada: number;
  bloqueados: number;
  execucoes: number;
  taxaDeBloqueio: number;
  /** Da ultima execucao que escreveu; null enquanto nenhuma escreveu. */
  resultadosAntes: number | null;
  resultadosDepois: number | null;
}

/** Espelho de metrics.py :: resumo_kpis, com a mesma assinatura.
 *
 * `cobertura_de_atributo` fica de fora: exige catalogo.listar_produtos(), que
 * o backend nao serve. Ver spec §2, decisao D2. No lugar dela vai o
 * antes/depois da busca, que ja vem no estado. */
export function indicadores(estados: EstadoVenditus[]): Indicadores {
  const escritos = estados.filter((e) => e.escreveu);
  const bloqueados = estados.filter((e) => e.status === STATUS_BLOQUEADO).length;
  const ultimoEscrito = escritos.at(-1) ?? null;

  const soma = escritos.reduce((total, e) => total + (e.perda_estimada ?? 0), 0);

  return {
    receitaRecuperada: Math.round(soma * 100) / 100,
    bloqueados,
    execucoes: estados.length,
    taxaDeBloqueio: estados.length === 0 ? 0 : bloqueados / estados.length,
    resultadosAntes: ultimoEscrito?.resultados_antes ?? null,
    resultadosDepois: ultimoEscrito?.resultados_depois ?? null,
  };
}
```

- [ ] **Passo 4: Rodar o teste para confirmar que passa**

```bash
cd front && npm test
```

Esperado: `28 passed`.

- [ ] **Passo 5: Commit**

```bash
git add front/src/logica/indicadores.ts front/src/logica/indicadores.test.ts
git commit -m "Indicadores espelhando metrics.py, com a regra do escreveu travada em teste"
```

---

### Task 6: `usarExecucao.ts` — o gancho do stream

**Arquivos:**
- Criar: `front/src/ganchos/usarExecucao.ts`

> Se a Task 1 revelou nomes diferentes no `useStream`, ajuste este arquivo de acordo antes de escrevê-lo.

- [ ] **Passo 1: Escrever o gancho**

```ts
import { useEffect, useRef, useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";
import type { EstadoVenditus } from "../dados/contrato";
import { STATUS_TERMINAIS } from "../dados/contrato";
import { perdaEstimada } from "../dados/espelho";

export function usarExecucao(aoEncerrar: (estado: EstadoVenditus) => void) {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [termoAtual, setTermoAtual] = useState<string | null>(null);
  const [segundos, setSegundos] = useState(0);
  const jaEncerrou = useRef(false);

  const fluxo = useStream<EstadoVenditus>({
    apiUrl: "/api",
    assistantId: "venditus",
    threadId,
    onThreadId: setThreadId,
  });

  const estado = fluxo.values;
  const terminou =
    estado?.status !== undefined &&
    STATUS_TERMINAIS.includes(estado.status) &&
    !fluxo.isLoading;

  /** Empurra o estado final para a lista de execucoes, uma unica vez. */
  useEffect(() => {
    if (terminou && !jaEncerrou.current && estado) {
      jaEncerrou.current = true;
      aoEncerrar(estado);
    }
  }, [terminou, estado, aoEncerrar]);

  /** Contador de segundos do passo ativo.
   *  Sem ele, os 15-40s de LLM parecem travamento no video. */
  useEffect(() => {
    if (!fluxo.isLoading) return;
    const inicio = Date.now();
    const relogio = setInterval(
      () => setSegundos(Math.floor((Date.now() - inicio) / 1000)),
      1000
    );
    return () => clearInterval(relogio);
  }, [fluxo.isLoading, estado?.status]);

  function iniciar(termo: string, volume: number) {
    jaEncerrou.current = false;
    setSegundos(0);
    setThreadId(null);
    setTermoAtual(termo);
    fluxo.submit({ termo, volume, perda_estimada: perdaEstimada(volume) });
  }

  function responder(aprovado: boolean) {
    setSegundos(0);
    fluxo.submit(undefined, { command: { resume: { aprovado } } });
  }

  return { fluxo, estado, iniciar, responder, termoAtual, segundos, terminou };
}
```

- [ ] **Passo 2: Verificar que compila**

```bash
cd front && npx tsc --noEmit
```

Esperado: nenhuma saída. Se o TypeScript reclamar do formato de `submit` ou de `command`, **volte à Task 1** e confira a assinatura real — não force com `as any`.

- [ ] **Passo 3: Commit**

```bash
git add front/src/ganchos/
git commit -m "Gancho da execucao: um useStream por caso, com o relogio do passo ativo"
```

---

### Task 7: Moldura — cabeçalho, indicadores, lista e estado vazio

**Arquivos:**
- Criar: `front/src/componentes/Cabecalho.tsx`, `FaixaDeIndicadores.tsx`, `ListaDeBuscas.tsx`, `EstadoVazio.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: `front/src/componentes/Cabecalho.tsx`**

```tsx
export function Cabecalho({ children }: { children: React.ReactNode }) {
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
```

- [ ] **Passo 2: `front/src/componentes/FaixaDeIndicadores.tsx`**

```tsx
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
      className={`min-w-[112px] rounded-lg border px-3 py-1.5 text-right ${
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
          HANDOFF §4 pede: e a metrica que nenhum concorrente calcula. */}
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
```

- [ ] **Passo 3: `front/src/componentes/ListaDeBuscas.tsx`**

```tsx
import type { EstadoVenditus } from "../dados/contrato";
import { BUSCAS, CONVERSAO_ASSUMIDA, TICKET_MEDIO_BRL, perdaEstimada } from "../dados/espelho";
import { moeda } from "../logica/formato";

/** O desfecho de um termo ja executado, para o selo na lista. */
function selo(estado: EstadoVenditus | undefined) {
  if (!estado) return null;
  if (estado.status === "quarentena")
    return <span className="text-perigo">recusado</span>;
  if (estado.escreveu)
    return (
      <span className="text-sucesso">
        gravado · {estado.resultados_antes} → {estado.resultados_depois}
      </span>
    );
  if (estado.status === "rejeitado")
    return <span className="text-texto-fraco">rejeitado por você</span>;
  return <span className="text-texto-fraco">sem correção</span>;
}

export function ListaDeBuscas({
  encerradas,
  termoAtual,
  ocupado,
  aoEscolher,
}: {
  encerradas: Record<string, EstadoVenditus>;
  termoAtual: string | null;
  ocupado: boolean;
  aoEscolher: (termo: string, volume: number) => void;
}) {
  const ordenadas = [...BUSCAS].sort(
    (a, b) => perdaEstimada(b.volume) - perdaEstimada(a.volume)
  );

  return (
    <nav className="w-56 shrink-0 border-r border-borda p-2.5">
      <div className="px-1.5 pb-2 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        Buscas sem resultado
      </div>

      {ordenadas.map((busca) => {
        const encerrada = encerradas[busca.termo];
        const ativa = termoAtual === busca.termo;
        return (
          <button
            key={busca.termo}
            type="button"
            disabled={ocupado}
            onClick={() => aoEscolher(busca.termo, busca.volume)}
            className={`mb-1 block w-full min-h-11 rounded-md border-l-[3px] px-2 py-2 text-left transition-colors duration-200 focus-visible:outline-2 focus-visible:outline-gold disabled:opacity-50 disabled:cursor-not-allowed ${
              ativa
                ? "border-l-gold bg-[#17130A]"
                : "border-l-transparent hover:bg-secundario cursor-pointer"
            }`}
          >
            <div className="text-[12.5px] font-semibold">{busca.termo}</div>
            <div className="mt-0.5 flex justify-between gap-2 text-[10.5px] tabular-nums text-texto-fraco">
              <span>{selo(encerrada) ?? `${busca.volume} buscas/mês`}</span>
              <span>{moeda(perdaEstimada(busca.volume))}</span>
            </div>
          </button>
        );
      })}

      {/* O HANDOFF §4 exige a formula na tela sempre que o R$ aparecer. */}
      <p className="mt-3 border-t border-borda px-1.5 pt-2 text-[10.5px] leading-relaxed text-[#737373]">
        estimativa · volume × {CONVERSAO_ASSUMIDA * 100}% de conversão ×{" "}
        {moeda(TICKET_MEDIO_BRL)} de ticket médio (ABComm 2026)
      </p>
    </nav>
  );
}
```

- [ ] **Passo 4: `front/src/componentes/EstadoVazio.tsx`**

```tsx
export function EstadoVazio() {
  return (
    <div className="flex min-h-56 flex-col items-center justify-center gap-1.5 text-center">
      <p className="text-sm font-semibold">Escolha uma busca à esquerda.</p>
      <p className="text-xs text-texto-fraco">
        O Venditus lê a busca que falhou, investiga a causa no catálogo e audita
        as devoluções antes de propor qualquer escrita.
      </p>
    </div>
  );
}
```

- [ ] **Passo 5: Montar `front/src/App.tsx` com a forma B**

```tsx
import { useCallback, useMemo, useState } from "react";
import type { EstadoVenditus } from "./dados/contrato";
import { usarExecucao } from "./ganchos/usarExecucao";
import { indicadores } from "./logica/indicadores";
import { Cabecalho } from "./componentes/Cabecalho";
import { FaixaDeIndicadores } from "./componentes/FaixaDeIndicadores";
import { ListaDeBuscas } from "./componentes/ListaDeBuscas";
import { EstadoVazio } from "./componentes/EstadoVazio";

export default function App() {
  const [encerradas, setEncerradas] = useState<Record<string, EstadoVenditus>>({});

  const aoEncerrar = useCallback((estado: EstadoVenditus) => {
    setEncerradas((atuais) => ({ ...atuais, [estado.termo]: estado }));
  }, []);

  const execucao = usarExecucao(aoEncerrar);
  const dados = useMemo(() => indicadores(Object.values(encerradas)), [encerradas]);

  return (
    <div className="min-h-dvh">
      <Cabecalho>
        <FaixaDeIndicadores dados={dados} />
      </Cabecalho>

      <div className="flex">
        <ListaDeBuscas
          encerradas={encerradas}
          termoAtual={execucao.termoAtual}
          ocupado={execucao.fluxo.isLoading}
          aoEscolher={execucao.iniciar}
        />
        <main className="flex-1 p-4">
          {execucao.termoAtual === null ? <EstadoVazio /> : null}
        </main>
      </div>
    </div>
  );
}
```

- [ ] **Passo 6: Verificar na tela**

Com backend e `npm run dev` no ar, abra `http://localhost:5173`.

Esperado: logo e marca no topo; três indicadores mostrando `—`; a lista com os três termos **ordenados por R$** (3.841,73 · 1.446,30 · 723,15) e a fórmula no rodapé; à direita, o estado vazio. Clicar num termo ainda não mostra nada no palco — é a Task 8.

- [ ] **Passo 7: Commit**

```bash
git add front/src/componentes/ front/src/App.tsx
git commit -m "Moldura da forma B: cabecalho, indicadores, lista de buscas e estado vazio"
```

---

### Task 8: `LinhaDoTempo`

**Arquivos:**
- Criar: `front/src/componentes/LinhaDoTempo.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: Escrever o componente**

```tsx
import type { Status } from "../dados/contrato";
import { derivarPassos, type EstadoPasso } from "../logica/passos";

const CAIXA: Record<EstadoPasso, string> = {
  pendente: "bg-cartao border-borda",
  ativo: "bg-[#211B0C] border-gold",
  concluido: "bg-[#17130A] border-gold-fraco",
  bloqueado: "bg-[#1E0E0E] border-perigo",
  inalcancavel: "bg-cartao border-borda opacity-30",
};

const ROTULO: Record<EstadoPasso, string> = {
  pendente: "text-[#D4D4D4]",
  ativo: "text-gold-claro",
  concluido: "text-gold-claro",
  bloqueado: "text-[#FCA5A5]",
  inalcancavel: "text-[#D4D4D4] line-through",
};

export function LinhaDoTempo({
  status,
  segundos,
}: {
  status: Status | undefined;
  segundos: number;
}) {
  const passos = derivarPassos(status);

  return (
    <ol className="mb-4 flex gap-1">
      {passos.map((passo) => (
        <li
          key={passo.no}
          className={`flex-1 rounded-md border px-2 py-1.5 transition-all duration-200 motion-reduce:transition-none ${CAIXA[passo.estado]}`}
          aria-current={passo.estado === "ativo" ? "step" : undefined}
        >
          <span className={`block text-[11px] font-semibold leading-tight ${ROTULO[passo.estado]}`}>
            {passo.rotulo}
          </span>
          <span className="mt-0.5 block font-mono text-[8.5px] text-[#5C5C5C]">
            {/* O relogio so no passo ativo: sem ele, 15-40s de LLM parecem
                travamento. Com ele, parecem raciocinio. */}
            {passo.estado === "ativo" && segundos > 0
              ? `${passo.no} · ${segundos}s`
              : passo.no}
          </span>
        </li>
      ))}
    </ol>
  );
}
```

- [ ] **Passo 2: Ligar no `App.tsx`**

Importe e troque o conteúdo de `<main>`:

```tsx
import { LinhaDoTempo } from "./componentes/LinhaDoTempo";
```

```tsx
        <main className="flex-1 p-4">
          {execucao.termoAtual === null ? (
            <EstadoVazio />
          ) : (
            <LinhaDoTempo
              status={execucao.estado?.status}
              segundos={execucao.segundos}
            />
          )}
        </main>
```

- [ ] **Passo 3: Verificar ao vivo**

Clique em **"tênis impermeável"**. Esperado: os passos acendem em dourado da esquerda para a direita, com os segundos correndo no passo ativo, até parar em **"Sua aprovação"**.

Clique em **"capa de chuva impermeável"**. Esperado: ao chegar em "Audita as devoluções", o passo fica **vermelho** e os três seguintes ficam **riscados e apagados**.

- [ ] **Passo 4: Commit**

```bash
git add front/src/componentes/LinhaDoTempo.tsx front/src/App.tsx
git commit -m "Linha do tempo: os passos mortos riscados quando o guarda bloqueia"
```

---

### Task 9: `CartaoDeDiagnostico`

**Arquivos:**
- Criar: `front/src/componentes/CartaoDeDiagnostico.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: Escrever o componente**

```tsx
import type { Causa, Diagnostico } from "../dados/contrato";
import { TITULOS } from "../dados/espelho";
import { fraseDaCorrecao } from "../logica/formato";

const CAUSA_EM_PORTUGUES: Record<Causa, string> = {
  typo: "Erro de digitação na busca",
  sinonimo: "Sinônimo que o catálogo não usa",
  atributo_ausente: "Atributo faltando",
  categorizacao_errada: "Categoria errada",
  sem_estoque: "Produto sem estoque",
  sem_sortimento: "A loja não vende isso",
};

export function CartaoDeDiagnostico({
  diagnostico,
  termo,
}: {
  diagnostico: Diagnostico;
  termo: string;
}) {
  const correcao = diagnostico.correcao;

  return (
    <section className="mb-3 rounded-lg border border-borda bg-cartao p-3.5">
      <h2 className="flex items-center gap-2 text-sm font-bold">
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="size-4 shrink-0 stroke-gold stroke-2 fill-none [stroke-linecap:round]"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        {CAUSA_EM_PORTUGUES[diagnostico.causa]}
        <span className="rounded border border-borda bg-secundario px-1.5 py-0.5 text-[9.5px] uppercase tracking-wider text-texto-fraco">
          confiança {diagnostico.confianca}
        </span>
      </h2>

      {correcao ? (
        <p className="mt-1 text-[11.5px] text-texto-fraco">
          {correcao.sku} · {TITULOS[correcao.sku] ?? "produto fora do espelho"}
        </p>
      ) : null}

      <h3 className="mt-3 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        o que o catálogo diz hoje
      </h3>
      <blockquote className="border-l-2 border-[#333] pl-3 text-[12.5px] italic text-[#D4D4D4]">
        “{diagnostico.evidencia}”
      </blockquote>

      {correcao ? (
        <>
          <h3 className="mt-3.5 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
            a correção proposta
          </h3>
          {/* Duas camadas: a frase em portugues manda, o par campo=valor fica
              embaixo como prova. Mesmo padrao dos nomes dos nos. */}
          <div className="rounded-lg border-l-[3px] border-gold-escuro bg-[#191919] px-3 py-2.5">
            <p className="text-[15px] font-semibold leading-snug">
              {fraseDaCorrecao(correcao, termo)}
            </p>
            <p className="mt-1.5 font-mono text-[10.5px] text-[#6B6B6B]">
              atributo {correcao.campo} = "{correcao.valor}" · {correcao.sku}
            </p>
          </div>
        </>
      ) : (
        <p className="mt-3.5 text-[13px]">
          Nenhuma correção de catálogo se aplica — o problema não está no texto
          do produto.
        </p>
      )}
    </section>
  );
}
```

- [ ] **Passo 2: Ligar no `App.tsx`**

```tsx
import { CartaoDeDiagnostico } from "./componentes/CartaoDeDiagnostico";
```

Dentro de `<main>`, logo depois da `<LinhaDoTempo>`:

```tsx
              {execucao.estado?.diagnostico ? (
                <CartaoDeDiagnostico
                  diagnostico={execucao.estado.diagnostico}
                  termo={execucao.estado.termo}
                />
              ) : null}
```

- [ ] **Passo 3: Verificar ao vivo**

Rode "tênis impermeável". Esperado, depois do investigador: **"Atributo faltando"** com o selo "confiança alta", a linha `SKU-4471 · Tênis Trilha Alpha`, a evidência citada do catálogo, e a frase **"Marcar “Tênis Trilha Alpha” como impermeável no catálogo"** com `atributo impermeavel = "true" · SKU-4471` em mono cinza embaixo.

- [ ] **Passo 4: Commit**

```bash
git add front/src/componentes/CartaoDeDiagnostico.tsx front/src/App.tsx
git commit -m "Cartao de diagnostico com a correcao em duas camadas"
```

---

### Task 10: `BarraDeAprovacao`

**Arquivos:**
- Criar: `front/src/componentes/BarraDeAprovacao.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: Escrever o componente**

```tsx
import type { EstadoVenditus } from "../dados/contrato";
import { CONVERSAO_ASSUMIDA, TICKET_MEDIO_BRL } from "../dados/espelho";
import { fraseDaCorrecao, moeda } from "../logica/formato";

export function BarraDeAprovacao({
  estado,
  ocupado,
  aoResponder,
}: {
  estado: EstadoVenditus;
  ocupado: boolean;
  aoResponder: (aprovado: boolean) => void;
}) {
  const correcao = estado.diagnostico?.correcao ?? null;
  const guarda = estado.decisao_guarda;

  return (
    <section className="mb-3 rounded-lg border border-gold-escuro bg-cartao p-3.5">
      <h2 className="flex items-center gap-2 text-sm font-bold">
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="size-4 shrink-0 stroke-gold-claro stroke-2 fill-none [stroke-linecap:round] [stroke-linejoin:round]"
        >
          <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
        Liberado pelo pós-venda
      </h2>

      <p className="mt-1 text-[11.5px] text-texto-fraco">
        {guarda?.justificativa}
      </p>

      {correcao ? (
        <div className="mt-3 rounded-lg border-l-[3px] border-gold-escuro bg-[#191919] px-3 py-2.5">
          <p className="text-[15px] font-semibold leading-snug">
            {fraseDaCorrecao(correcao, estado.termo)}
          </p>
          <p className="mt-1.5 font-mono text-[10.5px] text-[#6B6B6B]">
            atributo {correcao.campo} = "{correcao.valor}" · {correcao.sku}
          </p>
        </div>
      ) : null}

      {/* O dinheiro pesa mais que os botoes: a decisao e sobre ele. */}
      <p className="mt-3.5 flex items-end gap-3">
        <span className="text-[34px] font-extrabold leading-none tracking-tight text-gold-claro tabular-nums">
          {moeda(estado.perda_estimada)}
        </span>
        <span className="pb-0.5 text-[15px] font-semibold text-texto-fraco">/ mês</span>
      </p>
      <p className="mt-1.5 text-xs text-[#D4D4D4]">
        é o que essa busca deixa de vender enquanto não acha nada.
      </p>
      <p className="mt-0.5 text-[10.5px] text-[#6B6B6B]">
        estimativa · {estado.volume} buscas × {CONVERSAO_ASSUMIDA * 100}% de conversão ×{" "}
        {moeda(TICKET_MEDIO_BRL)} de ticket médio (ABComm 2026)
      </p>

      <div className="mt-4 flex gap-2.5 border-t border-borda pt-3.5">
        <button
          type="button"
          disabled={ocupado}
          onClick={() => aoResponder(true)}
          className="min-h-11 cursor-pointer rounded-lg bg-gold px-5 py-2.5 text-[13px] font-bold text-[#171717] shadow-[0_0_22px_rgba(217,165,32,0.25)] transition-opacity duration-200 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold-claro disabled:opacity-50"
        >
          {ocupado ? "Gravando…" : "Aprovar e gravar no catálogo"}
        </button>
        <button
          type="button"
          disabled={ocupado}
          onClick={() => aoResponder(false)}
          className="min-h-11 cursor-pointer rounded-lg border border-borda px-5 py-2.5 text-[13px] font-bold text-texto-fraco transition-colors duration-200 hover:bg-secundario focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:opacity-50"
        >
          Rejeitar
        </button>
      </div>
    </section>
  );
}
```

- [ ] **Passo 2: Ligar no `App.tsx`**

```tsx
import { BarraDeAprovacao } from "./componentes/BarraDeAprovacao";
```

Depois do `CartaoDeDiagnostico`:

```tsx
              {execucao.estado?.status === "aprovado_pelo_guarda" ? (
                <BarraDeAprovacao
                  estado={execucao.estado}
                  ocupado={execucao.fluxo.isLoading}
                  aoResponder={execucao.responder}
                />
              ) : null}
```

- [ ] **Passo 3: Verificar ao vivo**

Rode "tênis impermeável" até a pausa. Esperado: o cartão dourado com **R$ 3.841,73** em corpo grande, a fórmula embaixo, e os dois botões. Clique em **"Aprovar e gravar no catálogo"** — a linha do tempo deve seguir para "Grava no catálogo" e "Refaz a busca".

- [ ] **Passo 4: Commit**

```bash
git add front/src/componentes/BarraDeAprovacao.tsx front/src/App.tsx
git commit -m "Barra de aprovacao com o R$ em destaque acima dos botoes"
```

---

### Task 11: `BlocoDeRecusa` — o clímax

**Arquivos:**
- Criar: `front/src/componentes/BlocoDeRecusa.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: Escrever o componente**

```tsx
import type { EstadoVenditus } from "../dados/contrato";
import { dias } from "../logica/formato";

export function BlocoDeRecusa({ estado }: { estado: EstadoVenditus }) {
  const guarda = estado.decisao_guarda;
  const lidas = estado.devolucoes_consultadas ?? [];

  /* O backend NAO informa quais devolucoes contradizem, e esta certo em nao
     informar: fazer o LLM reescrever as frases lhe daria a chance de
     parafrasear o cliente (nodes.py:179). Entao a lista e rotulada pelo que
     ela e — o que o guarda leu — e o contador fica no titulo. Filtrar por
     palavra-chave aqui seria inventar uma inferencia que o backend nao fez. */
  const ordenadas = [...lidas].sort((a, b) => a.dias_atras - b.dias_atras);

  return (
    <section className="mb-3 rounded-lg border border-perigo bg-gradient-to-b from-[#1A0E0E] to-cartao p-3.5">
      <h2 className="flex items-center gap-2 text-sm font-bold text-[#FF6B6B]">
        <svg
          viewBox="0 0 24 24"
          aria-hidden="true"
          className="size-4 shrink-0 stroke-current stroke-2 fill-none [stroke-linecap:round]"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="m4.9 4.9 14.2 14.2" />
        </svg>
        {/* A palavra acompanha a cor: comunicar o bloqueio so pelo vermelho
            quebra a regra color-not-only. */}
        CORREÇÃO RECUSADA
      </h2>

      <p className="mt-1 text-[11.5px] text-texto-fraco">
        <strong className="text-[#FF9B9B]">
          {guarda?.devolucoes_contraditorias} das {lidas.length} devoluções contradizem
        </strong>{" "}
        o atributo que seria gravado.
      </p>

      <h3 className="pt-3 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
        as {lidas.length} devoluções que o guarda leu
      </h3>

      <ul className="my-2 max-h-56 overflow-y-auto">
        {ordenadas.map((devolucao, indice) => (
          <li
            key={`${devolucao.sku}-${devolucao.dias_atras}-${indice}`}
            className="my-1.5 flex items-baseline justify-between gap-3 border-l-2 border-[#7F1D1D] px-3 py-1"
          >
            {/* As frases sao o payload: maiores que o corpo do texto. */}
            <q className="text-[13px] italic text-[#F0F0F0]">{devolucao.motivo}</q>
            <span className="shrink-0 text-[10px] tabular-nums text-[#737373]">
              {dias(devolucao.dias_atras)}
            </span>
          </li>
        ))}
      </ul>

      <div className="rounded-md bg-[#191919] px-3 py-2.5">
        <h3 className="pb-1 text-[8.5px] uppercase tracking-[0.11em] text-texto-fraco">
          justificativa do guarda
        </h3>
        <p className="text-xs text-[#C4C4C4]">{guarda?.justificativa}</p>
      </div>

      <p className="mt-3 text-[13.5px] font-semibold">O catálogo continua como estava.</p>

      {/* O fato em destaque, o encaminhamento como narrativa declarada. A
          palavra "quarentena" sozinha prometeria uma acao que nao acontece. */}
      <p className="mt-2.5 border-t border-borda pt-2.5 text-[10.5px] text-[#737373]">
        O caso vira hipótese para o time de qualidade — o Venditus não abre
        chamado, ele para e mostra o porquê.{" "}
        <span className="font-mono text-[#5C5C5C]">status: {estado.status}</span>
      </p>
    </section>
  );
}
```

- [ ] **Passo 2: Ligar no `App.tsx`**

```tsx
import { BlocoDeRecusa } from "./componentes/BlocoDeRecusa";
```

Depois da `BarraDeAprovacao`:

```tsx
              {execucao.estado?.decisao_guarda?.permitir === false ? (
                <BlocoDeRecusa estado={execucao.estado} />
              ) : null}
```

- [ ] **Passo 3: Verificar ao vivo — este é o quadro do vídeo**

Rode **"capa de chuva impermeável"**. Esperado:

- Título vermelho com ícone SVG e a palavra **CORREÇÃO RECUSADA**
- **"8 das 11 devoluções contradizem"**
- **As onze frases**, a mais recente primeiro, começando por *"Chovi 10 minutos e fiquei todo molhado" · 5 dias*
- A justificativa do guarda
- **"O catálogo continua como estava."**
- O rodapé com `status: quarentena`

Se a lista vier vazia, `devolucoes_consultadas` não chegou — **volte à Task 1, passo 4.**

- [ ] **Passo 4: Commit**

```bash
git add front/src/componentes/BlocoDeRecusa.tsx front/src/App.tsx
git commit -m "Bloco de recusa: as frases do cliente, nao o contador"
```

---

### Task 12: `BlocoDeResultado` e `AvisoDeBackend`

**Arquivos:**
- Criar: `front/src/componentes/BlocoDeResultado.tsx`, `front/src/componentes/AvisoDeBackend.tsx`
- Modificar: `front/src/App.tsx`

- [ ] **Passo 1: `front/src/componentes/BlocoDeResultado.tsx`**

```tsx
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

  return (
    <section className="rounded-lg border border-gold-escuro bg-cartao p-3.5">
      <p className="text-xl font-bold">
        A busca achava{" "}
        <span className="tabular-nums text-texto-fraco">{estado.resultados_antes}</span>. Agora
        acha <span className="tabular-nums text-gold-claro">{estado.resultados_depois}</span>.
      </p>
      <p className="mt-2 font-mono text-[10.5px] text-[#6B6B6B]">
        fix_id {estado.fix_id} · determinístico, para o executor não gravar duas vezes
      </p>
    </section>
  );
}
```

- [ ] **Passo 2: `front/src/componentes/AvisoDeBackend.tsx`**

```tsx
import { useEffect, useState } from "react";

const COMANDO = "cd back && .venv\\Scripts\\langgraph dev --no-browser --port 2024";
const RESET = "cd back && .venv\\Scripts\\python scripts/verificar_shopify.py --resetar";

export function AvisoDeBackend({ jaCorrigido }: { jaCorrigido: boolean }) {
  const [noAr, setNoAr] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/ok")
      .then((r) => setNoAr(r.ok))
      .catch(() => setNoAr(false));
  }, []);

  if (noAr === false) {
    return (
      <div role="alert" className="border-b border-perigo bg-[#1E0E0E] px-5 py-2">
        <p className="text-xs font-semibold text-[#FF6B6B]">
          O backend não responde em 127.0.0.1:2024.
        </p>
        <code className="mt-1 block font-mono text-[10.5px] text-texto-fraco">{COMANDO}</code>
      </div>
    );
  }

  if (jaCorrigido) {
    return (
      <div role="status" className="border-b border-gold-escuro bg-[#17130A] px-5 py-2">
        <p className="text-xs font-semibold text-gold-claro">
          Esta correção já está aplicada na loja — a busca já achava o produto antes de rodar.
        </p>
        <code className="mt-1 block font-mono text-[10.5px] text-texto-fraco">{RESET}</code>
      </div>
    );
  }

  return null;
}
```

- [ ] **Passo 3: Ligar os dois no `App.tsx`**

```tsx
import { BlocoDeResultado } from "./componentes/BlocoDeResultado";
import { AvisoDeBackend } from "./componentes/AvisoDeBackend";
```

Logo abaixo do `</Cabecalho>`:

```tsx
      <AvisoDeBackend
        jaCorrigido={Object.values(encerradas).some((e) => e.resultados_antes > 0)}
      />
```

E no fim do `<main>`, depois do `BlocoDeRecusa`:

```tsx
              {execucao.terminou && execucao.estado ? (
                <BlocoDeResultado estado={execucao.estado} />
              ) : null}
```

Além disso, mostre o erro do stream. Antes da `<LinhaDoTempo>`:

```tsx
              {execucao.fluxo.error ? (
                <p role="alert" className="mb-3 rounded-lg border border-perigo bg-[#1E0E0E] px-3 py-2 text-xs text-[#FF6B6B]">
                  A execução falhou: {String(execucao.fluxo.error)}. Clique no termo de novo para tentar outra vez.
                </p>
              ) : null}
```

- [ ] **Passo 4: Verificar os três avisos**

1. Derrube o backend (`Ctrl+C` no terminal do `langgraph dev`) e recarregue a página. Esperado: a faixa vermelha com o comando. Suba de novo.
2. Rode "tênis impermeável" e aprove. Esperado: **"A busca achava 0. Agora acha 1."** com o `fix_id` embaixo.
3. Rode "tênis impermeável" **de novo**. Esperado: a faixa dourada avisando que a correção já está aplicada, com o comando de reset.

- [ ] **Passo 5: Commit**

```bash
git add front/src/componentes/BlocoDeResultado.tsx front/src/componentes/AvisoDeBackend.tsx front/src/App.tsx
git commit -m "Bloco de resultado governado por escreveu, e os avisos de ambiente"
```

---

### Task 13: Aviso de largura mínima

**Arquivos:**
- Modificar: `front/src/App.tsx`

O responsivo mobile está fora de escopo (spec §9). Mas quebrar em silêncio numa tela estreita é pior que avisar.

- [ ] **Passo 1: Envolver o app**

No `App.tsx`, dentro do `<div className="min-h-dvh">`, adicione como primeiro filho:

```tsx
      <p className="border-b border-aviso bg-[#1F1A0A] px-5 py-2 text-xs text-aviso lg:hidden">
        O Venditus foi desenhado para tela larga. Abaixo de 1024px o layout não
        acompanha — use um monitor.
      </p>
```

E troque a `<div className="flex">` por `<div className="flex min-w-[960px]">` para o conteúdo não se espremer.

- [ ] **Passo 2: Verificar**

Estreite a janela abaixo de 1024px. Esperado: a faixa âmbar aparece e o conteúdo ganha rolagem horizontal em vez de se deformar.

- [ ] **Passo 3: Commit**

```bash
git add front/src/App.tsx
git commit -m "Avisa em telas estreitas em vez de quebrar em silencio"
```

---

### Task 14: Ensaio ao vivo dos dois casos

Nenhum código novo. É o ensaio geral, na ordem exata da gravação.

- [ ] **Passo 1: Zerar a loja**

```bash
cd back && .venv/Scripts/python scripts/verificar_shopify.py --resetar
```

- [ ] **Passo 2: Rodar a suíte do front**

```bash
cd front && npm test
```

Esperado: `28 passed`. **Se algo falhar, conserte antes de gravar.**

- [ ] **Passo 3: Subir os dois processos**

```bash
cd back && .venv/Scripts/langgraph dev --no-browser --port 2024
```

```bash
cd front && npm run dev
```

- [ ] **Passo 4: Percorrer o roteiro e conferir cada quadro**

| # | ação | o que tem que aparecer |
|---|---|---|
| 1 | abrir `http://localhost:5173` | três indicadores em `—`, lista ordenada por R$, estado vazio, nenhuma faixa de aviso |
| 2 | clicar em **tênis impermeável** | passos acendendo, segundos correndo |
| 3 | aguardar o diagnóstico | "Atributo faltando", `SKU-4471 · Tênis Trilha Alpha`, "Marcar “Tênis Trilha Alpha” como impermeável no catálogo" |
| 4 | aguardar o guarda | "Liberado pelo pós-venda", **R$ 3.841,73** grande, dois botões |
| 5 | clicar em **Aprovar e gravar** | passos até o fim, **"A busca achava 0. Agora acha 1."**, `fix_id` |
| 6 | olhar os indicadores | `R$ 3.841,73` · `0 de 1` · `0 → 1` |
| 7 | clicar em **capa de chuva impermeável** | mesmo diagnóstico, mesma proposta de escrita |
| 8 | aguardar o guarda | **passo vermelho**, os três seguintes riscados |
| 9 | ler o bloco de recusa | "8 das 11 devoluções contradizem", as onze frases, "O catálogo continua como estava." |
| 10 | olhar os indicadores | `R$ 3.841,73` · **`1 de 2`** · `0 → 1` |

O quadro 10 é o argumento inteiro num lugar só: mesma entrada, decisões opostas, e a taxa de recusa subindo ao vivo.

- [ ] **Passo 5: Anotar o que estiver errado e corrigir antes de gravar**

Se algum quadro divergir, corrija agora. **Não grave com um quadro errado** — o júri vê o vídeo, não o código.

- [ ] **Passo 6: Commit de qualquer ajuste**

```bash
git add -A front/
git commit -m "Ajustes do ensaio geral"
```

---

### Task 15: Atualizar o README

**Arquivos:**
- Modificar: `README.md:208`

Única alteração fora de `front/` no plano inteiro (decisão D5 do spec).

- [ ] **Passo 1: Trocar a linha da stack**

De:

```markdown
| ⚛️ Front | React + `useStream` + shadcn/ui *(próxima rodada)* |
```

Para:

```markdown
| ⚛️ Front | **React + Vite + `useStream`** + Tailwind v4 |
```

- [ ] **Passo 2: Atualizar a linha de escopo**

Na seção `## 🚧 Escopo`, remova `front-end` da lista de itens "Fora, e declarado" — ele deixou de estar fora.

- [ ] **Passo 3: Apontar os documentos do front**

Na tabela `## 📚 Documentos`, acrescente:

```markdown
| 🎨 [Design do front](docs/superpowers/specs/2026-08-09-venditus-front-design.md) | telas, nomenclatura e as lacunas do contrato |
```

- [ ] **Passo 4: Commit**

```bash
git add README.md
git commit -m "Atualiza a stack do front e tira o front-end do escopo declarado"
```

---

## Autorrevisão

**Cobertura do spec:**

| seção do spec | tarefa |
|---|---|
| §1 lacuna 1 (`perda_estimada`) | Task 2 (`perdaEstimada`), Task 6 (`iniciar`) |
| §1 lacuna 2 (fila) | Task 2 (`BUSCAS`), Task 7 |
| §1 lacuna 3 (cobertura) | Task 5 (substituída pelo antes/depois) |
| §1 lacuna 4 (títulos) | Task 2 (`TITULOS`), Task 9 |
| §1 armadilha do `status` | Task 5 (teste dedicado), Task 12 (`BlocoDeResultado`) |
| §2 D1 espelho | Task 2 |
| §2 D2 antes/depois | Task 5, Task 7 |
| §2 D3 ao vivo | Task 1, Task 14 |
| §2 D4 forma B | Task 7 |
| §2 D5 sem shadcn | Task 0, Task 15 |
| §2 D6 só dark | Task 0 (`tema.css` com o bloco light comentado) |
| §2 D7 proxy | Task 0 |
| §2 D8 rótulo + nó | Task 4 |
| §3 nomenclatura | Task 4 (nós), Task 7 (vocabulário), Task 9 (causas), Task 3 (frase da correção) |
| §4 arquitetura | Tasks 2, 5, 6 |
| §5 os dez componentes | Tasks 7 a 12 |
| §6 tela de recusa | Task 11 |
| §7 erros | Task 12 |
| §8 testes | Tasks 3, 4, 5 |
| §9 fora de escopo | Task 13 (aviso de largura) |
| §10 fronteiras | Task 15 é a única alteração fora de `front/` |

**Sem placeholders:** todo passo que muda código traz o código; todo comando traz a saída esperada.

**Consistência de tipos:** `EstadoVenditus`, `Status`, `Diagnostico`, `CorrecaoProposta`, `DecisaoGuarda`, `Devolucao` definidos na Task 2 e usados sem renomeação nas Tasks 3, 5, 6, 9, 10, 11, 12. `derivarPassos` (Task 4) e `indicadores` (Task 5) mantêm o nome nas Tasks 8 e 7. `usarExecucao` devolve `{ fluxo, estado, iniciar, responder, termoAtual, segundos, terminou }` (Task 6) e o `App.tsx` consome exatamente esses nomes nas Tasks 7 a 13.

**Contagem de testes:** 9 (Task 3) + 12 (Task 4) + 7 (Task 5) = **28**, o número esperado nas Tasks 5 e 14.
