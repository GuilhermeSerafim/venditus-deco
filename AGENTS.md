# OPHION — instruções para agentes

## O que é

Um agente que lê **buscas sem resultado** de um e-commerce, diagnostica a causa no
catálogo, e **recusa a correção quando o pós-venda a contradiz**. Só escreve no
catálogo após aprovação humana.

A tese em uma frase: *busca dá volume mas não dá verdade; devolução dá verdade mas
não dá volume. Juntar os dois permite distinguir uma correção de uma mentira.*

**Documentos de referência — leia antes de codar:**
- Spec: `docs/superpowers/specs/2026-08-09-ophion-mvp-design.md`
- Plano: `docs/superpowers/plans/2026-08-09-ophion-backend.md`

O plano tem 15 tarefas em TDD, com código completo em cada passo. Siga na ordem.

**Contexto de prazo:** hackathon, 20h totais. Prefira a solução que funciona hoje
à que é elegante amanhã. Mas nenhuma das regras abaixo é candidata a atalho.

---

## Regras inegociáveis

Cada uma abaixo é uma decisão tomada com motivo. Um agente que não conhece o motivo
tende a desfazê-la por reflexo. **Não desfaça sem confirmar com o Guilherme.**

### 1. Nunca passar `temperature`, `top_p` ou `top_k` para o modelo

Praticamente todo exemplo de LangGraph escreve `ChatOpenAI(temperature=0)`. Nos
modelos GPT-5.x de raciocínio esses parâmetros são aceitos **apenas** com
`reasoning_effort="none"` — com qualquer outro nível a chamada erra.

O controle correto é `reasoning_effort`. Se precisar de saída mais determinística,
use `with_structured_output()`, que já é o padrão do projeto.

```python
# certo
ChatOpenAI(model="gpt-5.6-terra", reasoning_effort="medium")

# errado — quebra
ChatOpenAI(model="gpt-5.6-terra", temperature=0)
```

Verificação: `git grep -n temperature -- src/` deve retornar vazio.

### 2. A escrita fica em nó separado, depois do `interrupt()`, e é idempotente

Retomar de um `interrupt()` **re-executa o nó inteiro desde o início**. Qualquer
escrita ou chamada cobrada colocada antes do `interrupt()` acontece duas vezes.

Por isso `aprovacao` (que chama `interrupt()`) e `executor` (que escreve) são nós
distintos, e o `executor` checa `fix_id` antes de gravar.

**Não colapse os dois "para simplificar".** O sintoma é escrita duplicada no
catálogo — ao vivo, durante a gravação do vídeo.

### 3. `langchain-openai >= 1.4.1`

Abaixo dessa versão o parâmetro `reasoning_effort` é aceito e **ignorado em
silêncio**. Não afrouxe o pin.

### 4. Um modelo só nos dois nós de LLM

`gpt-5.6-terra` no investigador (`reasoning_effort="medium"`) e no guarda
(`reasoning_effort="high"`).

Não "otimize" custo dividindo entre `sol` e `luna`. A demo custa centavos — dividir
modelo economiza troco, adiciona configuração e arrisca a qualidade justamente no
guarda, que é o nó onde errar custa o pitch.

### 5. A busca casa contra título e atributos estruturados — nunca contra a descrição

Em `FakeCatalogAdapter._casa_token`. **Isso não é um bug, é a premissa do produto:**
o texto livre existe e mesmo assim o item não é encontrável. Se a busca passar a
ler a descrição, o caso de demonstração deixa de existir.

### 6. Fora de escopo — não implemente

Aparecem na narrativa do pitch e **não** devem virar código nesta rodada:

- Caminho de escrita pós-venda → PDP. O corpus de devolução alimenta **apenas** o
  nó guarda.
- Camada de lote / anomalia temporal e regional.
- Adapter VTEX (a interface existe; a implementação não).
- Cron, autenticação, deploy, multi-loja.
- Front-end — rodada seguinte.

---

## Dois testes que não podem ser enfraquecidos

Se um deles falhar, **conserte o código, nunca a asserção**. São a prova da tese:

| Teste | O que prova |
|---|---|
| `test_caminho_bloqueado_nao_escreve` | O guarda impede a escrita quando o pós-venda contradiz |
| `test_executor_e_idempotente` | Retomar o interrupt não duplica a escrita |

Se as outras 13 tarefas quebrarem e essas duas passarem, ainda há pitch.

---

## Ambiente

**Use `python`, não `py`.** O `python` da máquina é 3.12.10. O launcher `py`
aponta para 3.14, que ainda não tem wheel para várias dependências — você cairia
em compilação de C sem motivo.

```bash
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
.venv\Scripts\pytest -v
```

Variáveis em `.env` (já no `.gitignore`):

```
OPENAI_API_KEY=sk-...
# Opcionais — sem eles o projeto usa o catálogo fake automaticamente
SHOPIFY_STORE_DOMAIN=...
SHOPIFY_ADMIN_TOKEN=...
SHOPIFY_API_VERSION=...
```

**Todos os testes rodam sem chave e sem internet** — usam `FakeLLM` e
`FakeCatalogAdapter`. Só a Task 13 (montar `app.py`) e a Task 15 (avaliar acurácia)
precisam da chave da OpenAI; só a Task 12 precisa da Shopify.

---

## Convenções

- **Código, identificadores e docstrings em português.** O projeto inteiro é assim;
  mantenha.
- Mensagens de commit em português, no imperativo.
- A lógica de domínio (`nodes.py`, `metrics.py`, `estimate.py`) **não conhece HTTP
  nem Shopify**. Acesso a catálogo passa pelo protocolo `CatalogAdapter`. É o que
  torna a troca para VTEX uma implementação, não um refactor.
- LLMs são **injetados** nos construtores de nó (`criar_investigador(llm, catalogo)`).
  Não instancie `ChatOpenAI` dentro de um nó — isso torna o nó não testável.

---

## Quando algo não bater com o plano

O plano foi escrito num ambiente diferente. A API do LangGraph muda entre versões.

A **Task 0** existe exatamente para isso: ela verifica a superfície de API instalada
antes de qualquer coisa ser construída em cima. **Rode-a primeiro.** Se um import
falhar ali, ajuste o plano inteiro antes de seguir — não descubra na Task 10.

Divergências conhecidas e prováveis:
- `interrupt` / `Command` podem estar em `langgraph.types` ou `langgraph.constants`
- `SqliteSaver.from_conn_string` pode exigir uso como context manager
- A alternativa ao `interrupt()` é `compile(interrupt_before=["executor"])`,
  retomando com `invoke(None, config)`

Ajustar a chamada do framework é esperado. Ajustar as regras inegociáveis acima
não é.
