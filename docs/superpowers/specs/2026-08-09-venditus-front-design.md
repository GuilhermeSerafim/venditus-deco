# Venditus — Design do front

**Data:** 2026-08-09
**Contexto:** Hackathon deco "Agents for Commerce" — rodada do front
**Orçamento:** poucas horas, backend fechado
**Antecedentes:** [`README.md`](../../../README.md) · [`front/HANDOFF.md`](../../../front/HANDOFF.md) · [`AGENTS.md`](../../../AGENTS.md) · [spec do MVP](2026-08-09-venditus-mvp-design.md)

---

## Context

O backend está completo: 15 tarefas, 78 testes, rodando com GPT-5.6 e uma loja Shopify real. Falta a interface, e é ela que o júri vê no vídeo.

A restrição dominante é dupla. Primeiro, **tempo**: poucas horas até a gravação. Segundo, **o backend está fechado** — `back/src/` e `back/tests/` não são modificados, e dado que falta vira relatório, não gambiarra no front.

O objetivo da interface não é ser um admin completo. É tornar visível uma única afirmação: *dois casos entram com diagnóstico idêntico e saem com decisões opostas, e a diferença só existe porque os dois sinais estão no mesmo motor.*

---

## 1. O que o backend entrega e o que ele não entrega

`langgraph dev` expõe apenas a API do grafo — threads, runs, stream, state. Não há rota custom em `back/langgraph.json`. Quatro consequências foram levantadas antes de qualquer decisão de design:

| # | Lacuna | Origem | Efeito no front |
|---|---|---|---|
| 1 | `perda_estimada` é obrigatória no input e nenhum nó a calcula | `aprovacao` lê `state["perda_estimada"]` (`graph.py:40`); quem preenche é `estado_inicial()` (`state.py:32`), que não passa por HTTP | O front **precisa** enviá-la no `submit`. Sem ela o run quebra com `KeyError` no nó da pausa — depois de duas chamadas de LLM já pagas |
| 2 | A fila não existe como recurso | `seed.BUSCAS` (`seed.py:37`) | Sem espelho, a lista de buscas não tem origem |
| 3 | `cobertura_de_atributo` é incalculável | `metrics.py:14` exige `catalogo.listar_produtos()`, não servido | Métrica substituída (ver §2) |
| 4 | O título do produto não trafega no estado | O estado carrega `correcao.sku`, não `titulo` | Sem espelho, a tela mostraria "SKU-8802" sem nome |

Nenhuma é bug: o backend foi desenhado como grafo, não como API de leitura.

### A armadilha do `status`

`status === "aplicado"` **não significa que algo foi escrito.**

Quando o diagnóstico vem sem correção (`sem_estoque` / `sem_sortimento`), o `executor` devolve `status="sem_correcao"` e `escreveu=False` (`nodes.py:46`). Mas a aresta `executor → verificador` roda em seguida, e o verificador sobrescreve com `status="aplicado"` (`nodes.py:67`). O `sem_correcao` só é observável no meio do stream; no estado final ele nunca aparece.

`metrics.py:38` já decide por `escreveu`, e não por `status`. **O front segue a mesma regra, em todo lugar, sem exceção.** É o terceiro item da fila (`mochila cargueira 80 litros`) que percorre esse caminho.

---

## 2. Decisões

| # | Decisão | Alternativa recusada | Motivo |
|---|---|---|---|
| D1 | **Espelho mínimo e declarado** em `dados/espelho.ts`: as 3 buscas, a fórmula da estimativa, os 5 títulos de produto. Cada bloco comentado com o arquivo-fonte do back | Abrir rotas de leitura no backend | Backend fechado; a duplicação fica visível num arquivo só, e não espalhada |
| D2 | **`antes → depois` no lugar de `cobertura_de_atributo`** nos indicadores | Espelhar o catálogo e calcular cobertura no front | Exigiria rastrear escritas no front — contorno proibido. E `0 → 1` na busca é mais forte que `0% → 20%` de cobertura sobre 5 produtos |
| D3 | **100% ao vivo** contra `langgraph dev`, sem camada de replay | Modo ensaio com estados gravados | Os 15-40s de LLM viram cena (a linha do tempo acendendo), não problema a esconder. O tempo poupado vai para essa animação |
| D4 | **Forma B: lista fixa + investigação ao lado** | Páginas separadas com menu; lista que expande | A tese é "os dois saem da mesma lista e divergem". Isso só é visível se a lista continuar na tela durante o bloqueio. Vídeo sem corte |
| D5 | **Vite + React + TS + Tailwind, sem shadcn/ui** | shadcn/ui; Next.js | Dos ~10 componentes, o shadcn cobre 3, e os triviais. Diverge do `README.md` linha 208 — **a linha é atualizada junto**. Os tokens ficam no formato HSL do shadcn, então adotá-lo depois continua sendo um comando |
| D6 | **Só tema dark** | Dark + light; só light | `#D9A520` sobre branco dá 2,2:1 — reprova em WCAG AA (4,5:1) e no piso de 3:1 para elemento gráfico. Sobre `#0D0D0D` dá 8,6:1. O light exigiria redesenhar todo lugar onde o gold aparece. Os tokens light do HANDOFF §5 ficam preservados em bloco comentado, com a nota de contraste |
| D7 | **Proxy do Vite** `/api → http://127.0.0.1:2024` | Chamar a origem direto e tratar CORS se aparecer | Quatro linhas eliminam a chance de descobrir CORS de madrugada |
| D8 | **Rótulo em português + nome técnico do nó em mono** | Só o nome do nó; só o rótulo amigável | O jurado lê o que acontece; o jurado engenheiro reconhece o grafo do LangGraph |

---

## 3. Nomenclatura

Convenção de `AGENTS.md`: código, identificadores e textos em português.

### Os nós na linha do tempo

| nó | rótulo na tela |
|---|---|
| `ingest` | Mede a busca |
| `investigador` | Investiga a causa |
| `guarda` | Audita as devoluções |
| `aprovacao` | Sua aprovação |
| `executor` | Grava no catálogo |
| `verificador` | Refaz a busca |

São **seis passos, não sete**. `quarentena` não é etapa do caminho, é o fim dele — aparece como rótulo de status no rodapé do bloco de recusa. Colocá-la como sétimo passo sugeriria um caminho que passa por ela e continua.

### Vocabulário da interface

| em vez de | na tela | motivo |
|---|---|---|
| Dashboard | **Resultado** | é o que ele mostra |
| KPIs | **Indicadores** | sigla de consultoria não comunica em vídeo |
| Fila / Queue | **Buscas sem resultado** | nomeia o problema, não a estrutura de dados |
| `taxa_de_bloqueio` | **Correções recusadas** | "bloqueio" soa a falha do sistema; "recusada" soa a decisão — e é uma decisão |
| `resultados_antes → depois` | **"A busca achava 0. Agora acha 1."** | frase, não par de números |
| `quarentena` | **"Nada foi gravado"** + `quarentena` em mono | ver abaixo |

### Por que "Quarentena" saiu do texto principal

O nó `quarentena` (`nodes.py:30`) encerra o grafo sem escrever. Ele não retira o produto do ar, não abre chamado, não põe a correção numa fila de revisão. Nada disso existe.

A palavra "quarentena" **promete uma ação que não acontece**. Numa interface cuja tese é *"a gente recusa quando não sabe"*, exagerar o que o sistema faz é o erro mais caro possível. Então:

- Título do bloco: **"Correção recusada"**
- Fato em destaque: **"O catálogo continua como estava."**
- Rodapé, em tom menor: *"O caso vira hipótese para o time de qualidade — o Venditus não abre chamado, ele para e mostra o porquê."* + `status: quarentena` em mono

Mesmo padrão que o README já usa para o R$: narrativa rotulada como narrativa, fato como fato.

### A correção proposta, em duas camadas

`campo="impermeavel"` e `valor="true"` são o que o `executor` grava. Exibir o par cru faz o leitor processar chave-valor em vez de ler a frase. Molde:

```
valor em {true, sim, 1, verdadeiro}  →  Marcar “{título}” como {campo acentuado}
qualquer outro valor                  →  Definir {campo} de “{título}” como {valor}
```

Abaixo, em mono cinza: `atributo impermeavel = "true" · SKU-4471 · loja Shopify`.

O **campo acentuado** vem de casar `normalizar(token do termo) === campo`. O prompt do investigador exige que o nome do campo seja "a própria palavra que o cliente buscou", sem acento (`nodes.py:96`) — então o `termo` no estado carrega a versão acentuada da mesma palavra. Nada é inventado: é a palavra do cliente, que já está no estado. Sem casamento, exibe o campo cru.

---

## 4. Arquitetura

### Fluxo de um caso

```
ListaDeBuscas (clique)
  └→ usarExecucao(termo, volume)
       submit({ termo, volume, perda_estimada })      ← lacuna #1
       ↓ stream
       values.status ─────────────→ derivarPassos() → LinhaDoTempo
       decisao_guarda.permitir=false ───────────────→ BlocoDeRecusa
       interrupt presente ──────────────────────────→ BarraDeAprovacao
            └→ submit(undefined, { command: { resume: { aprovado } } })
       estado terminal ──→ push em execucoes[]
                              └→ indicadores(execucoes) → FaixaDeIndicadores
```

Um `useStream` por execução; o array de execuções encerradas vive acima dele. `indicadores()` espelha `metrics.py` com a mesma assinatura (`estados: VenditusState[]`) e a mesma regra do `escreveu`.

O payload de retomada é `{ aprovado: boolean }` — o formato que `graph.py:45` lê.

Dois parâmetros do `useStream` que travam a integração se estiverem errados: `apiUrl` é `/api` (o proxy do D7, não a origem direta) e `assistantId` é **`"venditus"`** — a chave de `graphs` em `back/langgraph.json`, não o nome do arquivo nem do módulo.

O Vite serve `front/public/` na raiz por padrão, então `logo-venditus.png` fica onde já está. Não mover.

### Estrutura

```
front/
  vite.config.ts               proxy /api → 127.0.0.1:2024
  src/
    dados/
      espelho.ts               3 buscas, fórmula, 5 títulos — cada bloco com o
                               arquivo-fonte do back no comentário
      contrato.ts              tipos TS espelhando state.py e models.py
    logica/
      passos.ts                status + interrupt → linha do tempo      ← testado
      indicadores.ts           espelho de metrics.py                    ← testado
      formato.ts               R$, dias, plural, campo acentuado
    ganchos/
      usarExecucao.ts          embrulha useStream
    componentes/               Cabecalho · FaixaDeIndicadores · ListaDeBuscas ·
                               LinhaDoTempo · CartaoDeDiagnostico · BlocoDeRecusa ·
                               BarraDeAprovacao · BlocoDeResultado · EstadoVazio ·
                               AvisoDeBackend
    estilos/tema.css           tokens gold dark; tokens light do HANDOFF §5 em
                               bloco comentado com a nota de contraste
```

`passos.ts` e `indicadores.ts` são funções puras, fora do React — são as duas coisas que podem estar caladamente erradas durante a gravação.

---

## 5. Os componentes

| componente | mostra | decisão embutida |
|---|---|---|
| `Cabecalho` | logo + marca | `logo-venditus.png` sobre `#0D0D0D` |
| `FaixaDeIndicadores` | recuperado · **recusadas** · a busca acha | "recusadas" com o mesmo peso visual do R$ e moldura gold, como o HANDOFF §4 pede. `tabular-nums` para não tremer ao atualizar. Antes da 1ª execução exibem `—`, não `0` |
| `ListaDeBuscas` | 3 buscas ordenadas por R$ | fórmula da estimativa sempre visível no rodapé. Itens desabilitados durante um run |
| `LinhaDoTempo` | 6 passos | **passos mortos riscados e a 30% quando o guarda bloqueia** — a tese virando pixel: o caminho até a escrita deixa de existir. Passo ativo mostra segundos correndo (senão parece travado no vídeo) |
| `CartaoDeDiagnostico` | causa traduzida, confiança, evidência citada, correção em duas camadas | causa vira frase: `atributo_ausente` → "Atributo faltando" |
| `BlocoDeRecusa` | as 11 frases + justificativa do guarda | ver §6 |
| `BarraDeAprovacao` | a correção, o R$ em destaque, 2 botões | um CTA primário só (gold, texto preto); "Rejeitar" fantasma. O R$ em 34px acima dos botões: a decisão é sobre esse número |
| `BlocoDeResultado` | "A busca achava 0. Agora acha 1." + `fix_id` | governado por `escreveu` |
| `EstadoVazio` | linha do tempo apagada + "Escolha uma busca" | o júri vê o formato do pipeline antes de qualquer clique |
| `AvisoDeBackend` | backend fora do ar; loja já corrigida | ver §7 |

---

## 6. A tela de recusa

É o clímax do vídeo, não um estado de erro.

`devolucoes_consultadas` traz **as 11** devoluções do SKU — `nodes.py:169` chama `devolucoes_do_sku(c.sku)` sem filtro. `decisao_guarda.devolucoes_contraditorias` diz **8**. O backend não informa *quais* 8, e está certo em não informar: fazer o LLM reescrever as frases lhe daria a chance de parafrasear o cliente, que é exatamente o que o comentário em `nodes.py:179` evita.

**Portanto o front não marca quais contradizem.** Filtrar por palavra-chave seria inventar uma inferência que o backend não fez. A lista é rotulada pelo que ela é — *"as 11 devoluções que o guarda leu"* — com o contador no título. Ver onze reclamações seguidas, das quais oito falam de água, é mais forte que ver oito marcadas.

Ordem: `dias_atras` crescente, a mais recente primeiro. As frases são o payload — 13px, itálico, maiores que o corpo do texto.

O título traz ícone SVG do Lucide **e** a palavra "RECUSADA": a regra `color-not-only` proíbe comunicar o bloqueio só pelo vermelho, e `no-emoji-icons` descarta o 🛑 sugerido no HANDOFF §4 (emoji renderiza diferente por SO e não aceita token de cor).

---

## 7. Erros

| situação | como aparece |
|---|---|
| backend fora do ar (`GET /api/ok` falha) | faixa no topo com o comando: `cd back && .venv\Scripts\langgraph dev --no-browser --port 2024` |
| run falha no meio (chave inválida, rate limit) | passo ativo em vermelho com a mensagem do erro e "tentar de novo" |
| `resultados_antes > 0` num caso que deveria dar 0 | aviso discreto: correção já aplicada na loja, rode `python scripts/verificar_shopify.py --resetar` |
| nada clicado ainda | `EstadoVazio` |

O terceiro é o erro mais provável entre um take e outro da gravação.

---

## 8. Testes

Dois arquivos, Vitest, só as funções puras:

- **`passos.test.ts`** — os dez status (`novo`, `diagnosticando`, `diagnosticado`, `aprovado_pelo_guarda`, `bloqueado_pelo_guarda`, `quarentena`, `aprovado`, `rejeitado`, `aplicado`, `sem_correcao`) mais a presença do `interrupt`, virando a linha do tempo correta.
- **`indicadores.test.ts`** — espelho do `metrics.py`, incluindo o caso que prova que `status="aplicado"` com `escreveu=false` **não** conta receita.

O resto é verificação a olho. Com poucas horas, testar componente de React custa mais do que protege.

---

## 9. Fora de escopo

Declarado, não esquecido:

- Tema light (D6)
- Responsivo mobile — o vídeo é desktop; abaixo de 1024px o app avisa em vez de quebrar
- Histórico entre sessões via `GET /threads` — os indicadores zeram no F5, aceitável num take
- Qualquer escrita que não passe pelo nó `executor`
- Autenticação, deploy, multi-loja — herdado de `AGENTS.md` §6

---

## 10. Fronteiras herdadas

De `AGENTS.md` e `front/HANDOFF.md` §6, sem alteração:

- Trabalho em `front/`. **`back/src/` e `back/tests/` não são modificados.**
- Dado que falta vira relatório, não contorno no front.
- **Um único token de gold**, definido uma vez. As três inconsistências do projeto de origem (Tremor com gold divergente, `dark-tremor` azul, `tertiary` indefinido) não são reproduzidas — e o Tremor não entra, então a primeira não se aplica.
- Textos, identificadores e commits em português.

Uma alteração fora de `front/` é prevista: a linha 208 do `README.md`, que anuncia shadcn/ui na stack (D5).
