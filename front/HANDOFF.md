# Handoff — front do Venditus

Documento de partida para quem vai construir a interface. O backend está
pronto, testado e rodando.

---

## 1. O produto, em três parágrafos

Lojas de e-commerce perdem venda porque **o catálogo não fala a língua do
cliente**. Alguém busca *"tênis impermeável"*, a loja tem o produto, mas a
palavra só existe no texto da descrição e não como atributo estruturado. A
busca não acha e o cliente vai embora **calado** — a loja nunca fica sabendo.

O Venditus lê essas buscas, descobre a causa e corrige o catálogo. Mas antes de
corrigir, ele **lê as devoluções daquele produto**. Se os clientes que compraram
dizem que o produto molha, ele **recusa** a correção e encaminha para qualidade —
porque marcar como impermeável aumentaria devolução.

Dois produtos entram com **diagnóstico idêntico** e saem com decisões opostas:

| | 🥾 SKU-4471 Tênis Trilha Alpha | 🧥 SKU-8802 Capa de Chuva Nimbus |
|---|---|---|
| Descrição menciona impermeabilidade | sim | sim |
| Atributo estruturado | ausente | ausente |
| Devoluções em 90 dias | 3, nenhuma sobre água | 11, **8 dizem que molha** |
| Decisão | ✅ corrige | 🛑 **recusa** |

**A tela de recusa é o clímax do vídeo do pitch.** Não é um estado de erro —
é a peça principal da interface.

---

## 2. Rodando

São **dois processos, em dois terminais**. Os comandos abaixo são para
**Windows PowerShell 5.1**, que é o shell da máquina do projeto.

> ⚠️ Duas diferenças que derrubam quem copia comando de tutorial:
> **`&&` não existe** no PowerShell 5.1 — o separador é `;`, ou uma linha por
> comando. E o executável precisa de `.\` na frente, senão o PowerShell não
> resolve o caminho relativo.

### Preparo, uma vez só

```powershell
cd back
python -m venv .venv
.\.venv\Scripts\pip.exe install -e ".[dev]"
.\.venv\Scripts\python.exe -c "import venditus"   # tem que passar sem erro
```

Crie `back/.env` com a sua chave (o servidor não sobe sem ela):

```
OPENAI_API_KEY=sk-...
```

### Terminal 1 — backend

```powershell
cd back
.\.venv\Scripts\langgraph.exe dev --no-browser --port 2024
```

Deixe rodando e **de olho**: é neste terminal que aparece o traceback quando
um run falha. A API devolve só `"An internal error occurred"`, sem o detalhe.

### Terminal 2 — front

```powershell
cd front
npm install     # uma vez só
npm run dev
```

### Onde você olha

| processo | porta | abre no navegador? |
|---|---|---|
| front (Vite) | **5173** | **sim — `http://localhost:5173`** |
| backend (`langgraph dev`) | 2024 | não; só `/docs`, se quiser o Swagger |

O front fala com o backend pelo proxy `/api`, configurado em
`front/vite.config.ts`. O navegador nunca chama a porta 2024 diretamente — é
o que elimina CORS.

Confira o backend: `curl http://127.0.0.1:2024/ok` → `{"ok":true}`

### Ritual de reteste

Duas coisas guardam estado entre um ensaio e outro. **Zere as duas antes de
cada tomada**, sempre nesta ordem:

**1. A loja** — só é necessário se a execução anterior *escreveu* (o caso do
tênis aprovado). O caso da capa é bloqueado e não escreve nada.

```powershell
cd back
.\.venv\Scripts\python.exe scripts\verificar_shopify.py --resetar
```

A saída confirma o estado de partida:
`busca por 'tênis impermeável' agora: 0 resultado(s)`

**2. O servidor** — **obrigatório sempre que o passo 1 rodar.** Pare o
`langgraph dev` (`Ctrl+C`) e suba de novo.

O adapter guarda os `fix_id` já aplicados num `set` **em memória**
(`adapters/shopify.py:79`), e o servidor cria um adapter só, no import. O
script de reset roda em outro processo e apaga o metafield da Shopify, mas
não toca nessa memória. Sem reiniciar:

```
executor  → correcao_ja_aplicada(fix_id) = True → PULA a escrita
          → devolve escreveu: true assim mesmo
verificador → consulta a loja → o atributo não está lá → 0 resultados
```

O sintoma é **"A busca achava 0. Agora acha 0."** com `escreveu: true`. A
interface detecta isso e mostra um aviso âmbar em vez do número de sucesso,
mas a causa é esta e o conserto é reiniciar.

**3. A tela** — abra `http://localhost:5173/?limpar`

O `?limpar` some da barra de endereço sozinho depois de agir, para um F5
acidental não zerar tudo no meio da apresentação.

**Como saber que está no estado de partida:** a lista não tem nenhum selo
(`gravado`, `recusado`), os três indicadores mostram `—`, e nenhuma nota
aparece ao rodar o primeiro caso.

Não precisa reiniciar o `langgraph dev` nem o `npm run dev` — cada execução
cria uma thread nova, e o Vite recarrega o código sozinho.

### Conferir o contrato sem abrir o navegador

```powershell
cd front
node scripts/sonda-sdk.mjs
```

Roda os dois casos do pitch pelo SDK e confere o protocolo item a item. É o
caminho mais rápido para saber se o problema está no backend ou na interface.

> ⚠️ A sonda **aprova o caso do tênis**, ou seja, escreve na loja de verdade.
> Rode o reset depois (veja a Armadilha 3).

### ⚠️ Armadilha 1 — instalação editável quebrada

Se `import venditus` falhar com `ModuleNotFoundError`, a instalação editável
quebrou silenciosamente. Rode:

```bash
.venv\Scripts\pip install -e . --force-reinstall --no-deps
```

Confirme que surgiu `_editable_impl_venditus.pth` em `.venv/Lib/site-packages`.
O sintoma é traiçoeiro: `pytest` funciona (injeta o caminho por config) e todo o
resto falha.

### ⚠️ Armadilha 2 — `langgraph` global em vez do venv

**Use sempre `.venv\Scripts\langgraph`, nunca `langgraph` solto.** Se houver um
`langgraph` instalado globalmente, o PATH pode resolvê-lo primeiro, e aí o
servidor sobe no Python global — que nunca enxerga o `.pth` do venv.

O sintoma engana por completo: o servidor sobe, `GET /ok` responde `200`, o
assistant aparece em `POST /assistants/search`, e **só quebra quando um run
executa de verdade**, com `{"error":"ModuleNotFoundError","message":"An
internal error occurred"}` — sem dizer qual módulo. O traceback fica só no
terminal do servidor.

Para confirmar qual Python está servindo:

```powershell
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
  Select-Object ProcessId, ExecutablePath
```

O processo do servidor tem que ser `back\.venv\Scripts\python.exe`.

### ⚠️ Armadilha 3 — resetar a loja não é cosmético

`python scripts/verificar_shopify.py --resetar` **muda o que o LLM
diagnostica**, não só o número da tela.

Com o atributo `impermeavel` já gravado no SKU-4471, a busca acha o produto, e
o investigador procura outra coisa faltando — numa execução real ele propôs
gravar `campo="tenis"`, um atributo inventado que não existia. O guarda liberou
(devoluções sobre tamanho e cor não contradizem "ser tênis"), e a escrita
aconteceu.

Ou seja: **sem reset, o caso do tênis não falha com erro — ele "funciona" e
mostra a correção errada na tela.** Resete antes de cada tomada.

O `--resetar` apaga apenas a chave `impermeavel`. Se um teste gravou outra
chave, apague-a à mão pelo admin da Shopify.

---

## 3. O contrato

**Leia `back/src/venditus/state.py`.** É exatamente o que chega no `useStream`.

### Os 7 nós e o `status` que cada um deixa

```
START → ingest ────────────────────────── "diagnosticando"
          ↓
       investigador (LLM) ──────────────── "diagnosticado"
          ↓
       guarda (LLM) ──── permitir=false ── "bloqueado_pelo_guarda"
          │                                        ↓
          │                              quarentena → END   "quarentena"  🛑
          │
          └──────────── permitir=true ──── "aprovado_pelo_guarda"
                            ↓
                        aprovacao  ← ⏸ interrupt(): espera o humano
                            ├── rejeitado → END              "rejeitado"
                            └── aprovado
                                  ↓
                              executor ─────────────────────  "aplicado"
                                  ↓
                              verificador → END               "aplicado"
```

`quarentena` é o status terminal do bloqueio — é o que `metrics.py` conta em
`taxa_de_bloqueio`. Existe também `sem_correcao`, quando o executor recebe um
diagnóstico sem correção proposta (`sem_estoque` / `sem_sortimento`).

### Campos do estado

| Campo | O que é |
|---|---|
| `termo` | a busca que falhou |
| `volume` | buscas por mês |
| `perda_estimada` | R$ estimados perdidos |
| `diagnostico` | `{causa, confianca, evidencia, correcao}` |
| `decisao_guarda` | `{permitir, justificativa, devolucoes_contraditorias}` |
| **`devolucoes_consultadas`** | **lista de `{sku, motivo, dias_atras}`** — é o que a tela de recusa renderiza |
| `resultados_antes` / `resultados_depois` | contagem da busca, antes e depois |
| `status`, `escreveu`, `fix_id` | controle |

### Payload da pausa de aprovação

```json
{ "termo": "...", "perda_estimada": 3841.73,
  "diagnostico": {...}, "decisao_guarda": {...} }
```

### Rotas que importam

| | |
|---|---|
| `POST /threads` | cria uma execução |
| `POST /threads/{id}/runs/stream` | roda e recebe estados em streaming |
| `GET /threads/{id}/state` | vê onde parou (detecta a pausa) |
| `POST /threads/{id}/runs` | retoma após aprovação |

O `useStream` do `@langchain/langgraph-sdk/react` embrulha tudo isso — inclusive
as pausas de aprovação. A fila não é estado escrito à mão, é o hook.

---

## 4. As quatro telas

**1. Fila** — buscas sem resultado, ordenadas por R$ perdido.

**2. Detalhe** — o diagnóstico, a evidência citada do catálogo, aprovar/rejeitar.

**3. 🛑 Recusa — a mais importante.** Mostre as **frases dos clientes**, não só o
contador:

```
BLOQUEADO — 8 de 11 devoluções contradizem

"Chovi 10 minutos e fiquei todo molhado"       5 dias
"Não é impermeável, é só repelente"            9 dias
"Molhou tudo dentro da bolsa"                 14 dias
```

*"8 devoluções contradizem"* é uma afirmação. Ver as frases é prova.

**4. Dashboard** — os quatro números já estão calculados em
`back/src/venditus/metrics.py` (`resumo_kpis`): `cobertura_de_atributo`,
`receita_recuperada`, `bloqueados` e `taxa_de_bloqueio`, mais o denominador
`execucoes`. Some a isso o antes/depois de cada execução
(`resultados_antes` → `resultados_depois`).

**A taxa de bloqueio é o número do pitch.** Nenhum concorrente consegue
calculá-la, porque nenhum tem o sinal de pré-venda e o de pós-venda no mesmo
motor. Dê a ela o mesmo peso visual do R$.

O R$ é **estimativa** (`volume × 2% × R$ 564,96` — ticket médio ABComm 2026).
Mostre a fórmula na tela e rotule como tal.

---

## 5. Identidade visual

Logo em `front/public/logo-venditus.png` — louros dourados com "VENDITUS".

### Gold

| Token | Light | Dark |
|---|---|---|
| `--gold` | `43 74% 49%` · `#D9A520` | idem |
| `--gold-light` | `45 80% 58%` · `#EABF3E` | idem |
| `--gold-dark` | `38 80% 42%` · `#C18215` | `40 85% 45%` · `#D49311` |
| `--gold-muted` | `43 30% 70%` · `#C9BC9C` | `43 40% 35%` · `#7D6936` |

`--primary` e `--ring` = gold `43 74% 49%` nos dois temas.
`--primary-foreground` = preto `0 0% 9%`.

### Feedback (iguais em light e dark)

`success 142 71% 45%` · `warning 38 92% 50%` · `info 217 91% 60%` ·
`destructive 0 84% 60%`

### Gráficos

`chart-1 217 91% 60%` azul · `chart-2 142 71% 45%` verde ·
`chart-3 262 83% 58%` roxo · `chart-4 32 95% 55%` laranja ·
`chart-5 340 82% 52%` rosa

### Neutros

**Light** — background `#FFFFFF` · subtle `#FAFAFA` · card `#FFFFFF` ·
secondary/muted/accent `#F5F5F5` · border/input `#E5E5E5` ·
muted-foreground `#737373` · foreground `#171717` ·
sidebar-hover `#F7F4ED` (gold lavado)

**Dark** — background `#0D0D0D` · subtle `#121212` · card/popover `#141414` ·
secondary `#1F1F1F` · muted/accent/border/input `#262626` ·
muted-foreground `#A6A6A6` · foreground `#FFFFFF` · sidebar-bg `#0F0F0F`

### Outros

- Sombras gold: `--shadow-gold` e `--shadow-gold-hover` (glow, opacidade 0.25 → 0.45)
- Tipografia: **Inter** (corpo) + **Plus Jakarta Sans** (títulos)
- Radius: `0.625rem`

### ⚠️ Três armadilhas que vêm do projeto de origem

Esta paleta foi extraída de **outro** repositório. Os problemas abaixo são
daquele código — aqui começamos limpo e **não os reproduzimos**:

1. **Tremor com gold divergente** — lá `tremor.brand.DEFAULT = #F2C94C`, diferente
   do `--gold` `#D9A520`. Se usar Tremor, alinhe os dois.
2. **`dark-tremor` ainda azul** — sobrou do tema padrão.
3. **`tertiary` referenciado e nunca definido** — `bg-tertiary` sai sem cor.

Regra: **um único token de gold**, definido uma vez.

---

## 6. Fronteiras

- Trabalhe em `front/`. **Não modifique `back/src/` nem `back/tests/`.**
- Se precisar de dado que o backend não expõe, **pare e reporte** em vez de
  contornar no front — contornar esconde o problema.
- Repositório: `https://github.com/GuilhermeSerafim/venditus-deco`, branch `main`.

---

## 7. Skills disponíveis no repositório

Em `.claude/skills/`, copiadas para lá porque nem todo agente as tem instaladas.
**Não ativam sozinhas fora do Claude Code — leia como instruções.**

1. `brainstorming/SKILL.md` — feche o design antes de codar
2. `frontend-design/SKILL.md` — ao construir
3. `ui-ux-pro-max/SKILL.md` — cor, tipografia, layout (tem bases em `data/` e
   scripts de busca em `scripts/`)

---

## 8. Estado do backend

15 de 15 tarefas · 78 testes · rodando com GPT-5.6 e loja Shopify reais.

Comandos úteis em `back/`:

| | |
|---|---|
| `python scripts/rodar_demo.py` | roda os dois casos do pitch, ponta a ponta |
| `python scripts/verificar_shopify.py --resetar` | devolve o SKU-4471 ao estado "antes" |
| `python scripts/gerar_diagrama.py` | regenera o diagrama da arquitetura |
| `python scripts/avaliar_classificador.py` | mede acurácia (20/20 hoje) |

Documentos: `README.md`, `AGENTS.md`, e o spec em
`docs/superpowers/specs/2026-08-09-venditus-mvp-design.md`.
