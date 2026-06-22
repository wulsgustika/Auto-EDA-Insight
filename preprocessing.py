"""
backend/preprocessing.py
Data preprocessing utilities: cleaning, imputation, encoding.
SD-1306 Data Science Programming — Institut Teknologi Sains Bandung
"""

import numpy as np
import pandas as pd


class Preprocessing:
    """Handles data cleaning and transformation before analysis."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    # ── Missing Value Handling ──────────────────────────────────────────────
    def fill_numeric_mean(self) -> "Preprocessing":
        """Fill missing numeric values with column mean."""
        num_cols = self.df.select_dtypes(include="number").columns
        for col in num_cols:
            self.df[col].fillna(self.df[col].mean(), inplace=True)
        return self

    def fill_numeric_median(self) -> "Preprocessing":
        """Fill missing numeric values with column median."""
        num_cols = self.df.select_dtypes(include="number").columns
        for col in num_cols:
            self.df[col].fillna(self.df[col].median(), inplace=True)
        return self

    def fill_categorical_mode(self) -> "Preprocessing":
        """Fill missing categorical values with column mode."""
        cat_cols = self.df.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            mode = self.df[col].mode()
            if not mode.empty:
                self.df[col].fillna(mode.iloc[0], inplace=True)
        return self

    def drop_missing_rows(self, threshold: float = 0.5) -> "Preprocessing":
        """Drop rows where fraction of missing values exceeds threshold."""
        n_cols = len(self.df.columns)
        self.df.dropna(thresh=int(n_cols * (1 - threshold)), inplace=True)
        return self

    def drop_missing_cols(self, threshold: float = 0.8) -> "Preprocessing":
        """Drop columns where fraction of missing values exceeds threshold."""
        missing_frac = self.df.isnull().mean()
        drop_cols = missing_frac[missing_frac > threshold].index.tolist()
        self.df.drop(columns=drop_cols, inplace=True)
        return self

    # ── Duplicate Handling ──────────────────────────────────────────────────
    def drop_duplicates(self) -> "Preprocessing":
        """Remove duplicate rows."""
        self.df.drop_duplicates(inplace=True)
        self.df.reset_index(drop=True, inplace=True)
        return self

    # ── Outlier Handling ────────────────────────────────────────────────────
    def clip_outliers_iqr(self, multiplier: float = 1.5) -> "Preprocessing":
        """Clip numeric outliers using IQR method."""
        num_cols = self.df.select_dtypes(include="number").columns
        for col in num_cols:
            q1 = self.df[col].quantile(0.25)
            q3 = self.df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - multiplier * iqr
            upper = q3 + multiplier * iqr
            self.df[col] = self.df[col].clip(lower=lower, upper=upper)
        return self

    # ── Type Conversion ─────────────────────────────────────────────────────
    def convert_datetime(self, columns: list = None) -> "Preprocessing":
        """Convert specified columns (or auto-detect) to datetime."""
        cols = columns or self.df.select_dtypes(include="object").columns.tolist()
        for col in cols:
            try:
                converted = pd.to_datetime(self.df[col], infer_datetime_format=True)
                self.df[col] = converted
            except Exception:
                pass
        return self

    # ── Encoding ────────────────────────────────────────────────────────────
    def label_encode(self, columns: list = None) -> "Preprocessing":
        """Label encode categorical columns."""
        cols = columns or self.df.select_dtypes(include=["object", "category"]).columns.tolist()
        for col in cols:
            self.df[col] = pd.Categorical(self.df[col]).codes
        return self

    # ── Column Cleaning ─────────────────────────────────────────────────────
    def clean_column_names(self) -> "Preprocessing":
        """Normalize column names: lowercase, replace spaces with underscores."""
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^\w]", "_", regex=True)
            .str.replace(r"_+", "_", regex=True)
            .str.strip("_")
        )
        return self

    # ── Summary ─────────────────────────────────────────────────────────────
    def missing_summary(self) -> pd.DataFrame:
        """Return a DataFrame summarising missing values per column."""
        total   = len(self.df)
        missing = self.df.isnull().sum()
        pct     = (missing / total * 100).round(2)
        return pd.DataFrame({
            "column":        self.df.columns.tolist(),
            "missing_count": missing.values,
            "missing_pct":   pct.values,
            "dtype":         [str(t) for t in self.df.dtypes.values],
        }).sort_values("missing_count", ascending=False).reset_index(drop=True)

    # ── Finalize ────────────────────────────────────────────────────────────
    def get_result(self) -> pd.DataFrame:
        """Return the cleaned DataFrame."""
        return self.df.reset_index(drop=True)
