# Roteiro — demonstração do Venditus

**Você tem 2 minutos.** Seu colega tem 3 e carrega os números de mercado.
**Você carrega a prova.**

**Formato: vídeo gravado e editado.** Isso muda tudo para melhor — você grava
uma tomada com os três casos, corta a espera na edição, e regrava se algo der
errado. Nada acontece ao vivo.

---

## A forma da sua fala, em uma linha

> Duas buscas entram iguais → uma é corrigida, a outra é **recusada** →
> e a terceira mostra onde o sistema ainda falha.

Três atos. O segundo é o clímax. O terceiro é o que separa você de quem só
mostra o caminho feliz.

---

# ANTES DE GRAVAR

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

> Sem isso, a escrita é pulada e a busca não muda.

## 3. Limpar a tela

Abra: `http://localhost:5173/?limpar`

## ✅ Confira antes de apertar o REC

| item | esperado |
|---|---|
| a lista | três buscas, **nenhum selo** |
| indicadores | `—` · `—` · `—` |
| faixas de erro | nenhuma |
| janela | maximizada, ≥1024px de largura |

---

# COMO GRAVAR

**Uma tomada só, nesta ordem.** A ordem é causal, não estética: o caso da capa
só diagnostica o produto certo depois que o tênis foi corrigido.

```
1. tênis   → aprovar   (leva ~60-90s)
2. capa    → é recusada sozinha, você não faz nada (~40-70s)
3. mochila → aprovar   (leva ~60-90s)
```

Grave **sem falar**. A narração entra depois, por cima.

## Na edição

**Acelere as esperas de LLM, mas mostre que acelerou.** Ponha um selo `×8` no
canto durante os trechos acelerados.

> ⚠️ Corte seco nesses trechos é o que faz um jurado perguntar *"isso foi
> encenado?"*. Acelerar com marcador visível responde antes da pergunta: o
> tempo passou, nada foi montado.

Alvo: os três casos cabem em **~90 segundos** de vídeo.

---

# O ROTEIRO

## ATO 1 — o problema · 0:00 a 0:18

🎬 **Tela:** a lista das três buscas

🗣 **Fala:**

> "Essas são buscas que clientes fizeram e a loja não atendeu. **Seis mil reais
> por mês** parados em três termos.
>
> Pela Baymard, **quase metade dos sites de e-commerce não oferece nenhum
> caminho de recuperação** quando a busca não acha nada. O cliente sai calado,
> e a loja nunca fica sabendo que perdeu a venda.
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

Como é gravado, quase tudo se resolve regravando. Refaça o preparo (zerar loja
→ reiniciar servidor → `?limpar`) antes de cada tomada.

| situação | o que fazer |
|---|---|
| **narração passou de 2 min** | corte o ATO 3 inteiro. **Nunca corte a leitura das duas frases** |
| **diagnóstico no produto errado** | regrave. Se acontecer de novo, use como está e narre: 🗣 *"Saiu no produto errado. É um modelo, e modelo erra — por isso a escrita passa por aprovação humana antes de tocar no catálogo."* |
| **aviso âmbar na capa** | você pulou o reinício do servidor. Refaça o preparo |
| **faixa vermelha no topo** | o backend caiu. Suba de novo e regrave |

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
> da lista)* É o elo mais fraco da conta — o ticket tem fonte, a conversão é
> escolha nossa.

### "Esse ticket médio não vale para essa loja"
> Provavelmente não, e **não muda o argumento**. No ponto de equilíbrio o
> ticket aparece dos dois lados da divisão e cancela:
>
> ```
> devoluções que anulam o ganho = (volume × 2% × ticket) ÷ (ticket × 1,30)
>                               =  volume × 2% ÷ 1,30
> ```
>
> O ticket só serve para dar tamanho ao R$ na tela. As "cerca de duas
> devoluções por mês" dependem só do volume de busca, da conversão e dos 30%.

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

**O ticket cancela no ponto de equilíbrio** — vale saber, é o que blinda a
conta contra "esse ticket não vale para essa loja":

```
(volume × 2% × ticket) ÷ (ticket × 1,30)  =  volume × 2% ÷ 1,30
                                          =  128 × 0,02 ÷ 1,30  ≈  2
```

> Diga **"cerca de duas devoluções por mês"**, não o decimal. Igualmente fatal
> e mais honesto.

---

# FONTES — verificadas em 09/08/2026

| afirmação | fonte | situação |
|---|---|---|
| quase metade dos sites não oferece recuperação em busca vazia | [Baymard](https://baymard.com/blog/no-results-page) | ✅ confere com a página atual |
| ticket médio R$ 564,96 em 2026 | ABComm | ✅ confere |
| devolução custa até 30% acima do reembolso | [E-Commerce Brasil](https://www.ecommercebrasil.com.br/noticias/devolucoes-podem-custar-30-acima-do-valor-reembolsado-aponta-estudo) · [Mercado&Consumo](https://mercadoeconsumo.com.br/03/03/2026/ecommerce/devolucoes-no-e-commerce-elevam-custo-em-ate-30-alem-do-valor-reembolsado/) | ✅ confere |

> ⚠️ **Não use "68% de 325 sites".** Esse número circula em blogs de terceiros
> citando um benchmark antigo. A página atual da Baymard diz **"nearly 50%"**.
> Se um jurado abrir a fonte durante a apresentação, ele vê 50%.

## Munição extra para o seu colega (3 min dele)

Da mesma pesquisa, e nenhum estava no seu levantamento:

- o custo total de uma devolução vai de **20% a 65% do valor do produto**,
  conforme o segmento
- a taxa de devolução no e-commerce brasileiro fica entre **20% e 40%**
- lojas que não gerenciam logística reversa perdem **8% a 12% do faturamento
  anual**

Fonte: [Troque e Devolva — Taxa de devolução no e-commerce Brasil 2026](https://www.troqueedevolva.com.br/blog/taxa-devolucao-ecommerce-brasil-2026-dados)
