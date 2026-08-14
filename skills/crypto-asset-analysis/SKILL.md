---
name: crypto-asset-analysis
description: Comprehensive crypto asset analysis combining a keyless quantitative core (CoinGecko, Binance futures, blockchain.info on-chain, Fear & Greed) with web-researched narrative and catalysts, ending in an explicit buy/hold/sell recommendation with confidence and counter-argument. The crypto counterpart to us-stock-analysis. Use when evaluating a specific coin as a swing or position candidate, when a crypto thesis needs a deep dive before entry, or when asked whether a coin is cheap, over-levered, or losing network usage.
---

# Crypto Asset Analysis Skill

## Purpose

Evaluate a single crypto asset the way `us-stock-analysis` evaluates a stock: a
structured deep dive that ends in a rating, not a data dump.

The obstacle is that **crypto has no balance sheet.** There are no earnings, no
debt covenants, no analyst models. Half of the equity framework has no referent.
This skill maps each equity dimension onto the closest crypto equivalent and is
explicit about which mappings are solid and which are approximations:

| Equity dimension | Crypto equivalent | Source | Quality |
|---|---|---|---|
| Valuation (P/E) | NVT Signal, market-cap rank, distance to ATH | on-chain + CoinGecko | good for BTC, absent for alts |
| Earnings quality | network usage: active addresses, fees, transactions | blockchain.info | **BTC only** |
| Leverage | perp funding, open interest, long/short ratio | Binance futures | good, all majors |
| Analyst targets | Fear & Greed, positioning | alternative.me | market-wide, not per asset |
| Competition | relative strength vs. BTC, dominance | CoinGecko | good, except for BTC itself |
| Technicals | trend, drawdown, realized volatility | CoinGecko | good, all majors |

**Everything is free and keyless.** No FMP call, no paid on-chain provider.

## The two halves, and why they are separate

**The script measures. Claude judges.** `scripts/crypto_asset_analysis.py`
produces every number and deliberately produces **no rating**. The rating comes
from Claude combining those numbers with narrative and catalysts gathered by
WebSearch.

This split is not stylistic. A composite score would need weights, and there is
no way to calibrate weights for crypto right now — the same problem that left
the crypto swing screener with equity thresholds and zero candidates. A number
whose uncertainty is visible is worth more than a score that hides it.

## Workflow

### Step 1 — Run the quantitative core

```bash
python3 skills/crypto-asset-analysis/scripts/crypto_asset_analysis.py \
  --ticker BTC --output-dir reports/
```

Writes `crypto_asset_<ticker>_<date>.json` and `.md`. Takes 30-90 seconds;
CoinGecko rate-limits the free tier and the client backs off rather than failing.

**The report opens with the core diagnostic** — the quadrant formed by the
30-day price trend against the 30-day usage trend, stated outright rather than
left for the reader to assemble. It answers the question the workspace
methodology puts before every thesis: *did usage fall, or only the price?*

Two things about how it is built, because both are easy to get wrong by hand:

- **Both sides use the same 30-day window.** Comparing a 90-day price move
  against a 30-day usage trend is the obvious mistake and it flatters the
  constructive reading.
- **Only fees and active addresses count toward the verdict.** Transaction
  count is distorted by batching and layer-2; hash rate follows mining
  economics, not demand. Both are still reported, neither votes.

It refuses to answer in exactly one case: when fees and addresses point in
opposite directions. A sideways price still gets a reading — a ranging market
is normal, and the usage half still says something.

**Read the coverage section next, before any number.** It lists what loaded and
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

## Interpretation rules that are easy to get wrong

**Percentiles are relative to the asset's own history, not to a universal
scale.** "Funding at the 95th percentile" means high *for this asset over the
last ~160 days*, not high in absolute terms. It is a positioning signal, not a
valuation.

**High funding plus rising open interest is crowding, not strength.** Longs are
paying to stay long and the crowd is growing. That is the setup for a long
squeeze, and it is the single most useful thing the derivatives data provides.

**Falling network usage with a rising price is the clearest bearish divergence
crypto offers** — the equivalent of revenue falling while the multiple expands.
Available for BTC only, and surfaced by the core diagnostic as
`warnung_bewertung_ohne_nutzung`.

**Do not overrule the diagnostic by eye.** If it says `unklar`, fees and
addresses genuinely disagree; picking the one that suits the thesis is how a
measurement becomes a rationalisation.

**Relative strength against BTC is undefined for BTC.** The script returns None
rather than a structural zero. Never report BTC as "underperforming BTC".

**Realized volatility is annualised on 365 days**, not 252. Crypto does not
close on weekends; using the equity factor understates volatility by ~17%.

## Limits — state these, do not paper over them

- **MVRV, realized cap and SOPR are unavailable.** No free provider exists. For
  cycle-position questions this is a genuine hole, not a rounding error.
- **On-chain data covers Bitcoin only.** For every other asset the network-usage
  dimension is empty.
- **Fear & Greed is market-wide.** It says nothing about the specific asset.
- **Open interest history is capped at 30 days** by Binance, so its percentile
  is short-horizon.
- **CoinGecko free tier caps daily history at 365 days**, so nothing here sees a
  full crypto cycle.

## Relationship to other skills

Run **`crypto-regime-analyzer` first.** It answers whether crypto deserves any
exposure at all; this skill answers whether *this asset* is the right expression.
Analysing an asset in a RISK_OFF regime is fine as preparation, but the regime
gate governs whether a position follows.

Hand the result to `position-sizer` and `trader-memory-core` exactly as the
equity path does — both are asset-class agnostic.
