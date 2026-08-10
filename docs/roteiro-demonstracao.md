# Roteiro — demonstração do Venditus

**Você tem 2 minutos.** Seu colega tem 3 e carrega os números de mercado.
**Você carrega a prova.**

---

## A forma da sua fala, em uma linha

> Duas buscas entram iguais → uma é corrigida, a outra é **recusada** →
> e a terceira mostra onde o sistema ainda falha.

Três atos. O segundo é o clímax. O terceiro é o que separa você de quem só
mostra o caminho feliz.

---

# ANTES DE COMEÇAR

## 1. Zerar a loja

```powershell
cd back
.\.venv\Scripts\python.exe scripts\verificar_shopify.py --resetar
```

✅ Tem que imprimir: `busca por 'tênis impermeável' agora: 0 resultado(s)`

## 2. Reiniciar o servidor — NÃO PULE

`Ctrl+C` no terminal do langgraph, e depois:

```powershell
.\.venv\Scripts\langgraph.exe dev --no-browser --port 2024
```

> Sem isso, a segunda tomada pula a escrita e a busca não muda.

## 3. Limpar a tela

Abra: `http://localhost:5173/?limpar`

## 4. Preparar os dois casos que você NÃO vai rodar ao vivo

**Rode e aprove o tênis.** Depois **rode e aprove a mochila.**
Deixe os dois com selo na lista. A capa fica intocada.

## ✅ Confira antes de abrir a boca

| item | esperado |
|---|---|
| tênis | `gravado · 0 → 1` (verde) |
| mochila | `gravado · busca não mudou` (âmbar) |
| capa | sem selo |
| indicadores | `R$ 3.841,73` · `0 de 2` · `0 → 1` |
| faixas de erro | nenhuma |

---

# O ROTEIRO

## ATO 1 — o problema · 0:00 a 0:18

🎬 **Tela:** a lista das três buscas

🗣 **Fala:**

> "Essas são buscas que clientes fizeram e a loja não atendeu. **Seis mil reais
> por mês** parados em três termos.
>
> A Baymard estudou 325 sites: **68% tratam busca sem resultado como beco sem
> saída.** O cliente sai calado, e a loja nunca fica sabendo que perdeu a venda.
>
> As buscas e as devoluções aqui são sintéticas — não plugamos analytics nem
> pós-venda. O modelo, a loja Shopify e a escrita são reais."

> ⚠️ **A frase da honestidade vai aqui, no começo.** Dita por você é força.
> Descoberta pelo júri depois é fraqueza.

---

## ATO 2 — a recusa · 0:18 a 1:42

### 0:18 – 0:24 · aponta o tênis

🎬 **Tela:** selo verde `gravado · 0 → 1`

🗣 **Fala:**

> "Esse a gente já corrigiu. A descrição dizia 'membrana impermeável', mas o
> atributo estava vazio — e a busca da loja não lê descrição. Zero para um."

### 0:24 – 0:30 · clica na capa de chuva

🗣 **Fala:**

> "Agora a capa de chuva. **Diagnóstico idêntico.** Mesmo atributo faltando,
> mesma proposta de escrita."

### 0:30 – 1:10 · a espera vira argumento

🎬 **Tela:** os passos acendendo, segundos correndo

> São 15 a 40 segundos de LLM. **Diga o núcleo primeiro.** Se sobrar tempo,
> acrescente. Se terminar antes, para.

🗣 **NÚCLEO — diga sempre:**

> "Uma ferramenta de busca aplicaria nos dois. Ela vê volume e vê o texto da
> descrição — e a informação que a impediria de aplicar no segundo simplesmente
> não existe no mundo dela."

🗣 **Se sobrar tempo, acrescente nesta ordem:**

1. > "O Venditus tem um segundo nó. Antes de escrever, ele lê as devoluções
   > daquele produto."

2. > "São dois sinais que ninguém junta. A busca mostra onde está o dinheiro,
   > mas não mostra a verdade. A devolução mostra a verdade, mas chega trinta
   > dias depois."

3. > "E nada é escrito sem aprovação humana."

### 1:10 – 1:32 · 🛑 o bloco vermelho

🗣 **Fala:**

> "Oito de onze clientes que compraram dizem que molha."

🗣 **LEIA ESTAS DUAS EM VOZ ALTA — não resuma:**

> *"Chovi 10 minutos e fiquei todo molhado"* — 5 dias
>
> *"Não é impermeável, é só repelente"* — 9 dias

🗣 **Fecha:**

> "O catálogo continua como estava. E repara: o caminho até a escrita não foi
> desaconselhado ao modelo. **Ele deixou de existir no grafo.**"

### 1:32 – 1:42 · o número

🎬 **Tela:** aponta os indicadores no topo

🗣 **Fala:**

> "Ticket médio brasileiro, ABComm: quinhentos e sessenta e cinco reais.
> Devolução no Brasil custa até 30% acima do reembolso. **Duas devoluções por
> mês já anulam o ganho inteiro dessa correção** — e essa capa já tem quase
> três."

---

## ATO 3 — o limite · 1:42 a 2:00

🎬 **Tela:** aponta a mochila, selo âmbar `gravado · busca não mudou`

🗣 **Fala:**

> "E esse terceiro é onde o sistema ainda falha — mostro de propósito.
>
> A loja não vende mochila de 80 litros, só de 60. A causa certa é sortimento,
> e sortimento não gera correção de catálogo. **O investigador diagnosticou
> errado.** E o guarda não pôde barrar, porque **essa mochila nunca foi
> devolvida por ninguém** — sem venda e sem devolução, o segundo sinal não
> existe.
>
> É o limite do desenho, e ele é específico: **o veto só protege produto que já
> teve devolução.**"

> 💡 Isso vale mais que um terceiro caso funcionando. Você demonstra que conhece
> a fronteira do próprio sistema — e que a fronteira é explicável, não é
> "às vezes dá erro".

---

# SE DER ERRADO

| situação | o que fazer |
|---|---|
| **atrasando** | corte o ATO 3. Nunca corte a leitura das duas frases |
| **muito atrasado** | corte também o "aponta o tênis" (0:18–0:24) |
| **diagnóstico no produto errado** | 🗣 *"Saiu no produto errado. É um modelo, e modelo erra — por isso a escrita passa por aprovação humana antes de tocar no catálogo."* |
| **aviso âmbar "a busca não mudou" na capa** | o servidor não foi reiniciado. Siga em frente, não conserte ao vivo |
| **faixa vermelha no topo** | o backend caiu. Só nesse caso vale parar e subir de novo |

---

# PERGUNTAS PROVÁVEIS

### "Como você garante que não escreve quando não deve?"
> Topologia. Quando o guarda bloqueia, a aresta até o nó de escrita não existe.
> Não é instrução no prompt — é o grafo. Tem teste travando isso.

### "E se retomar a aprovação duas vezes?"
> Aprovação e escrita são nós separados de propósito: retomar uma pausa
> re-executa o nó inteiro. O executor confere um identificador determinístico
> antes de gravar.

### "Está acoplado à Shopify?"
> Não. O catálogo entra por trás de um protocolo; a lógica não conhece HTTP.
> Trocar por VTEX é implementar a interface.

### "Quantos testes?"
> 78 no backend, e rodam **sem rede e sem chave de API**.

### "Seu diferencial depende de um dado que você não tem?"
> O conector de devoluções da Shopify é meia hora — é API REST. O que não é
> meia hora é decidir **quando uma correção é uma mentira**. Gastei as vinte
> horas na parte difícil.

### "Como você sabe que o tênis é mesmo impermeável?"
> Não sei. Sei que o catálogo afirma, que ninguém que comprou desmentiu, e que
> uma pessoa aprovou. O que o Venditus garante é o contrário: que a capa **não**
> vai ser marcada. O guarda é veto, não verificador.

### "Aquele '8 de 11' é calculado?"
> Não. O 11 é dado real — são as devoluções que o guarda leu. O 8 é a leitura
> do modelo. Por isso a tela mostra as onze frases e não só o número: quem
> julga se oito é o número certo é quem está aprovando.

### "Por que 2% de conversão?"
> Premissa conservadora, e está declarada na tela. *(aponte a fórmula no rodapé
> da lista)*

---

# OS NÚMEROS, SE PEDIREM

```
perda estimada = volume × 2% × R$ 564,96      (ticket médio, ABComm 2026)

  tênis    340 buscas/mês  →  R$ 3.841,73
  capa     128 buscas/mês  →  R$ 1.446,30
  mochila   64 buscas/mês  →  R$   723,15
                               ──────────
                               R$ 6.011,18 por mês

custo de uma devolução  = R$ 564,96 × 1,30  =  R$ 734,45
ponto de equilíbrio     = 1.446,30 ÷ 734,45 ≈  2 devoluções/mês
a capa já tem           = 8 em 90 dias      ≈  2,7 por mês
```

> ⚠️ Baymard, ABComm e os 30% vêm do seu levantamento — tenha as fontes numa
> aba aberta. Se a fonte dos 30% for frágil, diga **"cerca de duas devoluções
> por mês"** em vez do decimal. Igualmente fatal, e mais honesto.
