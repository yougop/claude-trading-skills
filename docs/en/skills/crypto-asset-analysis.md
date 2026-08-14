---
layout: default
title: "Crypto Asset Analysis"
grand_parent: English
parent: Skill Guides
nav_order: 15
lang_peer: /ja/skills/crypto-asset-analysis/
permalink: /en/skills/crypto-asset-analysis/
generated: true
---

# Crypto Asset Analysis
{: .no_toc }

Comprehensive crypto asset analysis combining a keyless quantitative core (CoinGecko, Binance futures, blockchain.info on-chain, Fear & Greed) with web-researched narrative and catalysts, ending in an explicit buy/hold/sell recommendation with confidence and counter-argument. The crypto counterpart to us-stock-analysis. Use when evaluating a specific coin as a swing or position candidate, when a crypto thesis needs a deep dive before entry, or when asked whether a coin is cheap, over-levered, or losing network usage.
{: .fs-6 .fw-300 }

<span class="badge badge-free">No API</span>

[View Source on GitHub](https://github.com/tradermonty/claude-trading-skills/tree/main/skills/crypto-asset-analysis){: .btn .fs-5 .mb-4 .mb-md-0 }

<details open markdown="block">
  <summary>Table of Contents</summary>
  {: .text-delta }
- TOC
{:toc}
</details>

---

## 1. Overview

# Crypto Asset Analysis Skill

---

## 2. Prerequisites

- **API Key:** None required
- **Python 3.9+** recommended

---

## 3. Quick Start

```bash
python3 skills/crypto-asset-analysis/scripts/crypto_asset_analysis.py \
  --ticker BTC --output-dir reports/
```

---

## 4. Workflow

### Step 1 — Run the quantitative core

```bash
python3 skills/crypto-asset-analysis/scripts/crypto_asset_analysis.py \
  --ticker BTC --output-dir reports/
```

Writes `crypto_asset_<ticker>_<date>.json` and `.md`. Takes 30-90 seconds;
CoinGecko rate-limits the free tier and the client backs off rather than failing.

**Read the coverage section first, before any number.** It lists what loaded and
what did not. A missing source is never imputed — a gap stays a gap. Two failure
modes are called out specifically:

- `*_kurz` entries mean a request succeeded but returned a short series. Any
  percentile built on it is not trustworthy.
- `price_sanity` means the price is outside the plausible band for that asset,
  which almost always means the wrong instrument came back.

### Step 2 — Research narrative and catalysts by WebSearch

The script cannot see any of this. Search for at least:

1. **Protocol news** — upgrades, forks, major releases, security incidents
2. **Regulatory** — ETF decisions, enforcement actions, jurisdiction changes
3. **Flows** — spot ETF creations/redemptions, treasury allocations, unlocks
4. **Competition** — what the closest competing chain or asset is doing
5. **Scheduled events** — halvings, unlock cliffs, mainnet dates

**Token unlocks are the crypto counterpart to an earnings date** (Rule 5 in the
workspace guide). A large scheduled unlock inside the holding period is supply
arriving on a known date. Find it, or state that you checked and found none.

### Step 3 — Read the references you actually need

| File | When |
|---|---|
| `references/crypto-fundamentals.md` | interpreting valuation and network usage |
| `references/onchain-metrics.md` | what each on-chain series means, and its blind spots |
| `references/derivatives-positioning.md` | funding, open interest, long/short |
| `references/report-template.md` | assembling the final report |

### Step 4 — Synthesise into a rating

Follow `references/report-template.md`. The rating must carry:

- **Direction** — buy / hold / sell / avoid
- **Confidence** — high / medium / low, with the reason for the level
- **The strongest counter-argument**, in the same report
- **Kill criterion** — what observation would invalidate the thesis
- **Coverage caveat** — for an altcoin, state plainly that network usage could
  not be measured. Do not let a four-dimension analysis read like a six.

---

## 5. Resources

**References:**

- `skills/crypto-asset-analysis/references/crypto-fundamentals.md`
- `skills/crypto-asset-analysis/references/derivatives-positioning.md`
- `skills/crypto-asset-analysis/references/onchain-metrics.md`
- `skills/crypto-asset-analysis/references/report-template.md`

**Scripts:**

- `skills/crypto-asset-analysis/scripts/crypto_asset_analysis.py`
- `skills/crypto-asset-analysis/scripts/data_sources.py`
- `skills/crypto-asset-analysis/scripts/metrics.py`
