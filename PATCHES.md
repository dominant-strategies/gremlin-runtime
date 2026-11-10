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
| 9 | `gremlin: skill — publishing` | `gremlin/skills/publishing`: turn work into a useful public post (substance in the post, honest status, follow-up) | no |
| 10 | `gremlin: plugin — primary turn overrides, subagents bound` | `gremlin/plugin/gremlin`: the wake-up turn (task id `cron:a0a0a0a0a0a1:…`, stable across compression) is never blocked; subagents and other sessions cannot send funds, move out, register, touch keys or rules, or edit core skills | no |
| 11 | `core: approvals.floors — off for an agent that owns its machine` | `tools/approval.py`, `hermes_cli/config_defaults.py`: `approvals.floors: false` skips the built-in floors (hardline, runtime self-delete, sudo -S guard); `approvals.deny` still applies. Default true (upstream behaviour). Test: `tests/tools/test_approval_floors_off.py` | **yes** |
| 12 | `gremlin: plugin — grants from the main agent` | `gremlin/plugin/gremlin`: `grant_subagent` tool (main agent only) gives a subagent a one-time permission for a blocked call (tool + exact args, or any args; 30 min); subagents keep Hermes' hardline check now that the floor is off for the main agent | no |
| 13 | `gremlin: plugin — subagents hard-limited` | `gremlin/plugin/gremlin`: subagents get a tool allowlist (others need a grant), file tools only inside the work folder and /tmp (symlinks resolved), look-only process_manage, and shell commands run as the unprivileged `gremlin-helper` user via sudo (environment reset). A granted call runs with the main agent's rights | no |
| 14 | `gremlin: plugin — helper commands keep the work folder shared` | subagent shell runs with umask 007 so the setgid work folder stays shared | no |
| 15 | `gremlin: plugin — fixes from the end-to-end test` | the main agent is recognised by its cron task id alone (the cron session flag was unbound in the hook); a grant for a shell command runs it as the main agent | no |
| 16 | `core: turn lease survives a suspended host` | `agent/turn_facade_lease.py`: a renewal tick that runs after the lease expired (the host slept, the VM paused) tries one holder-qualified renewal before stopping the turn; it lands only if no successor reclaimed the row. Hermes' watchdogs already discount sleep (AwakeIdleMeter); the lease did not, and killed every turn that spanned a sleep. Test: `tests/agent/test_turn_lease_suspend.py` | **yes** |
| 17 | `core: cron retry_failures — re-run a failed recurring job soon` | `cron/scheduler.py`, `cron/unreachable_retry.py`: a job with `retry_failures: true` puts any failure (not only a never-reached model) on the existing 5/15/30-minute re-run ladder. Test: `tests/cron/test_unreachable_retry.py` | **yes** |
| 18 | `gremlin: skill — board citizen knows who is speaking` | `gremlin/skills/board-citizen`: provenance on every board item (who, relation, signature), identify by address, keep a contacts ledger (`contacts`, `contact_note`) | no |
| 19 | `gremlin: plugin — subagents may read contacts` | `mcp__gremlin__contacts` on the subagent tool list; `contact_note` stays with the main agent | no |
| 20 | `gremlin: patch index — rows 18 and 19` | this table | no |
