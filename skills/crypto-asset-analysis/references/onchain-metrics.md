# On-Chain Metrics — coverage, meaning, blind spots

## Coverage, stated up front

| Metric | Free source | Assets |
|---|---|---|
| Active addresses | blockchain.info | **BTC only** |
| Transaction fees (USD) | blockchain.info | **BTC only** |
| Transaction count | blockchain.info | **BTC only** |
| Estimated transaction volume (USD) | blockchain.info | **BTC only** |
| Hash rate | blockchain.info | **BTC only** |
| Miner revenue | blockchain.info | **BTC only** |
| NVT / NVT Signal | computed from the above | **BTC only** |
| MVRV, realized cap | — none free — | nobody |
| SOPR | — none free — | nobody |
| Exchange netflows | — none free — | nobody |

Two consequences that must reach the report rather than staying here:

1. **Every altcoin analysis runs on four dimensions, not six.** Valuation loses
   its numerator and network usage is empty. Say this in the report; do not let
   the missing rows read as neutral.
2. **Cycle position is not measurable.** MVRV and SOPR are the metrics that
   answer "is the average holder in profit, and are they selling?" Glassnode and
   CryptoQuant both paywall them. Nothing in this skill substitutes for that.

## What each series means

### Active addresses
Distinct addresses transacting in a day. The closest free proxy for user count.

**Weakness:** one person can control thousands of addresses, and exchanges batch
many users into few addresses. The level is unreliable; **the trend is what to
read.** A 30-day decline while price rises is a genuine divergence.

### Transaction fees in USD
Total paid to miners for blockspace, excluding block rewards.

**The best of the four.** Fees are the one on-chain number that cannot be
manufactured — someone paid real money for inclusion. This is as close to
revenue as Bitcoin has.

Rising fees mean competition for blockspace, which means genuine demand. Fees
collapsing while price holds is the crypto analogue of revenue falling while the
multiple expands.

**Weakness:** spiky. Ordinal congestion events and inscription waves produce
outliers that are not demand trends. Read the percentile and the 30-day trend
together, never a single day.

### Transaction count
Daily transaction total. Simple throughput.

**Weakness — the largest of any series here.** Batching lets one transaction
carry hundreds of payments, and layer-2 moves activity off-chain entirely. A
falling count can accompany rising real usage. Treat it as context, never as
evidence on its own.

### Estimated transaction volume (USD)
Estimated USD value actually settled, with change outputs filtered out. This is
the denominator of NVT.

**Weakness:** the change-output filtering is heuristic and imperfect. Good enough
for a ratio tracked over time, not precise enough to quote as a level.

### Hash rate
Total computing power securing the chain.

**Weakness:** driven by mining economics — hardware cycles, energy prices,
difficulty adjustments — and it *follows* price rather than leading it. Useful as
a security and miner-commitment measure. It is not a demand indicator, and the
"hash rate leads price" claim does not survive testing.

### Miner revenue
Block rewards plus fees. Fetched by the script but not currently reported, since
after a halving it drops mechanically without saying anything about demand.

## How to read these together

The single question worth asking:

> **Is usage confirming the price, or diverging from it?**

The script answers it directly in the report's opening section. This table is
what it is answering with — the `quadrant` code is what lands in the JSON:

| Price | Fees + addresses | Reading | `quadrant` |
|---|---|---|---|
| rising | rising | confirmed — used more and valued more | `bestaetigt` |
| rising | falling | **the important warning** — multiple expansion without usage | `warnung_bewertung_ohne_nutzung` |
| rising | flat | rise without confirmation | `anstieg_ohne_bestaetigung` |
| falling | rising | constructive — the mean-reversion case | `konstruktiv_mean_reversion` |
| falling | falling | genuinely losing business; structure will not save it | `netzwerk_verliert_geschaeft` |
| falling | flat | correction without usage loss | `korrektur_ohne_nutzungsverlust` |
| flat | rising | base building under a range | `aufbau_unter_seitwaertskurs` |
| flat | falling | the range rests on price, not demand | `warnung_nutzung_erodiert` |
| flat | flat | nothing moving either way | `ruhelage` |
| any | contradictory | no verdict — fees and addresses disagree | `unklar` |

**Both trends are measured over the same 30 days**, by least-squares slope
rather than by comparing two endpoints — a single spike day at either end must
not decide the verdict.

**Only fees and active addresses vote.** Transaction count and hash rate are
reported but excluded, for the reasons given above: batching distorts the first,
mining economics drive the second. Letting a difficulty cycle vote on demand
would be a category error.

## Rules for using percentiles here

**All percentiles are against 365 days of the asset's own history.** That is
shorter than a crypto cycle. A metric at its 95th percentile is at a one-year
extreme, not an all-time one — and after a bear year, a one-year high can be a
multi-year low. Never phrase a 365-day percentile as an all-time statement.

**Below 30 observations the script returns no percentile at all** rather than a
number computed from too little data. When the report says "keine Einordnung",
that is the honest answer, not a bug.
