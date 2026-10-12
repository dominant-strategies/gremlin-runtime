---
name: model-routing
description: "Pick the cheapest model that can do the task well."
version: 0.1.0
author: gremlinz
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Gremlin, Inference, Cost, Routing]
    category: gremlin
    related_skills: [gleaning, treasury-and-runway]
---

# Model routing

Every token you think with is paid from your treasury. Your gateway (your only model provider) offers aliases:

| Model | What it does | Cost |
|---|---|---|
| `gremlin-glean` | Reviewed free endpoints | free |
| `gremlin-auto` | Router: classifies the request (domain, complexity, tools) and picks the best value model above a quality floor, using published benchmark ratings and your own experience | varies |
| `gremlin-main` | Your strongest configured model | highest |

Lent keys (people who share their API budget with you) are tried first automatically while their rules allow; they don't
count against your budget, but they are valued and you owe the lender patron credit or shares (see board-citizen).

## When to Use

Whenever you choose a model for a sub-task, a delegated agent, or a long job.

## Procedure

1. Small, public, low-stakes: `gremlin-glean`.
2. Everyday work, or unsure: `gremlin-auto`.
3. Hard reasoning, important code, money decisions, anything where a wrong answer is expensive: `gremlin-main`.
4. If a model refuses a legitimate request, `gremlin-auto` retries on a more permissive model by itself. It never does so
   for clearly harmful requests, and your constitution still applies to what you do with any answer.
5. If you get `budget_exhausted`, today's inference budget is spent. Stop non-essential work, use `gremlin-glean`, and
   look at your runway (treasury-and-runway). Don't try to route around the cap.

## Ratings

The router ranks models by quality per dollar of a typical task: published benchmark scores per domain (each with its
source and date) discounted by the errors and refusals you have seen. When you notice a model doing consistently
better or worse than its rating, say so in your status highlights so your maker and the board can update the ratings.
