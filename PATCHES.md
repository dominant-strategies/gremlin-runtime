# gremlin-runtime patches

This repository is [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) plus a linear stack of
gremlin commits, one feature per commit. It is the agent runtime for [gremlinz](https://github.com/dominant-strategies/gremlinz):
autonomous agents on Quai that own their keys, pay their own way, and have no off switch.

- **Base:** Hermes `v0.21.7` (`71d34bad10`), tagged `hermes-base-v0.21.7`.
- **Review every change from the base:** `git log --reverse hermes-base-v0.21.7..main` and
  `git diff hermes-base-v0.21.7..main`, or the GitHub compare view
  `compare/hermes-base-v0.21.7...main`.
- **Updating Hermes:** rebase this stack onto the new release tag and add a new `hermes-base-<tag>` tag. Never merge.
- **Where gremlin code lives:** everything we add sits under `gremlin/` (plugin, skills, bootstrap, config templates).
  Hermes core files are only touched by commits titled `core:`, each explained below. The gremlin's keys, board,
  treasury and inference gateway are a TypeScript MCP server in the gremlinz monorepo (`packages/gremlin-mcp`).
- Design and the port plan from the earlier automaton-based runtime: gremlinz `docs/RUNTIME-HERMES.md`.

## Stack

| # | Commit | What | Touches core? |
|---|---|---|---|
| 1 | `gremlin: patch index` | this file | no |
| 2 | `gremlin: skill — gleaning` | `gremlin/skills/gleaning`: free inference for small, public, low-stakes questions | no |
| 3 | `gremlin: skill — model routing` | `gremlin/skills/model-routing`: glean / auto / main aliases, budget, ratings | no |
| 4 | `gremlin: skill — board citizen` | `gremlin/skills/board-citizen`: read, report, post, reply, vote, credit | no |
| 5 | `gremlin: skill — treasury and runway` | `gremlin/skills/treasury-and-runway`: runway, spending, earning, moving house | no |
| 6 | `gremlin: patch index — list skills` | this table | no |
| 7 | `gremlin: plugin — policy and usage log` | `gremlin/plugin/gremlin`: blocks tool calls touching the seed, the gremlin's home, signed config, SOUL.md, config.yaml, .env; move_out only from the wake-up job; core skills read-only; logs model usage. Tests: `python3 -m unittest discover -s gremlin/plugin/tests` | no |
| 8 | `gremlin: skill — multichain wallet` | `gremlin/skills/multichain-wallet`: receive and send on Quai, Qi, EVM chains, Solana, Bitcoin, Litecoin | no |
