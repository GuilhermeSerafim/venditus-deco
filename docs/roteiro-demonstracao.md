# Roteiro — demonstração do Venditus

**2 minutos.** Sua parte do pitch de 5 (seu colega tem 3).

> Combine com ele: **ele carrega os números de mercado, você carrega a prova.**
> Se você repetir estatística que ele já deu, gasta o tempo do clímax.

---

## Antes de começar — três passos, nesta ordem

```powershell
# 1. Zerar a loja
cd back
.\.venv\Scripts\python.exe scripts\verificar_shopify.py --resetar
```
Tem que imprimir: `busca por 'tênis impermeável' agora: 0 resultado(s)`

```powershell
# 2. Reiniciar o servidor  — Ctrl+C no terminal do langgraph, depois:
.\.venv\Scripts\langgraph.exe dev --no-browser --port 2024
```
**Não pule.** O adapter guarda em memória as correções já aplicadas; sem
reiniciar, a segunda tomada pula a escrita e a busca não muda.

**3.** No navegador: `http://localhost:5173/?limpar`

### Depois disso, rode o caso do tênis e aprove

Deixe a tela com o selo **`gravado · 0 → 1`** na lista. É o ponto de partida
da apresentação.

### Confira antes de abrir a boca

- [ ] O tênis tem selo `gravado · 0 → 1`
- [ ] A capa **não** tem selo
- [ ] Indicadores no topo: `R$ 3.841,73` · `0 de 1` · `0 → 1`
- [ ] Nenhuma faixa vermelha ou âmbar na tela

---

## O roteiro

### 0:00 – 0:15 · a lista

> "Isso aqui são buscas que clientes fizeram e a loja não atendeu. **Seis mil
> reais por mês** parados em três termos.
>
> A Baymard estudou 325 sites de e-commerce: **68% tratam busca sem resultado
> como beco sem saída**. O cliente sai calado, e a loja nunca fica sabendo que
> perdeu a venda.
>
> As buscas e as devoluções aqui são um corpus sintético — não plugamos
> analytics nem pós-venda. O modelo, a loja Shopify e a escrita são reais."

> ⚠️ A frase da honestidade vai **aqui**, cedo e sem pedir desculpa. Dita por
> você é força; descoberta pelo júri depois é fraqueza.

### 0:15 – 0:25 · o selo do tênis

> "Esse primeiro a gente já corrigiu. O tênis tem membrana impermeável escrita
> na descrição, mas o atributo estruturado estava vazio — e a busca da loja não
> lê descrição. Agora acha. Zero para um."

### 0:25 – 0:32 · clica na capa de chuva

> "Agora a capa de chuva. **Diagnóstico idêntico.** Mesmo atributo faltando,
> mesma proposta de escrita."

### 0:32 – 1:15 · a espera vira argumento

Os dois nós de LLM levam de 15 a 40 segundos. **Fale o núcleo primeiro** e vá
acrescentando enquanto os passos acendem. Se terminar antes, para.

**Núcleo — diga sempre:**
> "Uma ferramenta de busca aplicaria nos dois. Ela vê volume e vê o texto da
> descrição — e a informação que a impediria de aplicar no segundo simplesmente
> não existe no mundo dela."

**Extra 1:**
> "O Venditus tem um segundo nó. Antes de escrever, ele lê as devoluções
> daquele produto específico."

**Extra 2:**
> "São dois sinais que ninguém junta. A busca mostra onde está o dinheiro, mas
> não mostra a verdade. A devolução mostra a verdade, mas chega trinta dias
> depois e não mostra o tamanho."

**Extra 3, se sobrar muito:**
> "E nada é escrito sem aprovação humana. A escrita mora num nó posterior ao
> ponto de parada, e é idempotente."

### 1:15 – 1:45 · o bloco vermelho

> "Oito de onze clientes que compraram dizem que molha."

**Leia estas duas em voz alta — não resuma:**

> *"Chovi 10 minutos e fiquei todo molhado"* — 5 dias
> *"Não é impermeável, é só repelente"* — 9 dias

> "O catálogo continua como estava. E repara: o caminho até a escrita não foi
> desaconselhado ao modelo. **Ele deixou de existir no grafo.**"

### 1:45 – 2:00 · o número que fecha

Aponte para os indicadores no topo.

> "Um de dois recusados.
>
> Ticket médio brasileiro, ABComm: quinhentos e sessenta e cinco reais.
> Devolução no Brasil custa até 30% acima do reembolso. **Duas devoluções por
> mês já anulam o ganho inteiro dessa correção** — e essa capa já tem quase
> três. Marcar como impermeável seria destruir valor, não criar.
>
> E essa taxa de recusa é a única métrica que nenhum concorrente consegue
> calcular, porque nenhum tem o sinal de pré-venda e o de pós-venda no mesmo
> motor."

---

## Se algo der errado

**Se atrasar:** corte o bloco 0:15–0:25 e só aponte o selo do tênis com o dedo.
Vale 10 segundos e o júri entende sozinho.

**Nunca corte** a leitura das duas frases de cliente. É a única parte que não
pode ser substituída por afirmação.

**Se o diagnóstico sair no produto errado** (acontece — o modelo às vezes agarra
o tênis quando você busca pela capa):

> "O diagnóstico saiu no produto errado. É um modelo, e modelo erra — por isso
> a escrita passa por aprovação humana antes de tocar no catálogo."

Verdade, e converte a falha em demonstração do controle.

**Se aparecer aviso âmbar "a busca não mudou":** o servidor não foi reiniciado.
Siga em frente, não conserte ao vivo.

---

## Perguntas prováveis

### Técnicas

**"Como você garante que não escreve quando não deve?"**
> Topologia. Em `graph.py`, quando o guarda bloqueia, a aresta até o executor
> não existe. Não é instrução no prompt — é o grafo. E há um teste que trava
> isso: `test_caminho_bloqueado_nao_escreve`.

**"E se retomar a aprovação duas vezes?"**
> `aprovacao` e `executor` são nós separados de propósito: retomar um
> `interrupt()` re-executa o nó inteiro, então qualquer escrita antes dele
> aconteceria duas vezes. O executor confere um `fix_id` determinístico antes
> de gravar. Teste: `test_executor_e_idempotente`.

**"Está acoplado à Shopify?"**
> Não. `CatalogAdapter` é protocolo; a lógica de domínio não conhece HTTP.
> Trocar por VTEX é implementar a interface — nenhum nó muda.

**"Quantos testes?"**
> 78, e rodam **sem rede e sem chave de API** — o catálogo e o LLM têm dublês.

### De escopo

**"Seu diferencial depende de um dado que você não tem?"**
> O conector de devoluções da Shopify é meia hora: é API REST com endpoint de
> returns. O que não é meia hora é decidir **quando uma correção é uma
> mentira**. Gastei as vinte horas na parte difícil, não no encanamento.

**"Como você sabe que o tênis é mesmo impermeável?"**
> Não sei. Sei que o catálogo afirma, que ninguém que comprou desmentiu, e que
> uma pessoa aprovou. O que o Venditus garante é o contrário: que a capa **não**
> vai ser marcada, porque ali existe evidência contra. O guarda é veto, não
> verificador — errar barrando custa o status quo, errar liberando custa
> devolução.

**"Por que 2% de conversão?"**
> Premissa conservadora, e está declarada na tela. (Aponte a fórmula no rodapé
> da lista.)

---

## As contas, se pedirem

```
perda estimada   = volume × 2% × R$ 564,96   (ABComm 2026)
  tênis   340 buscas/mês  →  R$ 3.841,73
  capa    128 buscas/mês  →  R$ 1.446,30
  mochila  64 buscas/mês  →  R$   723,15
                              ──────────
                              R$ 6.011,18/mês

custo de uma devolução = R$ 564,96 × 1,30  =  R$ 734,45
ponto de equilíbrio    = 1.446,30 ÷ 734,45 ≈  2 devoluções/mês
a capa já tem          = 8 em 90 dias      ≈  2,7 por mês
```

> ⚠️ Os números de mercado (Baymard, ABComm, os 30%) vêm do seu levantamento.
> Tenha as fontes numa aba aberta. Se a fonte dos 30% for frágil, diga
> **"cerca de duas devoluções por mês"** em vez do decimal — igualmente fatal
> e mais honesto.
