"""
backend/categorical_analysis.py
Advanced descriptive statistics for categorical variables.
"""

import pandas as pd


class CategoricalAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def compute(self) -> list:
        cat_cols = self.df.select_dtypes(include=["object", "category"]).columns.tolist()
        results  = []

        for col in cat_cols:
            s       = self.df[col]
            n_total = len(s)
            n_valid = s.notna().sum()
            vc      = s.value_counts(dropna=True)

            mode_val  = vc.index[0]  if len(vc) > 0 else None
            mode_freq = int(vc.iloc[0]) if len(vc) > 0 else 0
            mode_pct  = round(mode_freq / n_total * 100, 2) if n_total > 0 else 0

            top_n  = min(10, len(vc))
            top_vc = vc.head(top_n)
            top_values = [
                {"value": str(v), "count": int(c), "pct": round(c / n_total * 100, 1)}
                for v, c in zip(top_vc.index, top_vc.values)
            ]

            results.append({
                "column"       : col,
                "count"        : int(n_valid),
                "unique"       : int(s.nunique(dropna=True)),
                "mode"         : str(mode_val) if mode_val is not None else None,
                "mode_freq"    : mode_freq,
                "mode_pct"     : mode_pct,
                "missing_count": int(n_total - n_valid),
                "missing_pct"  : round((n_total - n_valid) / n_total * 100, 2) if n_total else 0,
                "top_values"   : top_values,
            })

        return results
