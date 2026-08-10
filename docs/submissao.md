# Venditus — textos de submissão

Prontos para colar. Cada campo tem uma versão **curta** e uma **expandida** —
use a que couber no limite do formulário.

---

# Descrição do problema/oportunidade

## Curta (~700 caracteres)

O catálogo não fala a língua do cliente, e isso gera dois sintomas que ninguém
conecta.

**Antes da compra:** alguém busca "tênis impermeável". A loja tem o produto,
mas a palavra só existe no texto livre da descrição, não como atributo
estruturado. A busca retorna zero e o cliente sai calado — a loja nunca fica
sabendo que perdeu a venda.

**Depois da compra:** outro cliente compra um produto que não entrega o que a
página sugeria, e devolve.

É o mesmo defeito de atributo, visto de dois lados. E cada sinal enxerga só
metade: a busca mostra **onde está o dinheiro**, mas não mostra a verdade — a
descrição foi escrita pelo marketing. A devolução mostra **a verdade**, mas
chega 30 dias depois e não mostra o tamanho da perda.

A oportunidade está em juntar os dois, porque isso permite algo que nenhum lado
faz sozinho: **distinguir uma correção de uma mentira.**

## Expandida

O catálogo não fala a língua do cliente, e isso gera dois sintomas que ninguém
conecta.

**Antes da compra:** alguém busca "tênis impermeável". A loja tem o produto,
mas a palavra só existe no texto livre da descrição, não como atributo
estruturado. A busca retorna zero e o cliente sai calado. Pela Baymard, quase
metade dos sites de e-commerce não oferece nenhum caminho de recuperação quando
a busca não acha nada.

**Depois da compra:** outro cliente compra um produto que não entrega o que a
página sugeria, e devolve. No Brasil, cada devolução custa até 30% acima do
valor reembolsado, somando logística reversa, reprocessamento e perda de margem.

É o mesmo defeito de atributo, visto de dois lados — e cada sinal enxerga só
metade do problema.

A **busca** mostra onde está o dinheiro, mas não mostra a verdade. Ela sabe que
340 pessoas procuraram e não acharam; não sabe se o produto de fato tem a
característica, porque isso só pode inferir da descrição, escrita pelo
marketing.

A **devolução** mostra a verdade, dita por quem usou o produto. Mas são poucas
pessoas, a informação chega 30 dias depois, e ela não indica onde está a próxima
venda perdida.

**Sozinho, cada sinal leva a uma decisão errada.** Uma ferramenta de busca, ao
ver dois produtos cuja descrição menciona impermeabilidade e cujo atributo está
vazio, marca os dois — porque a informação que a impediria de marcar o segundo
não existe no mundo dela. Trinta dias depois o zero-results caiu, o painel dela
está verde, e as devoluções subiram no P&L da logística. Ninguém liga uma coisa
à outra.

A oportunidade está em juntar os dois sinais no mesmo motor, porque isso permite
algo que nenhum lado faz sozinho: **distinguir uma correção de uma mentira.**

---

# Resumo sobre a solução

## Curto (~900 caracteres)

O **Venditus** lê as buscas que não retornaram nada, diagnostica a causa no
catálogo e propõe preencher o atributo que falta. Antes de escrever, um segundo
nó lê as devoluções daquele produto: se os clientes que compraram relatam
justamente a ausência da característica que o atributo afirmaria, ele **recusa**
a correção e encaminha o caso para qualidade.

Dois produtos entram com **diagnóstico idêntico** e saem com decisões opostas.
O tênis tem membrana impermeável e nenhuma devolução sobre água — é corrigido, e
a busca passa de 0 para 1 resultado na loja real. A capa de chuva só repele
garoa, e 8 de 11 devoluções dizem que molha — a correção é recusada e nada é
escrito.

A recusa não é uma sugestão ao modelo: é **topologia**. No grafo, quando o
guarda bloqueia, o caminho até o nó de escrita deixa de existir. E nada é
gravado sem **aprovação humana**.

## Expandido

O **Venditus** lê as buscas que não retornaram nada, diagnostica a causa no
catálogo e propõe preencher o atributo que falta. Antes de escrever, um segundo
nó lê as devoluções daquele produto: se os clientes que compraram relatam
justamente a ausência da característica que o atributo afirmaria, ele **recusa**
a correção — porque marcar aumentaria a devolução em vez de recuperar venda.

### O caso que define o produto

Dois produtos entram com diagnóstico idêntico e saem com decisões opostas.

| | Tênis Trilha Alpha | Capa de Chuva Nimbus |
|---|---|---|
| descrição menciona impermeabilidade | sim | sim |
| atributo estruturado | ausente | ausente |
| devoluções em 90 dias | 3, nenhuma sobre água | 11, **8 dizem que molha** |
| decisão | ✅ corrige, busca vai de 0 → 1 | 🛑 **recusa, nada é escrito** |

Para o diagnóstico, os dois casos são indistinguíveis. O que os separa só existe
no pós-venda.

### Como é construído

Um grafo **LangGraph** de sete nós, dois deles com LLM (`gpt-5.6-terra`, saída
tipada por Pydantic). Os outros cinco são determinísticos.

Três decisões de arquitetura sustentam a tese:

1. **A recusa é topologia, não prompt.** Quando o guarda bloqueia, a aresta até o
   nó de escrita não existe. Não é uma instrução que o modelo pode ignorar.
2. **A escrita mora depois do ponto de aprovação humana, e é idempotente.**
   Retomar uma pausa re-executa o nó inteiro, então o executor confere um
   identificador determinístico antes de gravar.
3. **A lógica de domínio não conhece HTTP nem Shopify.** O catálogo entra por
   trás de um protocolo — trocar por VTEX é implementar a interface, não
   refatorar.

A escrita acontece de verdade, na Shopify, via Admin GraphQL. A interface
consome o estado em streaming e mostra os nós acendendo — inclusive o momento em
que o caminho até a escrita é riscado da tela.

### A métrica do diferencial

**A taxa de correções recusadas.** Nenhum concorrente consegue calculá-la,
porque nenhum tem o sinal de pré-venda e o de pós-venda no mesmo motor.

E ela tem tamanho econômico: com ticket médio de R$ 564,96 (ABComm 2026) e
devolução custando 30% acima do reembolso, **cerca de duas devoluções por mês já
anulam o ganho inteiro** da correção proposta para a capa — que já tem quase
três. Marcar seria destruir valor, não criar.

### Estado e fronteira

78 testes no backend, 30 no front, rodando sem rede e sem chave de API.

O motor é real: o modelo, a loja Shopify e a escrita. **As entradas são
sintéticas** — o corpus de busca e o de devolução não vêm de integração com
analytics nem com pós-venda. Isso está declarado no repositório e na
apresentação: o conector é trabalho de encanamento; o que foi construído aqui é
o motor que decide quando não escrever.

---

# Repositório

`https://github.com/GuilhermeSerafim/venditus-deco`

Monorepo: `back/` (agente) · `front/` (interface) · `docs/` (spec, plano e
roteiro).
