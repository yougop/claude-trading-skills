"""Tests for the core diagnostic - the quadrant verdict.

Two boundaries are worth more than the happy path here.

The diagnostic must REFUSE to answer when the two usage series contradict each
other, and when there is no on-chain data at all. A forced quadrant would be
worse than none, because the point of the section is to be the line a reader
trusts at a glance.

It must equally refuse to refuse. A sideways price is the normal state of a
ranging market, and answering "unklar" there throws away the usage half, which
is the half that still says something. Every combination except contradictory
usage therefore carries its own reading.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import crypto_asset_analysis as caa  # noqa: E402


def _series(start: float, step: float, n: int = 60) -> list[float]:
    return [start + step * i for i in range(n)]


def _data(price_step: float, fee_step: float, addr_step: float) -> dict:
    return {
        "ticker": "BTC",
        "history": {"prices": _series(60_000.0, price_step)},
        "onchain": {
            "fees_usd": _series(200_000.0, fee_step),
            "active_addresses": _series(480_000.0, addr_step),
            # Present but deliberately ignored by the diagnostic.
            "tx_count": _series(680_000.0, -5_000.0),
            "hash_rate": _series(925_000_000.0, -5_000_000.0),
        },
    }


class TestQuadrantClassification:
    def test_price_up_usage_up_is_confirmed(self):
        d = caa.build_core_diagnostic(_data(100.0, 2_000.0, 3_000.0))
        assert d["quadrant"] == "bestaetigt"
        assert d["price_trend_30d"] == "rising"
        assert d["usage_verdict"] == "rising"

    def test_price_up_usage_down_is_the_warning(self):
        d = caa.build_core_diagnostic(_data(100.0, -2_000.0, -3_000.0))
        assert d["quadrant"] == "warnung_bewertung_ohne_nutzung"
        assert "wichtigste Warnung" in d["reading"]

    def test_price_down_usage_up_is_the_mean_reversion_case(self):
        d = caa.build_core_diagnostic(_data(-100.0, 2_000.0, 3_000.0))
        assert d["quadrant"] == "konstruktiv_mean_reversion"
        assert "Mean Reversion" in d["reading"]

    def test_price_down_usage_down_is_a_failing_network(self):
        d = caa.build_core_diagnostic(_data(-100.0, -2_000.0, -3_000.0))
        assert d["quadrant"] == "netzwerk_verliert_geschaeft"


class TestRefusalCases:
    def test_disagreeing_usage_series_produce_no_quadrant(self):
        # Fees up, addresses down. Forcing a verdict here would invent one.
        # This is the ONLY case that may fall through to "unklar".
        d = caa.build_core_diagnostic(_data(-100.0, 2_000.0, -3_000.0))
        assert d["usage_verdict"] == "mixed"
        assert d["quadrant"] == "unklar"
        assert "verschiedene Richtungen" in d["reading"]

    def test_flat_price_still_gets_a_reading(self):
        # A ranging price is the normal state of a sideways market. Answering
        # "unklar" here would discard the usage signal, which is the half that
        # actually says something.
        d = caa.build_core_diagnostic(_data(0.0, 2_000.0, 3_000.0))
        assert d["price_trend_30d"] == "flat"
        assert d["quadrant"] == "aufbau_unter_seitwaertskurs"
        assert "Basisbildung" in d["reading"]

    def test_flat_price_with_eroding_usage_is_a_warning(self):
        d = caa.build_core_diagnostic(_data(0.0, -2_000.0, -3_000.0))
        assert d["quadrant"] == "warnung_nutzung_erodiert"

    def test_every_non_mixed_combination_has_its_own_reading(self):
        # Guards against a combination silently collapsing into the default.
        for price in ("rising", "falling", "flat"):
            for usage in ("rising", "falling", "flat"):
                assert (price, usage) in caa.QUADRANTS
        readings = [r for _k, r in caa.QUADRANTS.values()]
        assert len(set(readings)) == len(readings)

    def test_one_series_flat_does_not_block_the_verdict(self):
        # Fees clearly rising, addresses sideways -> still "rising", because
        # sideways is not a contradiction, only an absence of confirmation.
        d = caa.build_core_diagnostic(_data(-100.0, 2_000.0, 0.0))
        assert d["usage_verdict"] == "rising"
        assert d["quadrant"] == "konstruktiv_mean_reversion"

    def test_altcoin_without_onchain_is_unavailable(self):
        d = caa.build_core_diagnostic(
            {"ticker": "SOL", "history": {"prices": _series(150.0, 1.0)}, "onchain": {}}
        )
        assert d["available"] is False
        assert "Bitcoin" in d["reason"]

    def test_short_price_history_is_unavailable(self):
        d = caa.build_core_diagnostic(
            {"ticker": "BTC", "history": {"prices": [60_000.0] * 5}, "onchain": {"fees_usd": [1.0]}}
        )
        assert d["available"] is False


class TestExcludedSeries:
    def test_tx_count_and_hash_rate_are_not_part_of_the_verdict(self):
        # Both excluded series fall hard in the fixture; the verdict must still
        # follow fees and addresses only. Batching distorts tx count and hash
        # rate follows mining economics, so neither is a demand signal.
        d = caa.build_core_diagnostic(_data(-100.0, 2_000.0, 3_000.0))
        assert set(d["usage"]) == {"fees_usd", "active_addresses"}
        assert d["quadrant"] == "konstruktiv_mean_reversion"

    def test_basis_note_names_the_exclusion(self):
        d = caa.build_core_diagnostic(_data(-100.0, 2_000.0, 3_000.0))
        assert "Hash-Rate" in d["basis"]


class TestRendering:
    def test_section_leads_the_report(self):
        result = caa.analyse(_data(-100.0, 2_000.0, 3_000.0), caa.ds.FetchLog())
        md = caa.render_markdown(result)
        assert "## Kerndiagnose" in md
        # It must come before every other section, not be buried.
        assert md.index("## Kerndiagnose") < md.index("## Kursstruktur")

    def test_unavailable_diagnostic_is_stated_as_a_real_gap(self):
        lines = caa._render_core_diagnostic({"available": False, "reason": "kein Bitcoin"})
        text = "\n".join(lines)
        assert "Nicht beantwortbar" in text
        assert "echte Luecke" in text

    def test_analyse_always_includes_the_diagnostic_key(self):
        result = caa.analyse({"ticker": "SOL", "history": {}, "onchain": {}}, caa.ds.FetchLog())
        assert "core_diagnostic" in result
        assert result["core_diagnostic"]["available"] is False
