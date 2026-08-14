# Crypto Fundamentals — what replaces the balance sheet

Equity analysis rests on a company that files statements. A protocol files
nothing. This document sets out what to put in place of each missing input, and
where the substitution is weak.

## The core diagnostic, carried over from equities

The workspace methodology asks one question before any thesis: **did earnings
fall, or only the multiple?** The crypto translation:

> **Did network usage fall, or only the price?**

Price down, usage flat or rising → a re-rating. Mean reversion is plausible.
Price down *and* usage down → the network is losing its actual business. No
amount of chart structure fixes that.

This sorts out roughly half of any candidate list, same as in equities. It is
answerable for Bitcoin. For altcoins the free data does not exist, so the
question stays open — say so rather than substituting price momentum for it.

## Valuation

### NVT and NVT Signal

**NVT = market cap / daily settled USD volume.** The rough analogue of a P/E:
what the network costs relative to the economic activity it settles.

Raw daily NVT is unusable — settled volume swings by multiples between weekdays
and weekends, so the ratio spikes on quiet days and reads as overvaluation that
is really just a Sunday. **NVT Signal** smooths the denominator over 90 days and
is the only version worth quoting.

**Never use absolute NVT thresholds.** Published "NVT above 90 is expensive"
rules come from 2014-2018 Bitcoin and broke once exchanges moved volume off-chain
and layer-2 settlement grew. The number drifts structurally. Use the percentile
against the asset's own recent history, which is what the script reports.

### Distance to all-time high

Useful, but not the way it is in equities. A stock 50% below its high suggests
something broke. A crypto asset 50% below its high is in a normal cycle position
— drawdowns of 70-80% happen inside otherwise intact multi-year uptrends.

Read it as cycle position, not damage.

### Supply issuance

**Circulating divided by maximum supply.** Answers how much dilution is still
ahead. Reported as None when there is no cap, which is itself informative — an
uncapped token has permanent issuance and needs demand growth just to hold price.

The scheduled part of issuance is knowable in advance. **Token unlock cliffs are
the crypto equivalent of an earnings date**: a known date on which supply
arrives. They belong in the thesis for the same reason earnings dates do.

## Network usage — the earnings substitute

Four series, Bitcoin only:

| Series | Reads as | Caveat |
|---|---|---|
| Active addresses | user count | one user can hold many addresses; exchanges batch |
| Transaction fees (USD) | willingness to pay for blockspace | the strongest of the four — it is revenue |
| Transaction count | raw throughput | batching and layer-2 move activity off this measure |
| Hash rate | miner commitment | follows price and energy cost, lags usage |

**Fees are the highest-quality signal.** They are the one number that cannot be
faked by wash activity — someone actually paid. Rising fees with a flat price is
the constructive divergence; falling fees with a rising price is the warning.

**Hash rate is the weakest.** It is driven by mining economics and hardware
cycles, and it follows price rather than leading it. Treat it as a security
measure, not a demand measure.

## Competition

The equity question "who is taking share?" maps onto:

- **Relative strength against BTC** over 90 days. Undefined for BTC itself.
- **BTC dominance** — the share of total market cap. Rising dominance means
  capital is consolidating into BTC and alts are losing ground regardless of
  their own narratives.
- **Where the narrative sits** — this is WebSearch work, not a data pull.

## What has no substitute

**Management quality, governance, capital allocation.** Some protocols have
foundations and treasuries that function like a company, most do not. There is no
data feed for this and no honest proxy. When it matters, it has to be researched
and stated as a judgment.

**Cash-flow quality.** Fee revenue is the closest thing, and only some protocols
route it to holders at all. Do not treat fees as if they were free cash flow
accruing to an owner.

## Where this framework is weakest

Ranked by how much it should worry you:

1. **No MVRV or realized cap.** These answer "what did the average holder pay,
   and are they in profit?" — the closest crypto has to a cycle-position
   indicator. Both are paywalled. This is the biggest single hole.
2. **On-chain is Bitcoin-only.** Every altcoin analysis runs on four dimensions
   out of six.
3. **365 days of history.** Shorter than a crypto cycle, so every percentile in
   the report is a within-cycle statement, not a through-cycle one.
4. **Fear & Greed is market-wide.** It cannot distinguish between assets.
