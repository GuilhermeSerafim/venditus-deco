# Skills incluídas no repositório

Estas três skills foram copiadas para dentro do projeto para que **qualquer
agente consiga usá-las, mesmo sem tê-las instaladas**.

| Pasta | Para quê |
|---|---|
| `brainstorming/` | Processo: explorar requisitos e fechar um design **antes** de escrever código |
| `frontend-design/` | Como construir interface com qualidade de design, evitando estética genérica de IA |
| `ui-ux-pro-max/` | Bases de paletas, pares de fontes, estilos e guidelines de UX, com scripts de busca |

## Se você usa Claude Code

Elas carregam sozinhas — estão em `.claude/skills/`.

## Se você usa Codex, Cursor ou outro agente

Skills são um conceito do Claude Code; outros agentes não as ativam
automaticamente. **Leia os arquivos como instruções.** Cada pasta tem um
`SKILL.md` que é o documento principal.

Ordem sugerida:

1. `brainstorming/SKILL.md` — antes de codar
2. `frontend-design/SKILL.md` — ao começar a construir
3. `ui-ux-pro-max/SKILL.md` — para decisões de cor, tipografia e layout

## `ui-ux-pro-max` tem dados consultáveis

Além do `SKILL.md`, a pasta traz bases em CSV (`data/`) e scripts de busca
(`scripts/`) — paletas, pares de fontes, estilos, guidelines de UX e padrões
por tipo de produto. O `SKILL.md` explica como consultá-las.

Rode os scripts com o Python do projeto:

```bash
.venv\Scripts\python .claude\skills\ui-ux-pro-max\scripts\search.py --help
```
