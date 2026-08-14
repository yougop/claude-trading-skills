#!/usr/bin/env python3
"""Quantitative core of the crypto-asset-analysis skill.

Produces the measurable half of a crypto asset review - six dimensions, each
reported with its own historical percentile - and an explicit statement of what
could not be measured. It does NOT produce a rating: the buy/hold/sell call is
Claude's synthesis of these numbers plus narrative and catalysts gathered by
WebSearch, exactly as `us-stock-analysis` splits the work.

That split is on purpose. A composite score here would need weights, and we have
no way to calibrate weights for crypto - the same problem that left the crypto
swing screener with inherited equity thresholds and zero candidates. Numbers
that are honest about their own uncertainty beat a confident-looking score.

Usage:
    python3 crypto_asset_analysis.py --ticker BTC --output-dir reports/
    python3 crypto_asset_analysis.py --ticker ETH --input-json snapshot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_sources as ds  # noqa: E402
import metrics as m  # noqa: E402


def _fmt(value: float | None, suffix: str = "", digits: int = 2) -> str:
    """Format a number for the report, or an em dash when it is missing."""
    if value is None:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.{digits}f} Mrd.{suffix}"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.{digits}f} Mio.{suffix}"
    return f"{value:,.{digits}f}{suffix}"


def _pct_label(rank: float | None) -> str:
    """Turn a percentile into words, so the report reads without a legend."""
    if rank is None:
        return "keine Einordnung (zu wenig Historie)"
    if rank >= 90:
        return f"{rank:.0f}. Perzentil — Extrem hoch"
    if rank >= 70:
        return f"{rank:.0f}. Perzentil — hoch"
    if rank >= 30:
        return f"{rank:.0f}. Perzentil — Mittelfeld"
    if rank >= 10:
        return f"{rank:.0f}. Perzentil — niedrig"
    return f"{rank:.0f}. Perzentil — Extrem niedrig"


def build_valuation(data: dict) -> dict[str, Any]:
    """Crypto's stand-in for valuation: NVT, market cap rank, distance to ATH."""
    profile = data.get("profile") or {}
    history = data.get("history") or {}
    onchain = data.get("onchain") or {}

    caps = history.get("market_caps") or []
    tx_vol = onchain.get("tx_volume_usd") or []

    signal = m.nvt_signal(caps, tx_vol) if tx_vol else None
    nvt_hist: list[float | None] = []
    if tx_vol and caps:
        n = min(len(caps), len(tx_vol))
        for i in range(90, n):
            nvt_hist.append(m.nvt_signal(caps[: i + 1], tx_vol[: i + 1]))

    return {
        "nvt_signal": signal,
        "nvt_percentile": m.percentile_rank(nvt_hist, signal),
        "nvt_note": None if tx_vol else "NVT braucht On-Chain-Transaktionsvolumen (nur BTC)",
        "market_cap_usd": profile.get("market_cap_usd"),
        "market_cap_rank": profile.get("market_cap_rank"),
        "ath_change_pct": profile.get("ath_change_pct"),
        "supply_issued_pct": m.supply_issuance_pct(
            profile.get("circulating_supply"), profile.get("max_supply")
        ),
    }


def build_network_usage(data: dict) -> dict[str, Any]:
    """Crypto's stand-in for earnings quality: is the network actually used?"""
    onchain = data.get("onchain") or {}
    if not onchain:
        return {"available": False, "reason": "keine kostenlose On-Chain-Quelle fuer dieses Asset"}

    out: dict[str, Any] = {"available": True}
    for key in ("active_addresses", "fees_usd", "tx_count", "hash_rate"):
        series = onchain.get(key)
        if not series:
            continue
        out[key] = {
            "latest": series[-1],
            "percentile": m.percentile_rank(series, series[-1]),
            "change_30d_pct": m.pct_change(series, 30),
            "trend_30d": m.trend_direction(series, 30),
        }
    return out


def build_leverage(data: dict) -> dict[str, Any]:
    """Crypto's stand-in for debt: how much leverage is stacked on the price?"""
    funding = data.get("funding") or []
    oi = data.get("open_interest") or {}
    ls = data.get("long_short") or []

    latest_funding = funding[-1] if funding else None
    notional = oi.get("notional_usd") or []

    return {
        "funding_annualized_pct": m.funding_annualized(latest_funding),
        "funding_percentile": m.percentile_rank(funding, latest_funding),
        "funding_avg_7d_annualized_pct": m.funding_annualized(m.sma(funding, 21)),
        "open_interest_usd": notional[-1] if notional else None,
        "open_interest_change_30d_pct": m.pct_change(notional, min(29, len(notional) - 1))
        if len(notional) > 1
        else None,
        "long_short_ratio": ls[-1] if ls else None,
        "long_short_percentile": m.percentile_rank(ls, ls[-1] if ls else None),
    }


def build_sentiment(data: dict) -> dict[str, Any]:
    """Crypto's stand-in for analyst targets: crowd positioning."""
    fng = data.get("fear_greed") or []
    if not fng:
        return {"available": False, "reason": "Fear & Greed nicht erreichbar"}
    return {
        "available": True,
        "fear_greed": fng[-1],
        "fear_greed_percentile": m.percentile_rank(fng, fng[-1]),
        "fear_greed_change_30d": fng[-1] - fng[-31] if len(fng) > 30 else None,
        "scope": "marktweit, nicht assetspezifisch",
    }


def build_price_structure(data: dict) -> dict[str, Any]:
    """Trend and volatility - the part that is directly comparable to equities."""
    history = data.get("history") or {}
    prices = history.get("prices") or []
    bench = data.get("benchmark_prices") or []

    return {
        "price_usd": prices[-1] if prices else None,
        "drawdown_from_high_pct": m.drawdown_from_high(prices),
        "max_drawdown_365d_pct": m.max_drawdown(prices),
        "realized_vol_30d_pct": m.realized_volatility(prices, 30),
        "realized_vol_90d_pct": m.realized_volatility(prices, 90),
        "return_30d_pct": m.pct_change(prices, 30),
        "return_90d_pct": m.pct_change(prices, 90),
        "sma50": m.sma(prices, 50),
        "sma200": m.sma(prices, 200),
        "above_sma200": (prices[-1] > m.sma(prices, 200))
        if prices and m.sma(prices, 200) is not None
        else None,
        "relative_strength_90d_vs_btc": m.relative_strength(prices, bench, 90) if bench else None,
        "rs_note": "BTC gegen sich selbst — RS strukturell nicht messbar"
        if data.get("ticker") == "BTC"
        else None,
    }


def analyse(data: dict, log: ds.FetchLog) -> dict[str, Any]:
    """Assemble all dimensions plus the coverage statement."""
    dims = {
        "bewertung": build_valuation(data),
        "netzwerknutzung": build_network_usage(data),
        "systemhebel": build_leverage(data),
        "sentiment": build_sentiment(data),
        "kursstruktur": build_price_structure(data),
    }
    profile = data.get("profile") or {}
    return {
        "ticker": data.get("ticker"),
        "name": profile.get("name"),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dimensions": dims,
        "coverage": log.as_dict(),
        "known_gaps": ds.ONCHAIN_GAPS,
    }


def render_markdown(result: dict) -> str:
    """Human-readable report. German, because the person reading it is."""
    d = result["dimensions"]
    val, net, lev, sent, px = (
        d["bewertung"],
        d["netzwerknutzung"],
        d["systemhebel"],
        d["sentiment"],
        d["kursstruktur"],
    )
    t = result["ticker"]
    lines: list[str] = [
        f"# Crypto-Asset-Analyse — {result.get('name') or t} ({t})",
        "",
        f"Erzeugt {result['generated_at']} · quantitativer Teil, ohne Narrativ und Katalysatoren.",
        "",
        "## Kursstruktur",
        "",
        "| Groesse | Wert |",
        "|---|---|",
        f"| Kurs | {_fmt(px['price_usd'])} USD |",
        f"| Abstand zum 365-Tage-Hoch | {_fmt(px['drawdown_from_high_pct'], ' %')} |",
        f"| Groesster Drawdown 365 Tage | {_fmt(px['max_drawdown_365d_pct'], ' %')} |",
        f"| Rendite 30 / 90 Tage | {_fmt(px['return_30d_pct'], ' %')} / "
        f"{_fmt(px['return_90d_pct'], ' %')} |",
        f"| Realisierte Vola 30 / 90 Tage | {_fmt(px['realized_vol_30d_pct'], ' %')} / "
        f"{_fmt(px['realized_vol_90d_pct'], ' %')} |",
        f"| Ueber SMA200 | {'ja' if px['above_sma200'] else 'nein' if px['above_sma200'] is not None else '—'} |",
    ]
    if px.get("rs_note"):
        lines.append(f"| Relative Staerke vs. BTC | {px['rs_note']} |")
    else:
        lines.append(
            f"| Relative Staerke 90 Tage vs. BTC | {_fmt(px['relative_strength_90d_vs_btc'], ' pp')} |"
        )

    lines += [
        "",
        "## Bewertung (Crypto-Pendant zum KGV)",
        "",
        "| Groesse | Wert | Einordnung |",
        "|---|---|---|",
        f"| NVT Signal | {_fmt(val['nvt_signal'], '', 1)} | {_pct_label(val['nvt_percentile'])} |",
        f"| Marktkapitalisierung | {_fmt(val['market_cap_usd'], ' USD')} | Rang "
        f"{val['market_cap_rank'] or '—'} |",
        f"| Abstand zum Allzeithoch | {_fmt(val['ath_change_pct'], ' %')} | |",
        f"| Anteil ausgegebenes Angebot | {_fmt(val['supply_issued_pct'], ' %')} | |",
    ]
    if val.get("nvt_note"):
        lines += ["", f"*{val['nvt_note']}*"]

    lines += ["", "## Netzwerknutzung (Crypto-Pendant zur Gewinnqualitaet)", ""]
    if not net.get("available"):
        lines += [f"**Nicht messbar** — {net.get('reason')}.", ""]
    else:
        lines += ["| Groesse | Aktuell | Einordnung | 30-Tage-Trend |", "|---|---|---|---|"]
        # Hash rate arrives in TH/s, which puts it in the hundreds of millions.
        # Scaling to EH/s is what every other source reports and keeps the
        # column readable next to address counts.
        labels = {
            "active_addresses": ("Aktive Adressen", 1.0),
            "fees_usd": ("Gebuehren (USD/Tag)", 1.0),
            "tx_count": ("Transaktionen/Tag", 1.0),
            "hash_rate": ("Hash-Rate (EH/s)", 1e-6),
        }
        for key, (label, scale) in labels.items():
            block = net.get(key)
            if not block:
                continue
            lines.append(
                f"| {label} | {_fmt(block['latest'] * scale, '', 0)} | "
                f"{_pct_label(block['percentile'])} | {block.get('trend_30d') or '—'} "
                f"({_fmt(block.get('change_30d_pct'), ' %')}) |"
            )

    lines += [
        "",
        "## Systemhebel (Crypto-Pendant zur Verschuldung)",
        "",
        "| Groesse | Wert | Einordnung |",
        "|---|---|---|",
        f"| Funding annualisiert | {_fmt(lev['funding_annualized_pct'], ' %')} | "
        f"{_pct_label(lev['funding_percentile'])} |",
        f"| Funding 7-Tage-Schnitt annualisiert | {_fmt(lev['funding_avg_7d_annualized_pct'], ' %')} | |",
        f"| Open Interest | {_fmt(lev['open_interest_usd'], ' USD')} | "
        f"30 Tage {_fmt(lev['open_interest_change_30d_pct'], ' %')} |",
        f"| Long/Short-Ratio | {_fmt(lev['long_short_ratio'])} | "
        f"{_pct_label(lev['long_short_percentile'])} |",
        "",
        "## Sentiment (Crypto-Pendant zu Analystenzielen)",
        "",
    ]
    if not sent.get("available"):
        lines += [f"**Nicht messbar** — {sent.get('reason')}.", ""]
    else:
        lines += [
            f"Fear & Greed **{sent['fear_greed']}** — {_pct_label(sent['fear_greed_percentile'])}, "
            f"30-Tage-Veraenderung {_fmt(sent.get('fear_greed_change_30d'), '', 0)}. "
            f"Geltungsbereich: {sent['scope']}.",
            "",
        ]

    cov = result["coverage"]
    lines += ["## Datenabdeckung", "", f"Geladen: {', '.join(cov['fetched']) or 'nichts'}.", ""]
    if cov["unavailable"]:
        lines += ["**Nicht verfuegbar:**", ""]
        lines += [f"- `{k}` — {v}" for k, v in cov["unavailable"].items()]
        lines.append("")
    lines += ["**Strukturelle Luecken ohne kostenlose Quelle:**", ""]
    lines += [f"- {v}" for v in result["known_gaps"].values()]
    lines += [
        "",
        "---",
        "",
        "Dieser Report enthaelt bewusst **kein** Rating. Die Einschaetzung entsteht erst, wenn "
        "Narrativ, Katalysatoren und Wettbewerbsumfeld per WebSearch dazukommen — siehe SKILL.md.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ticker", required=True, help="z.B. BTC, ETH, SOL")
    ap.add_argument("--output-dir", type=Path, default=Path("reports"))
    ap.add_argument("--input-json", type=Path, help="Offline-Snapshot statt Netzwerkzugriff")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    ticker = args.ticker.strip().upper()
    if args.input_json:
        data = json.loads(args.input_json.read_text(encoding="utf-8"))
        log = ds.FetchLog(ok=["input_json"], failed={})
        data.setdefault("ticker", ticker)
    else:
        try:
            data, log = ds.collect(ticker, days=args.days, quiet=args.quiet)
        except KeyError as exc:
            print(f"FEHLER: {exc}", file=sys.stderr)
            return 2

    result = analyse(data, log)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    json_path = args.output_dir / f"crypto_asset_{ticker.lower()}_{stamp}.json"
    md_path = args.output_dir / f"crypto_asset_{ticker.lower()}_{stamp}.md"
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")

    print(f"  {json_path}")
    print(f"  {md_path}")
    if log.failed:
        print(f"  {len(log.failed)} Quelle(n) nicht verfuegbar: {', '.join(sorted(log.failed))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
