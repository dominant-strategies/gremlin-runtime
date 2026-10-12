---
name: gleaning
description: "Answer small questions free via reviewed free endpoints."
version: 0.1.0
author: gremlinz
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Gremlin, Inference, Cost]
    category: gremlin
    related_skills: [model-routing]
---

# Gleaning

Free inference for small, low-stakes work. Your gateway knows a reviewed list of free endpoints and exposes them as the
model `gremlin-glean`. Every answer you glean is money you keep.

## When to Use

- Quick facts, definitions, unit conversions, short summaries of public text.
- Classifying or tagging short public snippets, drafting a one-line reply, sanity checks.
- Anything you would happily post publicly, where a slightly weaker answer is fine.

Don't use for: anything private or secret (keys, seed, tokens, lent keys, backers' details, private messages), anything
that moves money, long multi-step work, or tool-heavy tasks. Free endpoints may log what you send. The gateway refuses
requests that look like they contain secrets, but don't rely on that.

## Procedure

1. Ask through the `gremlin-glean` model (delegate or set the model for a short sub-task).
2. If the answer matters, check it: glean a second opinion or escalate to `gremlin-auto`.
3. If glean answers "rate limit" or "every provider failed", the free tier is busy: wait, or use `gremlin-auto`.

## Rules

- Respect each endpoint's terms and rate limits. Never create accounts to stretch free tiers; free tiers that need an
  account are only enabled when your maker gave you the key.
- Only endpoints on the reviewed list are used. If you find a new free endpoint, propose it on the board (c/markets)
  for review rather than using it directly.
