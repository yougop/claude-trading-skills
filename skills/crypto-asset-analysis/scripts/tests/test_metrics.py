"""Tests for the pure metric functions.

Emphasis is on the cases that produced real defects elsewhere in this toolbox:
a metric that silently returns a number when it has no basis for one, and a
relative-strength calculation that compares a series against itself.
"""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import metrics as m  # noqa: E402


class TestPercentileRank:
    def test_midpoint_of_uniform_history(self):
        assert m.percentile_rank(list(range(100)), 50) == pytest.approx(50.5, abs=0.6)

    def test_value_above_all_history(self):
        assert m.percentile_rank(list(range(100)), 999) == 100.0

    def test_value_below_all_history(self):
        assert m.percentile_rank(list(range(100)), -999) == 0.0

    def test_ties_count_half(self):
        # Every observation identical -> the value sits in the middle, not at an edge.
        assert m.percentile_rank([5.0] * 50, 5.0) == 50.0

    def test_short_history_returns_none_rather_than_a_guess(self):
        assert m.percentile_rank([1, 2, 3], 2) is None
        assert m.percentile_rank(list(range(29)), 10) is None
        assert m.percentile_rank(list(range(30)), 10) is not None

    def test_ignores_nones_and_nans(self):
        history = [None, float("nan"), *range(40)]
        assert m.percentile_rank(history, 20) is not None

    def test_missing_value_returns_none(self):
        assert m.percentile_rank(list(range(100)), None) is None


class TestRelativeStrength:
    def test_outperformance_is_positive(self):
        asset = [100.0 * 1.01**i for i in range(100)]
        bench = [100.0 * 1.005**i for i in range(100)]
        assert m.relative_strength(asset, bench, 90) > 0

    def test_series_against_itself_returns_none(self):
        # This is the BTC-vs-BTC defect: a structural zero that reads as
        # weakness. It must be refused, not reported.
        series = [100.0 * 1.01**i for i in range(100)]
        assert m.relative_strength(series, list(series), 90) is None

    def test_empty_benchmark_returns_none(self):
        assert m.relative_strength([1.0] * 100, [], 90) is None


class TestVolatility:
    def test_annualises_on_365_days_not_252(self):
        # Constant 1% daily moves, alternating sign.
        prices = [100.0]
        for i in range(60):
            prices.append(prices[-1] * (1.01 if i % 2 else 0.99))
        vol = m.realized_volatility(prices, 30)
        daily = math.sqrt(sum((math.log(1.01), math.log(0.99))[i % 2] ** 2 for i in range(2)) / 2)
        assert vol == pytest.approx(daily * math.sqrt(365) * 100, rel=0.25)

    def test_too_short_returns_none(self):
        assert m.realized_volatility([100.0] * 10, 30) is None


class TestDrawdown:
    def test_current_drawdown_from_peak(self):
        assert m.drawdown_from_high([100.0, 200.0, 150.0]) == 25.0

    def test_at_the_high_is_zero(self):
        assert m.drawdown_from_high([100.0, 150.0, 200.0]) == 0.0

    def test_max_drawdown_finds_worst_trough_not_the_last(self):
        # 100 -> 40 is a 60% drop; the later 90 -> 81 is only 10%.
        assert m.max_drawdown([100.0, 40.0, 90.0, 81.0]) == 60.0


class TestFunding:
    def test_exchange_default_annualises_to_about_eleven_percent(self):
        assert m.funding_annualized(0.0001) == pytest.approx(10.95, abs=0.01)

    def test_negative_funding_stays_negative(self):
        assert m.funding_annualized(-0.0001) < 0

    def test_none_propagates(self):
        assert m.funding_annualized(None) is None


class TestNvt:
    def test_ratio_is_cap_over_volume(self):
        assert m.nvt(1_000_000.0, 10_000.0) == 100.0

    def test_zero_volume_returns_none_not_infinity(self):
        assert m.nvt(1_000_000.0, 0.0) is None

    def test_signal_smooths_the_denominator(self):
        # A realistic quiet/busy swing: one day settles 3x the usual volume.
        # Raw NVT drops by two thirds on that day alone; the smoothed version
        # barely moves. That difference is the whole reason NVT Signal exists.
        caps = [1_000_000.0] * 100
        steady = [10_000.0] * 100
        spiked = [10_000.0] * 99 + [30_000.0]

        baseline = m.nvt_signal(caps, steady, window=90)
        assert m.nvt(caps[-1], spiked[-1]) == pytest.approx(baseline / 3, rel=0.01)

        smoothed = m.nvt_signal(caps, spiked, window=90)
        assert smoothed == pytest.approx(baseline, rel=0.03)

    def test_signal_still_reflects_a_sustained_shift(self):
        # Smoothing must dampen noise without blinding the metric: a volume
        # level that halves and stays halved has to show up.
        caps = [1_000_000.0] * 200
        steady = [10_000.0] * 200
        halved = [10_000.0] * 110 + [5_000.0] * 90
        assert m.nvt_signal(caps, halved, 90) == pytest.approx(
            m.nvt_signal(caps, steady, 90) * 2, rel=0.01
        )


class TestTrendDirection:
    def test_rising_series(self):
        assert m.trend_direction([float(i) for i in range(50)], 30) == "rising"

    def test_falling_series(self):
        assert m.trend_direction([float(-i) for i in range(50)], 30) == "falling"

    def test_constant_series_is_flat(self):
        assert m.trend_direction([100.0] * 50, 30) == "flat"

    def test_tiny_noise_is_flat_not_a_trend(self):
        series = [100.0 + (0.001 if i % 2 else 0.0) for i in range(50)]
        assert m.trend_direction(series, 30) == "flat"


class TestSupplyIssuance:
    def test_capped_supply(self):
        assert m.supply_issuance_pct(19_000_000.0, 21_000_000.0) == pytest.approx(90.48, abs=0.01)

    def test_uncapped_supply_returns_none_not_zero(self):
        # ETH has no max supply; reporting 0% would imply nothing is issued.
        assert m.supply_issuance_pct(120_000_000.0, None) is None
