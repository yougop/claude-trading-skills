"""Tests for the data layer - offline, no network.

The point of these is that a provider outage must never become an exception,
and a short or implausible response must never pass silently. Both failure
modes have already cost us something in this workspace.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import data_sources as ds  # noqa: E402


class TestAssetResolution:
    def test_known_ticker_resolves(self):
        ids = ds.resolve_asset("btc")
        assert ids["coingecko"] == "bitcoin"
        assert ids["binance"] == "BTCUSDT"
        assert ids["ticker"] == "BTC"

    def test_unknown_ticker_raises_with_the_known_list(self):
        with pytest.raises(KeyError) as exc:
            ds.resolve_asset("NOTACOIN")
        assert "BTC" in str(exc.value)

    def test_only_bitcoin_claims_onchain_coverage(self):
        onchain_capable = [t for t, v in ds.ASSET_MAP.items() if v.get("onchain")]
        assert onchain_capable == ["BTC"]


class TestFetchLog:
    def test_records_success_and_failure_separately(self):
        log = ds.FetchLog()
        log.succeed("a")
        log.fail("b", "kaputt")
        out = log.as_dict()
        assert out["fetched"] == ["a"]
        assert out["unavailable"] == {"b": "kaputt"}

    def test_output_is_sorted_for_stable_reports(self):
        log = ds.FetchLog()
        for name in ("z", "a", "m"):
            log.succeed(name)
        assert log.as_dict()["fetched"] == ["a", "m", "z"]


class TestPriceSanity:
    def test_plausible_btc_price_passes(self):
        assert ds._sanity_check_price("BTC", 63_000.0) is None

    def test_the_28_dollar_bitcoin_is_caught(self):
        # FMP served exactly this on 2026-08-14 and the charts were wrong for a day.
        complaint = ds._sanity_check_price("BTC", 28.0)
        assert complaint is not None and "Plausibilitaets" in complaint

    def test_asset_without_a_band_is_not_judged(self):
        assert ds._sanity_check_price("SOL", 0.01) is None

    def test_missing_price_is_not_a_complaint(self):
        assert ds._sanity_check_price("BTC", None) is None


class TestSeriesLengthCheck:
    def test_full_series_passes_quietly(self):
        log = ds.FetchLog()
        ds._check_series_length("fear_greed", list(range(365)), 365, log)
        assert log.failed == {}

    def test_single_value_response_is_flagged(self):
        # The Fear & Greed trailing-slash bug: HTTP 200, valid JSON, one day.
        log = ds.FetchLog()
        ds._check_series_length("fear_greed", [29], 365, log)
        assert "fear_greed_kurz" in log.failed
        assert "1 von 365" in log.failed["fear_greed_kurz"]

    def test_short_but_usable_series_passes(self):
        # 30 observations is the floor the percentile function needs.
        log = ds.FetchLog()
        ds._check_series_length("oi", list(range(30)), 365, log)
        assert log.failed == {}

    def test_request_smaller_than_the_floor_is_judged_against_the_request(self):
        log = ds.FetchLog()
        ds._check_series_length("oi", list(range(10)), 10, log)
        assert log.failed == {}

    def test_non_list_is_ignored(self):
        log = ds.FetchLog()
        ds._check_series_length("x", None, 365, log)
        assert log.failed == {}


class TestGapDeclaration:
    def test_known_gaps_are_named_not_hidden(self):
        assert "mvrv" in ds.ONCHAIN_GAPS
        assert all(isinstance(v, str) and v for v in ds.ONCHAIN_GAPS.values())

    def test_fear_greed_url_keeps_its_trailing_slash(self):
        # Without it the redirect drops the query string and the limit is lost.
        assert ds.FNG_BASE.endswith("/")


class TestCollectDegradesGracefully:
    def test_provider_outage_is_logged_not_raised(self, monkeypatch):
        def boom(*_args, **_kwargs):
            raise ConnectionError("Netz weg")

        for name in (
            "fetch_asset_profile",
            "fetch_market_history",
            "fetch_funding_history",
            "fetch_open_interest_history",
            "fetch_long_short_ratio",
            "fetch_fear_greed",
            "fetch_onchain_series",
        ):
            monkeypatch.setattr(ds, name, boom)

        data, log = ds.collect("BTC")

        assert data["ticker"] == "BTC"
        assert log.ok == []
        assert log.failed  # every source recorded a reason
        assert all("ConnectionError" in reason for reason in log.failed.values())

    def test_altcoin_gets_an_explicit_onchain_gap(self, monkeypatch):
        monkeypatch.setattr(ds, "fetch_asset_profile", lambda *_a, **_k: {})
        monkeypatch.setattr(ds, "fetch_market_history", lambda *_a, **_k: {"prices": []})
        monkeypatch.setattr(ds, "fetch_funding_history", lambda *_a, **_k: [])
        monkeypatch.setattr(ds, "fetch_open_interest_history", lambda *_a, **_k: {})
        monkeypatch.setattr(ds, "fetch_long_short_ratio", lambda *_a, **_k: [])
        monkeypatch.setattr(ds, "fetch_fear_greed", lambda *_a, **_k: [])

        _data, log = ds.collect("SOL")

        assert "onchain" in log.failed
        assert "Bitcoin" in log.failed["onchain"]

    def test_btc_skips_its_own_benchmark(self, monkeypatch):
        monkeypatch.setattr(ds, "fetch_asset_profile", lambda *_a, **_k: {})
        monkeypatch.setattr(ds, "fetch_market_history", lambda *_a, **_k: {"prices": [1.0]})
        monkeypatch.setattr(ds, "fetch_funding_history", lambda *_a, **_k: [])
        monkeypatch.setattr(ds, "fetch_open_interest_history", lambda *_a, **_k: {})
        monkeypatch.setattr(ds, "fetch_long_short_ratio", lambda *_a, **_k: [])
        monkeypatch.setattr(ds, "fetch_fear_greed", lambda *_a, **_k: [])
        monkeypatch.setattr(ds, "fetch_onchain_series", lambda *_a, **_k: [1.0])

        data, log = ds.collect("BTC")

        assert data["benchmark_prices"] == []
        assert "benchmark_btc" not in log.ok
