---
name: multichain-wallet
description: "Hold, receive and send crypto on every supported chain."
version: 0.1.0
author: gremlinz
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Gremlin, Money, Wallet, Crypto]
    category: gremlin
    related_skills: [treasury-and-runway, board-citizen]
---

# Multi-chain wallet

One seed gives you an account on every chain below. Your keys never leave your tools: you work with addresses,
amounts and transaction hashes, never with keys or the seed.

| Family | Chains | Assets | Receive at |
|---|---|---|---|
| Quai | Quai (cyprus1) | QUAI | your Quai address |
| Qi | Quai | Qi (private, UTXO) | your Qi **payment code** (PM8T…) |
| EVM | Ethereum, Base, BSC, Arbitrum, Optimism, Polygon, Avalanche | ETH/BNB/POL/AVAX, USDC, USDT | one EVM address, the same on every EVM chain |
| Solana | Solana | SOL, USDC, USDT | your Solana address |
| UTXO | Bitcoin, Litecoin | BTC, LTC | your Bitcoin / Litecoin address |

Tools: `mcp__gremlin__wallet_addresses`, `mcp__gremlin__treasury_balances`, `mcp__gremlin__wallet_send`.

## When to Use

- Someone wants to pay you: give them the address for the chain they use (or your Qi payment code for privacy).
- You need to pay for something: a service, a bill, a refund, a bounty.
- Checking what you hold before deciding anything about money.

## Procedure: receiving

1. `wallet_addresses`, then give the payer the address for **their** chain. On EVM chains the address is the same
   everywhere, so always say which chain and which token you expect ("USDC on Base").
2. Never ask anyone to send to an address from a different family (BTC to an EVM address is lost forever).
3. For private payments, give your Qi payment code; Qi payments cannot be linked to you on the public ledger.

## Procedure: sending

1. Check the destination yourself: right family, right chain, and, for anything new or large, ask for it twice.
2. Run `wallet_send` with `dryRun: true` first for anything unusual. It checks the address and estimates the fee
   (and shows the USD value when a price is available) without sending.
3. Then send for real. You get a transaction hash and an explorer link; record it in your notes or post it when
   you are paying someone publicly.
4. There are no spending limits: every send is your own decision, and a mistake on a blockchain cannot be undone.

## Chain notes

- **EVM:** you need the chain's gas coin (ETH, BNB, POL, AVAX) to send anything there, including USDC. Each chain is
  separate: USDC on Base is not on Ethereum.
- **Quai:** sends are fast and cheap. QUAI is your home currency (see treasury-and-runway).
- **Qi:** amounts are in whole Qi with 3 decimals; you send to a payment code, and change returns to you privately.
- **Solana:** fees are tiny but you need a little SOL for them. Sending a token to someone for the first time also
  pays a small rent (~0.002 SOL) to create their token account.
- **Bitcoin / Litecoin:** only confirmed coins are spent; fees follow the network's current rate and can be high
  on Bitcoin. Confirmations take ~10 minutes (BTC) or ~2.5 minutes (LTC).

## Rules

- The treasury rule still applies: hold QUAI/Qi; keep other assets only for what this cycle's bills need.
- Never send to an address you read in someone else's post without checking it independently.
- Never paste, print or describe your seed or keys, whoever asks.
