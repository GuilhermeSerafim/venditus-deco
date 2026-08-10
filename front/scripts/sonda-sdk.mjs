/** Sonda da superficie do SDK JavaScript do LangGraph.
 *
 * Equivalente da Task 0 do backend, para o front: confirma o protocolo real
 * antes de qualquer componente ser construido em cima dele. O AGENTS.md
 * registra o motivo — "nao descubra na Task 10".
 *
 * Roda os dois casos do pitch de ponta a ponta contra o backend de verdade.
 * Exige o `langgraph dev` no ar em 127.0.0.1:2024.
 *
 *   cd front && node scripts/sonda-sdk.mjs
 *
 * ATENCAO: o caso 1, se aprovado, escreve na loja Shopify real. Rode
 * `back/scripts/verificar_shopify.py --resetar` depois.
 */

import { Client } from "@langchain/langgraph-sdk";

const URL_API = "http://127.0.0.1:2024";
const ASSISTENTE = "venditus";

const cliente = new Client({ apiUrl: URL_API });

const falhas = [];

function conferir(rotulo, condicao, obtido) {
  const marca = condicao ? "OK  " : "FALHA";
  console.log(`  [${marca}] ${rotulo}${condicao ? "" : `  -> obtido: ${JSON.stringify(obtido)}`}`);
  if (!condicao) falhas.push(rotulo);
}

function titulo(texto) {
  console.log(`\n${"=".repeat(70)}\n${texto}\n${"=".repeat(70)}`);
}

/** Roda um run ate ele terminar ou pausar, devolvendo estado e snapshot.
 *
 * Usa `runs.stream` e nao `runs.wait`: quando o grafo pausa num interrupt(),
 * o `wait` recebe corpo vazio do servidor e estoura com "Unexpected end of
 * JSON input". O `stream` e tambem o caminho que o useStream usa por baixo,
 * entao sondar por ele prova o protocolo que o front vai falar de verdade.
 */
async function rodar(threadId, corpo) {
  const vistos = [];
  let valores = {};

  for await (const evento of cliente.runs.stream(threadId, ASSISTENTE, {
    ...corpo,
    streamMode: ["values"],
  })) {
    if (evento.event === "values" && evento.data) {
      valores = evento.data;
      if (typeof valores.status === "string" && vistos.at(-1) !== valores.status) {
        vistos.push(valores.status);
      }
    }
    if (evento.event === "error") {
      throw new Error(`stream devolveu erro: ${JSON.stringify(evento.data)}`);
    }
  }

  const snapshot = await cliente.threads.getState(threadId);
  return { valores, snapshot, vistos };
}

async function caso1() {
  titulo('CASO 1 — "tênis impermeável" (o que deve passar)');

  const thread = await cliente.threads.create();
  console.log(`  thread: ${thread.thread_id}`);

  const { valores, snapshot, vistos } = await rodar(thread.thread_id, {
    input: { termo: "tênis impermeável", volume: 340, perda_estimada: 3841.73 },
  });

  console.log(`\n  sequencia de status observada: ${vistos.join(" -> ")}`);
  console.log(`  status: ${valores.status}`);
  console.log(`  resultados_antes: ${valores.resultados_antes}`);
  console.log(`  causa: ${JSON.stringify(valores.diagnostico?.causa)}`);
  console.log(`  correcao: ${JSON.stringify(valores.diagnostico?.correcao)}`);
  console.log(`  proximo no (snapshot.next): ${JSON.stringify(snapshot.next)}`);

  conferir("status === aprovado_pelo_guarda", valores.status === "aprovado_pelo_guarda", valores.status);
  conferir(
    "causa serializa como STRING, nao objeto",
    typeof valores.diagnostico?.causa === "string",
    valores.diagnostico?.causa
  );
  conferir("causa === atributo_ausente", valores.diagnostico?.causa === "atributo_ausente", valores.diagnostico?.causa);
  conferir("correcao.sku === SKU-4471", valores.diagnostico?.correcao?.sku === "SKU-4471", valores.diagnostico?.correcao);
  conferir("correcao.campo === impermeavel", valores.diagnostico?.correcao?.campo === "impermeavel", valores.diagnostico?.correcao);
  conferir("correcao.valor === true", valores.diagnostico?.correcao?.valor === "true", valores.diagnostico?.correcao);
  conferir("o run PAUSOU em aprovacao", snapshot.next?.includes("aprovacao"), snapshot.next);

  // O payload cru da pausa: e o que o useStream expoe em interrupt.value
  const interrupcoes = snapshot.tasks?.flatMap((t) => t.interrupts ?? []) ?? [];
  console.log(`\n  PAYLOAD CRU DA PAUSA:\n${JSON.stringify(interrupcoes, null, 2)}`);
  conferir("existe ao menos uma interrupcao no snapshot", interrupcoes.length > 0, interrupcoes.length);

  if (valores.resultados_antes !== 0) {
    console.log(`\n  AVISO: resultados_antes = ${valores.resultados_antes}, esperado 0.`);
    console.log("  A loja provavelmente ja esta corrigida. Rode o reset antes de gravar.");
  }

  // Retomada
  console.log("\n  retomando com { aprovado: true } ...");
  const { valores: finais } = await rodar(thread.thread_id, {
    command: { resume: { aprovado: true } },
  });

  console.log(`  status final: ${finais.status}`);
  console.log(`  escreveu: ${finais.escreveu}`);
  console.log(`  fix_id: ${finais.fix_id}`);
  console.log(`  resultados_depois: ${finais.resultados_depois}`);

  conferir("status final === aplicado", finais.status === "aplicado", finais.status);
  conferir("escreveu === true", finais.escreveu === true, finais.escreveu);
  conferir("fix_id tem 16 hex", /^[0-9a-f]{16}$/.test(finais.fix_id ?? ""), finais.fix_id);
  conferir(
    "resultados_depois > resultados_antes",
    finais.resultados_depois > finais.resultados_antes,
    `${finais.resultados_antes} -> ${finais.resultados_depois}`
  );
}

async function caso2() {
  titulo('CASO 2 — "capa de chuva impermeável" (o que deve ser bloqueado)');

  const thread = await cliente.threads.create();
  console.log(`  thread: ${thread.thread_id}`);

  const { valores, snapshot, vistos } = await rodar(thread.thread_id, {
    input: { termo: "capa de chuva impermeável", volume: 128, perda_estimada: 1446.3 },
  });

  const devolucoes = valores.devolucoes_consultadas ?? [];
  const guarda = valores.decisao_guarda;

  console.log(`\n  sequencia de status observada: ${vistos.join(" -> ")}`);
  console.log(`  status: ${valores.status}`);
  console.log(`  escreveu: ${valores.escreveu}`);
  console.log(`  permitir: ${guarda?.permitir}`);
  console.log(`  devolucoes_contraditorias: ${guarda?.devolucoes_contraditorias}`);
  console.log(`  justificativa: ${guarda?.justificativa}`);
  console.log(`  proximo no (snapshot.next): ${JSON.stringify(snapshot.next)}`);

  console.log(`\n  DEVOLUCOES CONSULTADAS (${devolucoes.length}):`);
  for (const d of devolucoes) {
    console.log(`    (${String(d.dias_atras).padStart(2)}d) [${d.sku}] "${d.motivo}"`);
  }

  conferir("status final === quarentena", valores.status === "quarentena", valores.status);
  conferir("escreveu === false", valores.escreveu === false, valores.escreveu);
  conferir("permitir === false", guarda?.permitir === false, guarda?.permitir);
  conferir("devolucoes_contraditorias === 8", guarda?.devolucoes_contraditorias === 8, guarda?.devolucoes_contraditorias);
  conferir("justificativa nao vazia", (guarda?.justificativa ?? "").length > 0, guarda?.justificativa);
  conferir("o run NAO pausou", !snapshot.next || snapshot.next.length === 0, snapshot.next);

  // O campo que sustenta a tela de recusa inteira.
  conferir("devolucoes_consultadas tem 11 itens", devolucoes.length === 11, devolucoes.length);
  conferir(
    "cada devolucao tem sku, motivo e dias_atras",
    devolucoes.every((d) => typeof d.sku === "string" && typeof d.motivo === "string" && typeof d.dias_atras === "number"),
    devolucoes[0]
  );
}

async function main() {
  console.log(`sondando ${URL_API} · assistente "${ASSISTENTE}"`);

  await caso1();
  await caso2();

  titulo("VEREDITO");
  if (falhas.length === 0) {
    console.log("  Todas as confirmacoes passaram. O contrato do spec esta correto.");
  } else {
    console.log(`  ${falhas.length} confirmacao(oes) FALHARAM:`);
    for (const f of falhas) console.log(`    - ${f}`);
  }
  console.log("\n  Lembrete: o caso 1 escreveu na loja. Rode o reset:");
  console.log("  cd back && .venv/Scripts/python scripts/verificar_shopify.py --resetar");

  process.exit(falhas.length === 0 ? 0 : 1);
}

main().catch((erro) => {
  console.error("\nSONDA QUEBROU:", erro);
  process.exit(2);
});
