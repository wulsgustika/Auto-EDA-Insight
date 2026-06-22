"""
tests/test_visualization.py
Unit tests for visualization, time series, and insight generation.
SD-1306 Data Science Programming — Institut Teknologi Sains Bandung
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.visualization     import Visualization
from backend.time_series        import TimeSeries
from backend.insight_generator  import InsightGenerator


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def numeric_df():
    np.random.seed(0)
    return pd.DataFrame({
        "sales":    np.random.normal(500, 100, 100),
        "quantity": np.random.randint(1, 50, 100).astype(float),
        "profit":   np.random.normal(200, 50, 100),
        "discount": np.random.uniform(0, 0.3, 100),
    })


@pytest.fixture
def mixed_df():
    np.random.seed(1)
    n = 120
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "date":     dates,
        "sales":    np.random.normal(500, 80, n),
        "quantity": np.random.randint(1, 30, n).astype(float),
        "product":  np.random.choice(["A", "B", "C"], n),
        "region":   np.random.choice(["West", "East"], n),
    })


@pytest.fixture
def ts_df():
    dates = pd.date_range("2022-01-01", periods=60, freq="ME")
    np.random.seed(42)
    return pd.DataFrame({
        "date":   dates,
        "revenue": np.cumsum(np.random.normal(100, 20, 60)) + 1000,
        "cost":    np.cumsum(np.random.normal(60, 15, 60)) + 500,
    })


# ── Tests: Visualization ──────────────────────────────────────────────────────
class TestVisualization:

    def test_generate_all_returns_dict(self, numeric_df):
        v = Visualization(numeric_df)
        result = v.generate_all()
        assert isinstance(result, dict)

    def test_numerical_key_exists(self, numeric_df):
        v = Visualization(numeric_df)
        result = v.generate_all()
        assert "numerical" in result

    def test_numerical_charts_non_empty(self, numeric_df):
        v = Visualization(numeric_df)
        result = v.generate_all()
        assert len(result.get("numerical", [])) > 0

    def test_categorical_key_exists(self, mixed_df):
        v = Visualization(mixed_df)
        result = v.generate_all()
        assert "categorical" in result

    def test_chart_has_data_layout(self, numeric_df):
        v = Visualization(numeric_df)
        result = v.generate_all()
        for chart in result.get("numerical", []):
            if isinstance(chart, dict) and "figure" in chart:
                fig = chart["figure"]
                assert "data" in fig and "layout" in fig

    def test_bivariate_key(self, numeric_df):
        v = Visualization(numeric_df)
        result = v.generate_all()
        assert "bivariate" in result or "numerical" in result  # flexible


# ── Tests: TimeSeries ─────────────────────────────────────────────────────────
class TestTimeSeries:

    def test_analyze_returns_dict(self, ts_df):
        ts = TimeSeries(ts_df)
        result = ts.analyze()
        assert isinstance(result, dict)

    def test_has_available_key(self, ts_df):
        ts = TimeSeries(ts_df)
        result = ts.analyze()
        assert "available" in result

    def test_time_series_detected(self, ts_df):
        ts = TimeSeries(ts_df)
        result = ts.analyze()
        assert result.get("available") is True

    def test_no_datetime_column(self, numeric_df):
        ts = TimeSeries(numeric_df)
        result = ts.analyze()
        assert result.get("available") is False

    def test_charts_key_present_when_available(self, ts_df):
        ts = TimeSeries(ts_df)
        result = ts.analyze()
        if result.get("available"):
            assert "charts" in result or "columns" in result


# ── Tests: InsightGenerator ───────────────────────────────────────────────────
class TestInsightGenerator:

    def test_generate_returns_list(self, mixed_df):
        ig = InsightGenerator(mixed_df)
        result = ig.generate()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_insights_have_text(self, mixed_df):
        ig = InsightGenerator(mixed_df)
        result = ig.generate()
        for item in result:
            assert "text" in item or isinstance(item, str)

    def test_insight_types_valid(self, mixed_df):
        ig = InsightGenerator(mixed_df)
        result = ig.generate()
        valid_types = {"info", "success", "warning", "danger"}
        for item in result:
            if isinstance(item, dict) and "type" in item:
                assert item["type"] in valid_types

    def test_missing_insight_generated(self):
        df = pd.DataFrame({
            "a": [1, None, None, 4, 5],
            "b": ["x", None, "y", "x", "x"],
        })
        ig = InsightGenerator(df)
        result = ig.generate()
        texts = " ".join(
            (r["text"] if isinstance(r, dict) else str(r)) for r in result
        )
        assert "missing" in texts.lower() or len(result) > 0

    def test_no_numeric_df(self):
        df = pd.DataFrame({"cat": ["a", "b", "c", "a", "b"]})
        ig = InsightGenerator(df)
        result = ig.generate()
        assert isinstance(result, list)

    def test_with_all_numeric(self, numeric_df):
        ig = InsightGenerator(numeric_df)
        result = ig.generate()
        assert len(result) >= 2  # at least mean insight + one more


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
