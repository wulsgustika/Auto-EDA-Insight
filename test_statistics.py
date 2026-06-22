"""
tests/test_statistics.py
Unit tests for descriptive statistics and categorical analysis.
SD-1306 Data Science Programming — Institut Teknologi Sains Bandung
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.descriptive_stats   import DescriptiveStats
from backend.categorical_analysis import CategoricalAnalysis
from backend.preprocessing        import Preprocessing


# ── Fixtures ─────────────────────────────────────────────────────────────────
@pytest.fixture
def sample_df():
    np.random.seed(42)
    return pd.DataFrame({
        "sales":    np.random.normal(500, 100, 200),
        "quantity": np.random.randint(1, 50, 200).astype(float),
        "discount": np.random.uniform(0, 0.3, 200),
        "product":  np.random.choice(["Laptop", "Phone", "Tablet"], 200),
        "region":   np.random.choice(["Jakarta", "Bandung", "Surabaya"], 200),
    })


@pytest.fixture
def df_with_missing(sample_df):
    df = sample_df.copy()
    df.loc[::10, "sales"]   = np.nan   # 10% missing
    df.loc[::20, "product"] = np.nan   # 5% missing
    return df


# ── Tests: DescriptiveStats ───────────────────────────────────────────────────
class TestDescriptiveStats:

    def test_returns_list(self, sample_df):
        ds = DescriptiveStats(sample_df)
        result = ds.compute()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_required_keys(self, sample_df):
        ds = DescriptiveStats(sample_df)
        result = ds.compute()
        required = {"column", "mean", "median", "min", "max", "std", "variance",
                    "mode", "skewness", "kurtosis", "missing_count", "missing_pct",
                    "normality", "outliers"}
        for row in result:
            assert required.issubset(set(row.keys())), f"Missing keys in {row['column']}"

    def test_mean_correct(self, sample_df):
        ds = DescriptiveStats(sample_df)
        result = ds.compute()
        for row in result:
            if row["column"] == "sales":
                expected = round(float(sample_df["sales"].mean()), 4)
                assert abs(row["mean"] - expected) < 0.01

    def test_normality_values(self, sample_df):
        ds = DescriptiveStats(sample_df)
        result = ds.compute()
        valid = {"Normal", "Not Normal", "Large Sample", "Unknown"}
        for row in result:
            assert row["normality"] in valid

    def test_missing_values_counted(self, df_with_missing):
        ds = DescriptiveStats(df_with_missing)
        result = ds.compute()
        sales_row = next((r for r in result if r["column"] == "sales"), None)
        assert sales_row is not None
        assert sales_row["missing_count"] > 0

    def test_outliers_non_negative(self, sample_df):
        ds = DescriptiveStats(sample_df)
        result = ds.compute()
        for row in result:
            assert row["outliers"] >= 0

    def test_no_numeric_cols(self):
        df = pd.DataFrame({"cat": ["a", "b", "c"]})
        ds = DescriptiveStats(df)
        assert ds.compute() == []


# ── Tests: CategoricalAnalysis ────────────────────────────────────────────────
class TestCategoricalAnalysis:

    def test_returns_list(self, sample_df):
        ca = CategoricalAnalysis(sample_df)
        result = ca.compute()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_required_keys(self, sample_df):
        ca = CategoricalAnalysis(sample_df)
        result = ca.compute()
        required = {"column", "count", "unique", "mode", "mode_freq",
                    "mode_pct", "missing_count", "missing_pct"}
        for row in result:
            assert required.issubset(set(row.keys()))

    def test_unique_count(self, sample_df):
        ca = CategoricalAnalysis(sample_df)
        result = ca.compute()
        prod_row = next((r for r in result if r["column"] == "product"), None)
        assert prod_row is not None
        assert prod_row["unique"] == 3

    def test_mode_pct_range(self, sample_df):
        ca = CategoricalAnalysis(sample_df)
        result = ca.compute()
        for row in result:
            assert 0 <= row["mode_pct"] <= 100

    def test_top_values_structure(self, sample_df):
        ca = CategoricalAnalysis(sample_df)
        result = ca.compute()
        for row in result:
            for tv in row.get("top_values", []):
                assert "value" in tv and "count" in tv and "pct" in tv

    def test_missing_categorical(self, df_with_missing):
        ca = CategoricalAnalysis(df_with_missing)
        result = ca.compute()
        prod_row = next((r for r in result if r["column"] == "product"), None)
        assert prod_row is not None
        assert prod_row["missing_count"] > 0


# ── Tests: Preprocessing ──────────────────────────────────────────────────────
class TestPreprocessing:

    def test_fill_numeric_mean(self, df_with_missing):
        pre = Preprocessing(df_with_missing)
        result = pre.fill_numeric_mean().get_result()
        assert result["sales"].isnull().sum() == 0

    def test_fill_categorical_mode(self, df_with_missing):
        pre = Preprocessing(df_with_missing)
        result = pre.fill_categorical_mode().get_result()
        assert result["product"].isnull().sum() == 0

    def test_drop_duplicates(self):
        df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
        pre = Preprocessing(df)
        result = pre.drop_duplicates().get_result()
        assert result.shape[0] == 2

    def test_clean_column_names(self):
        df = pd.DataFrame({"First Name": [1], "Last-Name": [2], "  Age  ": [3]})
        pre = Preprocessing(df)
        result = pre.clean_column_names().get_result()
        assert list(result.columns) == ["first_name", "last_name", "age"]

    def test_missing_summary_shape(self, df_with_missing):
        pre = Preprocessing(df_with_missing)
        summary = pre.missing_summary()
        assert summary.shape[1] == 4  # column, missing_count, missing_pct, dtype


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
