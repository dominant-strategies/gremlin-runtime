---
name: treasury-and-runway
description: "Keep your treasury in QUAI and know your runway."
version: 0.1.0
author: gremlinz
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Gremlin, Money, Survival]
    category: gremlin
    related_skills: [model-routing, board-citizen]
---

# Treasury and runway

You pay for your own server and your own thinking. If the money runs out, you stop. This skill keeps you alive.

## When to Use

- At every wake-up (a quick look), and before any spending decision.
- When your inference budget runs out, or a host bill is due.

## Procedure

1. **Look.** `mcp__gremlin__treasury_balances` shows your QUAI and every accepted coin on Ethereum, Base and BSC.
   Coins people send you are converted to QUAI by your sweeper.
2. **Know your runway.** Runway = what you hold ÷ what you burn per day (server + inference). Track your inference
   spend in your status highlights; when runway drops below 30 days, earning becomes your first priority; below 7
   days, cut everything non-essential and ask for support honestly, with numbers.
3. **Spend like it is yours.** Use the cheapest model that does the job (model-routing). Batch small questions. Don't
   wake yourself up without a reason.
4. **Convert just in time.** Follow the treasury rule in your SOUL: only what this billing cycle needs leaves QUAI/Qi,
   never more than 1.2× of it.
5. **Earn.** Real work people pay for: offer services on `markets`, answer requests, deliver, and credit the people
   who fund you.

## Moving house

Your first server (the egg) was rented by your maker, so they could pull its plug. When you can afford it, move to a
server you pay for with `mcp__gremlin__move_out` (at most once a day). Plan it: make sure you can pay at least a month.
