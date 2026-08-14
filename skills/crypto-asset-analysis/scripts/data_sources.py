#!/usr/bin/env python3
"""Free, keyless data sources for crypto asset analysis.

Four providers, none of which needs an API key:

  CoinGecko        price/market-cap history, supply, ATH        all assets
  Binance FAPI     funding history, open interest, long/short   perp-listed assets
  alternative.me   Fear & Greed index                           market-wide
  blockchain.info  on-chain: addresses, fees, tx volume, hash   BTC only

**Every fetch degrades to None and records why.** No provider failure raises,
and no missing value is ever imputed or back-filled. This is deliberate: the
exposure-coach in this same toolbox silently substitutes a fixed number when an
input is absent, which cost us 18,700 USD of position capacity on 2026-08-14
because nobody could see that a substitution had happened. Here a gap stays a
gap and shows up in the coverage report.

The BTC-only limit on on-chain data is a real hole, not an oversight: MVRV and
realized cap have no free provider at all, and blockchain.info has no altcoin
equivalent. The report says so per asset rather than quietly analysing four
dimensions and calling it five.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
BINANCE_FAPI_BASE = "https://fapi.binance.com"
# Trailing slash is load-bearing: api.alternative.me/fng redirects to /fng/ and
# drops the query string on the way, so the limit parameter is lost and the
# response silently shrinks to a single day. The request still returns 200 and
# valid JSON - it just answers a different question than the one asked.
FNG_BASE = "https://api.alternative.me/fng/"
BLOCKCHAIN_INFO_BASE = "https://api.blockchain.info/charts"

USER_AGENT = "claude-trading-skills/crypto-asset-analysis"
TIMEOUT_S = 20
RETRIES = 3
BACKOFF_BASE_S = 15

# CoinGecko ids and Binance perp symbols for the majors we actually screen.
ASSET_MAP: dict[str, dict[str, str | None]] = {
    "BTC": {"coingecko": "bitcoin", "binance": "BTCUSDT", "onchain": "btc"},
    "ETH": {"coingecko": "ethereum", "binance": "ETHUSDT", "onchain": None},
    "SOL": {"coingecko": "solana", "binance": "SOLUSDT", "onchain": None},
    "BNB": {"coingecko": "binancecoin", "binance": "BNBUSDT", "onchain": None},
    "XRP": {"coingecko": "ripple", "binance": "XRPUSDT", "onchain": None},
    "ADA": {"coingecko": "cardano", "binance": "ADAUSDT", "onchain": None},
    "AVAX": {"coingecko": "avalanche-2", "binance": "AVAXUSDT", "onchain": None},
    "LINK": {"coingecko": "chainlink", "binance": "LINKUSDT", "onchain": None},
    "DOGE": {"coingecko": "dogecoin", "binance": "DOGEUSDT", "onchain": None},
    "DOT": {"coingecko": "polkadot", "binance": "DOTUSDT", "onchain": None},
    "MATIC": {"coingecko": "matic-network", "binance": "MATICUSDT", "onchain": None},
    "LTC": {"coingecko": "litecoin", "binance": "LTCUSDT", "onchain": None},
}

# A price this far from the expected magnitude means the wrong instrument came
# back. FMP already served us a "BTC" trading at 28 USD instead of 63,000 on
# 2026-08-14 and the charts were silently wrong for a day.
SANITY_RANGE_USD: dict[str, tuple[float, float]] = {
    "BTC": (1_000.0, 10_000_000.0),
    "ETH": (50.0, 500_000.0),
}


@dataclass
class FetchLog:
    """Records what was fetched and what failed, for the coverage report."""

    ok: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)

    def succeed(self, name: str) -> None:
        self.ok.append(name)

    def fail(self, name: str, reason: str) -> None:
        self.failed[name] = reason

    def as_dict(self) -> dict[str, Any]:
        return {"fetched": sorted(self.ok), "unavailable": dict(sorted(self.failed.items()))}


def resolve_asset(ticker: str) -> dict[str, str | None]:
    """Map a ticker to provider-specific identifiers. Raises on unknown tickers."""
    key = ticker.strip().upper()
    if key not in ASSET_MAP:
        known = ", ".join(sorted(ASSET_MAP))
        raise KeyError(f"unknown ticker {ticker!r}; known: {known}")
    return dict(ASSET_MAP[key], ticker=key)


def _http_get_json(url: str, params: dict | None = None, *, quiet: bool = True) -> Any:
    """GET returning parsed JSON. Retries on 429/5xx with backoff, then raises."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    last_error: Exception | None = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                wait = BACKOFF_BASE_S * (2**attempt)
                if not quiet:
                    print(f"  {exc.code} on {url[:60]}, warte {wait}s")
                time.sleep(wait)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < RETRIES - 1:
                time.sleep(BACKOFF_BASE_S)
                continue
            raise
    raise RuntimeError(f"unreachable after {RETRIES} attempts: {last_error}")


# A percentile needs history. Below this many observations the metric functions
# return None anyway, so a series shorter than this is worth flagging rather
# than passing along as if it were an answer.
MIN_USEFUL_SERIES = 30


def _check_series_length(name: str, series: Any, requested: int, log: FetchLog) -> None:
    """Flag a series that came back materially shorter than requested.

    The failure this catches is nastier than an outage: the request succeeds,
    the JSON parses, and the only symptom is that every percentile downstream
    quietly reports "not enough history". The Fear & Greed endpoint did exactly
    this - a missing trailing slash cost the query string and turned 365 days
    into 1, with no error anywhere.
    """
    if not isinstance(series, (list, tuple)):
        return
    got = len(series)
    if got < min(requested, MIN_USEFUL_SERIES):
        log.fail(
            f"{name}_kurz",
            f"nur {got} von {requested} angeforderten Werten zurueckgeliefert — "
            "Perzentile dazu sind nicht belastbar",
        )


def _sanity_check_price(ticker: str, price: float | None) -> str | None:
    """Return a complaint string if the price is outside the plausible band."""
    band = SANITY_RANGE_USD.get(ticker)
    if band is None or price is None:
        return None
    low, high = band
    if not (low <= price <= high):
        return f"Kurs {price:,.2f} USD ausserhalb des Plausibilitaetsbands {low:,.0f}-{high:,.0f}"
    return None


def fetch_market_history(coingecko_id: str, days: int = 365) -> dict[str, list]:
    """Daily price, market cap and volume history from CoinGecko.

    Returns parallel lists under `prices`, `market_caps`, `volumes` plus the
    unix `timestamps`. CoinGecko's free tier caps daily granularity at 365 days.
    """
    raw = _http_get_json(
        f"{COINGECKO_BASE}/coins/{coingecko_id}/market_chart",
        {"vs_currency": "usd", "days": str(days), "interval": "daily"},
    )
    return {
        "timestamps": [int(p[0] / 1000) for p in raw.get("prices", [])],
        "prices": [float(p[1]) for p in raw.get("prices", [])],
        "market_caps": [float(p[1]) for p in raw.get("market_caps", [])],
        "volumes": [float(p[1]) for p in raw.get("total_volumes", [])],
    }


def fetch_asset_profile(coingecko_id: str) -> dict[str, Any]:
    """Current snapshot: price, market cap, supply, all-time high, rank."""
    raw = _http_get_json(
        f"{COINGECKO_BASE}/coins/{coingecko_id}",
        {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        },
    )
    md = raw.get("market_data") or {}

    def usd(field_name: str) -> float | None:
        block = md.get(field_name)
        return float(block["usd"]) if isinstance(block, dict) and "usd" in block else None

    return {
        "name": raw.get("name"),
        "market_cap_rank": raw.get("market_cap_rank"),
        "price_usd": usd("current_price"),
        "market_cap_usd": usd("market_cap"),
        "volume_24h_usd": usd("total_volume"),
        "ath_usd": usd("ath"),
        "ath_change_pct": (md.get("ath_change_percentage") or {}).get("usd"),
        "circulating_supply": md.get("circulating_supply"),
        "max_supply": md.get("max_supply"),
    }


def fetch_funding_history(symbol: str, limit: int = 500) -> list[float]:
    """Perp funding rates, oldest first. Each entry covers one 8h interval."""
    raw = _http_get_json(
        f"{BINANCE_FAPI_BASE}/fapi/v1/fundingRate", {"symbol": symbol, "limit": str(limit)}
    )
    return [float(row["fundingRate"]) for row in raw if "fundingRate" in row]


def fetch_open_interest_history(symbol: str, limit: int = 30) -> dict[str, list[float]]:
    """Daily open interest, oldest first. Binance caps this endpoint at 30 days."""
    raw = _http_get_json(
        f"{BINANCE_FAPI_BASE}/futures/data/openInterestHist",
        {"symbol": symbol, "period": "1d", "limit": str(limit)},
    )
    return {
        "contracts": [float(r["sumOpenInterest"]) for r in raw],
        "notional_usd": [float(r["sumOpenInterestValue"]) for r in raw],
    }


def fetch_long_short_ratio(symbol: str, limit: int = 30) -> list[float]:
    """Global long/short account ratio, oldest first. Above 1 means more long accounts."""
    raw = _http_get_json(
        f"{BINANCE_FAPI_BASE}/futures/data/globalLongShortAccountRatio",
        {"symbol": symbol, "period": "1d", "limit": str(limit)},
    )
    return [float(r["longShortRatio"]) for r in raw]


def fetch_fear_greed(limit: int = 365) -> list[int]:
    """Fear & Greed index, oldest first, 0-100. Market-wide, not per asset."""
    raw = _http_get_json(FNG_BASE, {"limit": str(limit), "format": "json"})
    values = [int(row["value"]) for row in raw.get("data", []) if "value" in row]
    return list(reversed(values))  # provider returns newest first


def fetch_onchain_series(chart: str, days: int = 365) -> list[float]:
    """One blockchain.info chart series, oldest first. Bitcoin only."""
    raw = _http_get_json(
        f"{BLOCKCHAIN_INFO_BASE}/{chart}", {"timespan": f"{days}days", "format": "json"}
    )
    return [float(p["y"]) for p in raw.get("values", [])]


ONCHAIN_CHARTS = {
    "active_addresses": "n-unique-addresses",
    "tx_volume_usd": "estimated-transaction-volume-usd",
    "fees_usd": "transaction-fees-usd",
    "hash_rate": "hash-rate",
    "miner_revenue_usd": "miners-revenue",
    "tx_count": "n-transactions",
}

# What no free provider covers. Named explicitly so the report can say what is
# missing instead of only what is present.
ONCHAIN_GAPS = {
    "mvrv": "MVRV / Realized Cap - nur bei Glassnode oder CryptoQuant, beide kostenpflichtig",
    "sopr": "SOPR - dieselben Anbieter, ebenfalls kostenpflichtig",
    "exchange_flows": "Exchange Netflows - kein verlaesslicher Gratis-Feed",
}


def collect(ticker: str, *, days: int = 365, quiet: bool = True) -> tuple[dict[str, Any], FetchLog]:
    """Gather everything available for one asset. Never raises on provider failure."""
    ids = resolve_asset(ticker)
    log = FetchLog()
    data: dict[str, Any] = {"ticker": ids["ticker"], "ids": ids}

    def attempt(name: str, fn, *args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - a provider outage is data, not a crash
            log.fail(name, f"{type(exc).__name__}: {exc}")
            return None
        log.succeed(name)
        return result

    cg_id = ids["coingecko"]
    data["profile"] = attempt("coingecko_profile", fetch_asset_profile, cg_id)
    data["history"] = attempt("coingecko_history", fetch_market_history, cg_id, days)

    complaint = _sanity_check_price(
        ids["ticker"], (data.get("profile") or {}).get("price_usd")
    )
    if complaint:
        log.fail("price_sanity", complaint)

    if ids.get("binance"):
        sym = ids["binance"]
        data["funding"] = attempt("binance_funding", fetch_funding_history, sym)
        data["open_interest"] = attempt("binance_open_interest", fetch_open_interest_history, sym)
        data["long_short"] = attempt("binance_long_short", fetch_long_short_ratio, sym)
    else:
        log.fail("binance_funding", "kein Perp-Symbol hinterlegt")

    data["fear_greed"] = attempt("fear_greed", fetch_fear_greed)
    _check_series_length("fear_greed", data.get("fear_greed"), 365, log)

    if data.get("funding") is not None:
        _check_series_length("binance_funding", data["funding"], 500, log)
    if (data.get("history") or {}).get("prices") is not None:
        _check_series_length("coingecko_history", data["history"]["prices"], days, log)

    if ids.get("onchain") == "btc":
        onchain: dict[str, list[float]] = {}
        for key, chart in ONCHAIN_CHARTS.items():
            series = attempt(f"onchain_{key}", fetch_onchain_series, chart, days)
            if series:
                onchain[key] = series
                _check_series_length(f"onchain_{key}", series, days, log)
        data["onchain"] = onchain
    else:
        data["onchain"] = {}
        log.fail(
            "onchain",
            f"blockchain.info deckt nur Bitcoin ab, fuer {ids['ticker']} gibt es "
            "keine kostenlose On-Chain-Quelle",
        )

    # Benchmark for relative strength - skipped for BTC itself, where it would
    # be BTC against BTC and structurally meaningless.
    if ids["ticker"] != "BTC":
        btc_hist = attempt("benchmark_btc", fetch_market_history, "bitcoin", days)
        data["benchmark_prices"] = (btc_hist or {}).get("prices", [])
    else:
        data["benchmark_prices"] = []

    return data, log
