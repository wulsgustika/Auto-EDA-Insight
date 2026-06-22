"""
backend/descriptive_stats.py
Advanced descriptive statistics for numerical variables.
"""

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


class DescriptiveStats:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def compute(self) -> list:
        num_cols = self.df.select_dtypes(include="number").columns.tolist()
        results  = []

        for col in num_cols:
            s      = self.df[col].dropna()
            n_total = len(self.df[col])
            n_valid = len(s)

            if n_valid < 2:
                continue

            # IQR-based outlier count
            q1, q3  = s.quantile([0.25, 0.75])
            iqr     = q3 - q1
            n_out   = int(((s < (q1 - 1.5 * iqr)) | (s > (q3 + 1.5 * iqr))).sum())

            # Normality test (Shapiro if n<=5000 else skip → 'Large Sample')
            if n_valid <= 5000:
                try:
                    _, p_val = sp_stats.shapiro(s[:5000])
                    normality = "Normal" if p_val > 0.05 else "Not Normal"
                except Exception:
                    normality = "Unknown"
            else:
                normality = "Large Sample"

            # Mode
            mode_val = float(s.mode().iloc[0]) if not s.mode().empty else None

            results.append({
                "column"      : col,
                "count"       : n_valid,
                "mean"        : self._r(float(s.mean())),
                "median"      : self._r(float(s.median())),
                "min"         : self._r(float(s.min())),
                "max"         : self._r(float(s.max())),
                "std"         : self._r(float(s.std())),
                "variance"    : self._r(float(s.var())),
                "mode"        : self._r(mode_val),
                "skewness"    : self._r(float(s.skew())),
                "kurtosis"    : self._r(float(s.kurt())),
                "q1"          : self._r(float(q1)),
                "q3"          : self._r(float(q3)),
                "missing_count": n_total - n_valid,
                "missing_pct" : self._r((n_total - n_valid) / n_total * 100),
                "normality"   : normality,
                "outliers"    : n_out,
            })

        return results

    @staticmethod
    def _r(v, digits=4):
        if v is None:
            return None
        return round(v, digits)
