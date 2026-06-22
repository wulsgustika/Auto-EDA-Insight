"""
backend/insight_generator.py
Automatically generates intelligent data insights focused on data content.
"""

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


class InsightGenerator:
    def __init__(self, df: pd.DataFrame):
        self.df       = df
        self.num_cols = df.select_dtypes(include="number").columns.tolist()
        self.cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.dt_cols  = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

    def generate(self, source: str = "raw", raw_row_count: int = None) -> list:
        insights = []
        df = self.df
        n_rows, n_cols = df.shape
        n_num  = len(self.num_cols)
        n_cat  = len(self.cat_cols)
        n_dt   = len(self.dt_cols)

        # 0 — Ringkasan dataset
        col_summary = []
        if n_num: col_summary.append(f"<b>{n_num}</b> numerik")
        if n_cat: col_summary.append(f"<b>{n_cat}</b> kategorik")
        if n_dt:  col_summary.append(f"<b>{n_dt}</b> tanggal")
        insights.append({
            "icon" : "database",
            "type" : "info",
            "title": "Ringkasan Dataset",
            "text" : (
                f"Dataset berisi <b>{n_rows:,}</b> baris dan <b>{n_cols}</b> kolom "
                f"({', '.join(col_summary) if col_summary else 'tidak ada kolom terdeteksi'})."
            ),
        })

        # 1 — Komparatif cleaning (hanya untuk source='cleaned')
        if source == "cleaned" and raw_row_count is not None:
            diff = raw_row_count - n_rows
            pct  = round(diff / raw_row_count * 100, 1) if raw_row_count else 0
            if diff > 0:
                insights.append({
                    "icon" : "filter",
                    "type" : "success",
                    "title": "Perubahan Setelah Cleaning",
                    "text" : (
                        f"Proses cleaning mengurangi data dari <b>{raw_row_count:,}</b> menjadi "
                        f"<b>{n_rows:,}</b> baris (berkurang <b>{diff:,} baris / {pct}%</b>)."
                    ),
                })
            else:
                insights.append({
                    "icon" : "filter",
                    "type" : "info",
                    "title": "Perubahan Setelah Cleaning",
                    "text" : (
                        f"Jumlah baris tidak berubah (<b>{n_rows:,}</b> baris). "
                        "Cleaning hanya melakukan transformasi nilai atau tipe kolom."
                    ),
                })

        # 2 — Distribusi kolom numerik (min, max, median) — max 3 kolom
        if self.num_cols:
            for col in self.num_cols[:3]:
                s = df[col].dropna()
                if len(s) == 0:
                    continue
                mn, mx, med = s.min(), s.max(), s.median()
                insights.append({
                    "icon" : "bar-chart",
                    "type" : "info",
                    "title": f"Distribusi: {col}",
                    "text" : (
                        f"Kolom <b>{col}</b> — nilai minimum <b>{mn:,.2f}</b>, "
                        f"maksimum <b>{mx:,.2f}</b>, median <b>{med:,.2f}</b>."
                    ),
                })

        # 3 — Kolom numerik dengan rata-rata tertinggi
        if self.num_cols:
            means   = df[self.num_cols].mean()
            top_col = means.idxmax()
            insights.append({
                "icon" : "trend-up",
                "type" : "info",
                "title": "Rata-rata Tertinggi",
                "text" : (
                    f"Kolom <b>{top_col}</b> memiliki rata-rata tertinggi "
                    f"(<b>{means[top_col]:,.2f}</b>) dibanding kolom numerik lainnya."
                ),
            })

        # 4 — Korelasi terkuat antar kolom numerik
        if len(self.num_cols) >= 2:
            try:
                corr_mat = df[self.num_cols].corr()
                corr_abs = corr_mat.abs().copy()   # .copy() agar tidak read-only
                np.fill_diagonal(corr_abs.values, 0)
                flat = corr_abs.unstack()
                pair = flat.idxmax()
                val  = corr_mat.loc[pair]
                if abs(val) > 0.2:
                    direction = "positif" if val > 0 else "negatif"
                    strength  = "sangat kuat" if abs(val) > 0.8 else "kuat" if abs(val) > 0.6 else "sedang"
                    insights.append({
                        "icon" : "link",
                        "type" : "success" if abs(val) > 0.6 else "info",
                        "title": "Korelasi Terkuat",
                        "text" : (
                            f"<b>{pair[0]}</b> dan <b>{pair[1]}</b> memiliki korelasi "
                            f"{direction} yang <b>{strength}</b> (r = {val:.2f}). "
                            "Hubungan ini dapat dimanfaatkan untuk pemodelan prediktif."
                        ),
                    })
            except Exception:
                pass

        # 5 — Kategori paling dominan (max 2 kolom)
        if self.cat_cols:
            for col in self.cat_cols[:2]:
                vc = df[col].value_counts()
                if len(vc) == 0:
                    continue
                top_val = vc.index[0]
                top_cnt = int(vc.iloc[0])
                top_pct = round(top_cnt / n_rows * 100, 1)
                n_uniq  = int(df[col].nunique())
                insights.append({
                    "icon" : "star",
                    "type" : "info",
                    "title": f"Kategori Dominan: {col}",
                    "text" : (
                        f"Nilai terbanyak pada <b>{col}</b> adalah <b>'{top_val}'</b> "
                        f"({top_cnt:,} data, <b>{top_pct}%</b> dari total). "
                        f"Total terdapat <b>{n_uniq}</b> kategori unik."
                    ),
                })

        # 6 — Skewness (kemiringan distribusi)
        if self.num_cols:
            try:
                skews = df[self.num_cols].skew()
                top_skew_col = skews.abs().idxmax()
                skew_val     = skews[top_skew_col]
                if abs(skew_val) > 0.5:
                    arah  = "kanan (positif)" if skew_val > 0 else "kiri (negatif)"
                    level = "sangat miring" if abs(skew_val) > 2 else "cukup miring"
                    insights.append({
                        "icon" : "alert-triangle",
                        "type" : "warning" if abs(skew_val) > 2 else "info",
                        "title": f"Distribusi Miring: {top_skew_col}",
                        "text" : (
                            f"Kolom <b>{top_skew_col}</b> memiliki distribusi yang {level} ke {arah} "
                            f"(skewness = {skew_val:.2f}). Pertimbangkan transformasi log jika diperlukan."
                        ),
                    })
            except Exception:
                pass

        # 7 — Variabilitas tertinggi (coefficient of variation)
        if self.num_cols:
            try:
                stds = df[self.num_cols].std()
                means2 = df[self.num_cols].mean()
                cvs = {}
                for c in self.num_cols:
                    if means2[c] and means2[c] != 0:
                        cvs[c] = abs(stds[c] / means2[c])
                if cvs:
                    top_cv_col = max(cvs, key=cvs.get)
                    insights.append({
                        "icon" : "bell",
                        "type" : "warning" if cvs[top_cv_col] > 1 else "info",
                        "title": f"Variabilitas Tertinggi: {top_cv_col}",
                        "text" : (
                            f"Kolom <b>{top_cv_col}</b> memiliki variasi data yang paling tinggi "
                            f"(CV = {cvs[top_cv_col]:.2f}, σ = {stds[top_cv_col]:,.2f}). "
                            "Data sangat tersebar dari nilai rata-ratanya."
                        ),
                    })
            except Exception:
                pass

        # 8 — Rentang waktu (time series)
        if self.dt_cols:
            dt_col = self.dt_cols[0]
            try:
                dt_series = pd.to_datetime(df[dt_col], errors="coerce").dropna()
                if len(dt_series) > 0:
                    dt_min = dt_series.min().strftime("%d %b %Y")
                    dt_max = dt_series.max().strftime("%d %b %Y")
                    insights.append({
                        "icon" : "clock",
                        "type" : "success",
                        "title": f"Rentang Waktu: {dt_col}",
                        "text" : (
                            f"Data mencakup periode dari <b>{dt_min}</b> hingga <b>{dt_max}</b>. "
                            "Analisis time series tersedia untuk kolom ini."
                        ),
                    })
            except Exception:
                pass

        # 9 — Outlier (IQR method)
        if self.num_cols:
            try:
                out_counts = {}
                for c in self.num_cols:
                    s = df[c].dropna()
                    q1, q3 = s.quantile(0.25), s.quantile(0.75)
                    iqr = q3 - q1
                    out_counts[c] = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
                top_out = max(out_counts, key=out_counts.get)
                if out_counts[top_out] > 0:
                    pct_out = round(out_counts[top_out] / n_rows * 100, 1)
                    insights.append({
                        "icon" : "alert-circle",
                        "type" : "warning" if pct_out > 5 else "info",
                        "title": f"Outlier Terdeteksi: {top_out}",
                        "text" : (
                            f"Kolom <b>{top_out}</b> memiliki <b>{out_counts[top_out]:,}</b> nilai outlier "
                            f"(<b>{pct_out}%</b> dari data) berdasarkan metode IQR."
                        ),
                    })
            except Exception:
                pass

        return insights
