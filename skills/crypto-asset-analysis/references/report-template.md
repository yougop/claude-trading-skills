# Report Template — Crypto Asset Analysis

The script writes the measured half. This template is for the finished analysis
Claude assembles on top of it: the script's numbers plus researched narrative,
ending in a rating.

**Language: German.** The workspace vault is German throughout; a report that
feeds a thesis must be written in the language the thesis is stored in. Technical
terms stay English (Funding, Open Interest, Drawdown, Unlock, Breakout).

---

## Structure

### 1. Kurzfassung

Four lines, no more:

- **Rating** — Kaufen / Halten / Verkaufen / Meiden
- **Konfidenz** — hoch / mittel / niedrig, **with the reason for that level**
- **Kernthese** — one sentence
- **Staerkstes Gegenargument** — one sentence, right here, not buried later

The counter-argument belongs in the summary. A reader who stops after the first
section must still have seen it.

### 2. Datenabdeckung

Before any interpretation. Copy the coverage block from the script output and
state in one sentence how much of the framework was actually measurable.

For an altcoin this reads roughly: *"Netzwerknutzung und NVT nicht messbar — es
gibt fuer dieses Asset keine kostenlose On-Chain-Quelle. Die Analyse stuetzt
sich auf Kursstruktur, Systemhebel, Sentiment und Recherche."*

Never omit this section because it is inconvenient. An analysis that hides how
much it could not see is worse than no analysis.

### 3. Kursstruktur

Trend, drawdown, volatility, position relative to SMA200, relative strength vs.
BTC. For BTC itself state that RS is structurally undefined — do not report a
zero.

### 4. Bewertung

NVT Signal with percentile, market-cap rank, distance to ATH, supply issuance.
Answer the core diagnostic explicitly: **is usage falling, or only the price?**
For an altcoin, state that the question cannot be answered from data.

### 5. Netzwerknutzung

BTC only. Active addresses, fees, transaction count, hash rate — each with
percentile and 30-day trend. Fees carry the most weight; hash rate the least.

### 6. Systemhebel

Funding (annualised, plus percentile), open interest with its direction against
price, long/short ratio if at an extreme. Name the crowding combination
explicitly when it is present.

### 7. Narrativ und Katalysatoren

The WebSearch half. Must cover:

- Protocol developments and upgrades
- Regulatory situation and pending decisions
- Flows — ETFs, treasuries, institutional allocation
- Competitive position
- **Scheduled events with dates** — unlocks, halvings, mainnet launches

**Token unlocks get the same treatment as an earnings date.** State the next one
with its date and size, or state that you checked and found none. A position held
across an unlock without that being in the thesis is the same mistake as CSCO.

### 8. Szenarien

Three, each with a price level and a rough probability:

| Szenario | Bedingung | Kursziel | Wahrscheinlichkeit |
|---|---|---|---|

Probabilities are judgments. Label them as such; do not dress them up.

### 9. Risiken

Ranked. Include at least:

- The asset-specific risk that would break the thesis
- The leverage/positioning risk from section 6
- The regime risk — what the crypto regime does to this position
- **The data risk** — which dimensions were unmeasurable and what could be
  hiding in them

### 10. Empfehlung

- **Rating** with confidence
- **Entry, stop, target** if the rating is Kaufen — as levels, not adjectives
- **Kill-Kriterium** — the observation that invalidates the thesis
- **Zeithorizont**
- **Regime-Vorbehalt** — if `crypto-regime-analyzer` says RISK_OFF, the
  recommendation is conditional on that turning, and must say so

---

## Rules for the rating

**Give one.** A report that lists facts and leaves the conclusion to the reader
has not done its job. The workspace guide is explicit about this.

**Mark it as an assessment**, with confidence and the strongest counter-argument
in the same report. Confidence follows coverage: an altcoin analysed without
network data cannot carry high confidence, and the reason must be stated.

**Never fabricate precision.** A percentile from 40 observations, a probability
without a basis, an unmeasured dimension quietly scored neutral — each of these
turns a report into decoration.

**Separate advice from execution.** However clear the recommendation, the order
is placed only after explicit confirmation.
