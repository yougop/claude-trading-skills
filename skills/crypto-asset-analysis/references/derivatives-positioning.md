# Derivatives & Positioning — the leverage dimension

This is the strongest part of the free crypto data stack. Equity analysts would
love to have it: a live, public read on how much leverage sits on the price and
which direction it leans. Use it.

## Funding rate

Perpetual futures have no expiry, so they are tethered to spot by a payment
between longs and shorts, settled every 8 hours on Binance.

- **Positive** — longs pay shorts. The perp trades above spot. Crowd is long.
- **Negative** — shorts pay longs. The perp trades below spot. Crowd is short.

**Always read the annualised figure.** The raw number (0.0001) is meaningless
at a glance; annualised (about 11%) it is obviously a real cost on a multi-week
hold. The script annualises on 3 payments a day × 365.

Rules of thumb, in annualised terms:

| Annualised | Reading |
|---|---|
| below -20% | shorts crowded, squeeze risk upward |
| -20% to 0% | bearish positioning, often near lows |
| 0% to 15% | normal; 11% is the exchange default and means nothing |
| 15% to 50% | longs paying up, crowding building |
| above 50% | extreme; historically close to local tops |

**Treat these bands as orientation, not thresholds.** The percentile the script
reports against the asset's own history is the more reliable read — funding
regimes shift with the broader rate environment, and a band calibrated in 2021
does not transfer.

**Use the 7-day average for the state, the latest print for the change.** A
single 8h reading is noisy; the average is the regime.

## Open interest

Total notional of open perp contracts. On its own it says only how much is at
stake. **Its value is entirely in the combination with price:**

| Price | Open interest | Reading |
|---|---|---|
| rising | rising | new money entering — healthiest continuation signal |
| rising | falling | short covering — a rally with no new buyers, fades often |
| falling | rising | new shorts pressing — trend has conviction |
| falling | falling | longs capitulating — deleveraging, often near a bottom |

**Binance caps this endpoint at 30 days**, so the percentile is a one-month
statement. Do not present it as a cycle read.

## Long/short account ratio

Share of accounts positioned long, as a ratio. Above 1 means more accounts are
long than short.

**This counts accounts, not size.** Retail dominates the account count, so it is
a retail-sentiment measure. A ratio of 3 with price stalling means a lot of small
accounts are long and providing the fuel for a flush.

Reliably contrarian at extremes, noise in the middle. Only quote it when the
percentile is above 85 or below 15.

## The combination that actually matters

The single most useful read this data provides:

> **Funding high AND open interest rising AND price flat = crowding.**

Longs are paying an increasing toll to hold a position that is not working, and
the crowd is still growing. That is a long squeeze waiting for a trigger. It does
not tell you when — but it tells you that the downside is mechanically amplified,
because liquidations cascade.

The mirror case — deeply negative funding, open interest rising, price flat — is
the short-squeeze setup and marks capitulation lows more often than it marks
continuation.

## What derivatives data cannot tell you

- **Nothing about spot demand.** ETF flows, treasury buying and long-term
  accumulation are invisible here. A perp market can look crowded while spot
  quietly absorbs supply.
- **Nothing about a specific timing.** Crowded stays crowded, sometimes for
  months. This is a risk measure, not a trigger.
- **Binance only.** It is the largest venue, but positioning on other exchanges
  and in options is not in this picture.
