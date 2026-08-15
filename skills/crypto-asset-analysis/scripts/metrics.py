#!/usr/bin/env python3
"""Pure metric functions for crypto asset analysis.

Design rule that governs this whole module: **report a value together with its
own historical percentile, never against an inherited threshold.**

The reason is a mistake we already made once. The crypto swing screener inherited
`trend_min_score=85` and `t1_depth_min=10%` from the equity VCP screener and has
never produced a single candidate, because equity thresholds do not survive
2-3x crypto volatility. A threshold you cannot calibrate is not a measurement,
it is a guess wearing a number. Percentile rank against the asset's own history
needs no calibration: "funding is at the 96th percentile of its own last year"
means the same thing for BTC as for SOL.

No I/O, no network, no global state - everything here is a function of its
arguments so the tests can be exhaustive.
"""

from __future__ import annotations

import math
import statistics
from collections.abc import Iterable, Sequence

# Perpetual funding is quoted per 8h interval -> 3 payments a day.
FUNDING_INTERVALS_PER_YEAR = 3 * 365


def _clean(values: Iterable[float | None]) -> list[float]:
    """Drop Nones, NaNs and infinities. Returns a plain list of finite floats."""
    out: list[float] = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f):
            out.append(f)
    return out


def percentile_rank(history: Sequence[float | None], value: float | None) -> float | None:
    """Where `value` sits within `history`, as 0-100.

    Uses the midrank convention (ties count half), so a value equal to every
    observation lands at 50 rather than 0 or 100. Returns None when history is
    too short to mean anything - deliberately, because a percentile over three
    observations is noise with a decimal point.
    """
    hist = _clean(history)
    if value is None or not math.isfinite(float(value)) or len(hist) < 30:
        return None
    v = float(value)
    below = sum(1 for h in hist if h < v)
    equal = sum(1 for h in hist if h == v)
    return round(100.0 * (below + 0.5 * equal) / len(hist), 1)


def sma(values: Sequence[float | None], window: int) -> float | None:
    """Simple moving average of the last `window` finite observations."""
    vals = _clean(values)
    if window <= 0 or len(vals) < window:
        return None
    return sum(vals[-window:]) / window


def pct_change(values: Sequence[float | None], lookback: int) -> float | None:
    """Percent change over `lookback` observations, as a percentage."""
    vals = _clean(values)
    if lookback <= 0 or len(vals) < lookback + 1:
        return None
    old, new = vals[-(lookback + 1)], vals[-1]
    if old == 0:
        return None
    return round((new - old) / old * 100.0, 2)


def median_change(values: Sequence[float | None], window: int = 30) -> float | None:
    """Change between the median of the two halves of the window, in percent.

    Companion to `trend_direction`, and the reason it exists is a
    self-contradicting report line. The diagnostic paired a least-squares slope
    ("rising") with an endpoint-to-endpoint change (-12.5%) — two measures of
    different robustness, printed as if they agreed. BTC transaction fees on
    2026-08-15: first day 240k, last day 210k, but the median of the first half
    was 201k against 221k in the second. The slope was right; the endpoint
    comparison was hostage to one spiky day at the start.

    A robust direction deserves a robust magnitude beside it.
    """
    vals = _clean(values)
    if len(vals) < window or window < 4:
        return None
    fenster = vals[-window:]
    half = len(fenster) // 2
    a = statistics.median(fenster[:half])
    b = statistics.median(fenster[half:])
    if a == 0:
        return None
    return round((b / a - 1) * 100.0, 2)


def drawdown_from_high(values: Sequence[float | None]) -> float | None:
    """Current decline from the highest point in the series, as a positive percent."""
    vals = _clean(values)
    if len(vals) < 2:
        return None
    peak = max(vals)
    if peak <= 0:
        return None
    return round((peak - vals[-1]) / peak * 100.0, 2)


def max_drawdown(values: Sequence[float | None]) -> float | None:
    """Largest peak-to-trough decline in the series, as a positive percent."""
    vals = _clean(values)
    if len(vals) < 2:
        return None
    peak = vals[0]
    worst = 0.0
    for v in vals:
        if v > peak:
            peak = v
        if peak > 0:
            worst = max(worst, (peak - v) / peak)
    return round(worst * 100.0, 2)


def realized_volatility(values: Sequence[float | None], window: int = 30) -> float | None:
    """Annualised stdev of daily log returns over `window` days, in percent.

    Crypto trades 365 days a year, so the annualisation factor is sqrt(365),
    not the sqrt(252) used for equities. Getting this wrong understates crypto
    volatility by about 17%.
    """
    vals = _clean(values)
    if len(vals) < window + 1 or window < 2:
        return None
    rets = []
    for prev, cur in zip(vals[-(window + 1):-1], vals[-window:]):
        if prev > 0 and cur > 0:
            rets.append(math.log(cur / prev))
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return round(math.sqrt(var) * math.sqrt(365) * 100.0, 2)


def relative_strength(
    asset: Sequence[float | None],
    benchmark: Sequence[float | None],
    lookback: int = 90,
) -> float | None:
    """Asset return minus benchmark return over `lookback` days, in percentage points.

    Returns None when asset and benchmark are the same series - measuring BTC
    against BTC yields a structural zero that reads like weakness but is an
    artefact. This is the same defect that makes criterion 7 of the trend
    template unreachable for BTC; here it is caught rather than reported.
    """
    a = pct_change(asset, lookback)
    b = pct_change(benchmark, lookback)
    if a is None or b is None:
        return None
    if _clean(asset) == _clean(benchmark):
        return None
    return round(a - b, 2)


def funding_annualized(rate_per_interval: float | None) -> float | None:
    """Annualise one 8h perp funding rate, in percent.

    A 0.01% 8h rate - the exchange default - annualises to about 11%. That is
    the cost of carrying a long, and it is the number that matters for a
    multi-week hold, not the raw decimal.
    """
    if rate_per_interval is None or not math.isfinite(float(rate_per_interval)):
        return None
    return round(float(rate_per_interval) * FUNDING_INTERVALS_PER_YEAR * 100.0, 2)


def nvt(market_cap: float | None, tx_volume_usd: float | None) -> float | None:
    """Network Value to Transactions: market cap divided by daily settled USD volume.

    The rough crypto analogue of a P/E - what the network costs relative to the
    economic throughput it actually settles. High means the price has run ahead
    of usage.
    """
    if market_cap is None or tx_volume_usd is None:
        return None
    if tx_volume_usd <= 0 or market_cap <= 0:
        return None
    return round(market_cap / tx_volume_usd, 1)


def nvt_signal(
    market_caps: Sequence[float | None],
    tx_volumes: Sequence[float | None],
    window: int = 90,
) -> float | None:
    """NVT with the denominator smoothed over `window` days.

    Raw daily NVT is unusable - settled volume swings by multiples day to day,
    so the ratio spikes on quiet days and reads as overvaluation that is really
    just a weekend. Smoothing the denominator is the standard fix (Woo's "NVT
    Signal").
    """
    caps, vols = _clean(market_caps), _clean(tx_volumes)
    if not caps or len(vols) < window:
        return None
    return nvt(caps[-1], sum(vols[-window:]) / window)


def trend_direction(values: Sequence[float | None], window: int = 30) -> str | None:
    """Sign of the least-squares slope over the last `window` points.

    Returns "rising", "falling" or "flat". Flat is anything within 0.1% of the
    series mean per period, which keeps noise from being reported as a trend.
    """
    vals = _clean(values)
    if len(vals) < window or window < 3:
        return None
    y = vals[-window:]
    n = len(y)
    mean_x = (n - 1) / 2
    mean_y = sum(y) / n
    denom = sum((i - mean_x) ** 2 for i in range(n))
    if denom == 0:
        return None
    slope = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(y)) / denom
    if mean_y == 0:
        return None
    if abs(slope / mean_y) < 0.001:
        return "flat"
    return "rising" if slope > 0 else "falling"


def supply_issuance_pct(circulating: float | None, max_supply: float | None) -> float | None:
    """Share of maximum supply already issued, in percent.

    None when there is no cap - an uncapped token has no meaningful number here,
    and reporting 0 would imply the opposite of the truth.
    """
    if circulating is None or max_supply is None or max_supply <= 0:
        return None
    return round(circulating / max_supply * 100.0, 2)
