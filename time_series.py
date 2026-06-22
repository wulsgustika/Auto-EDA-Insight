"""
backend/time_series.py
Auto-detect datetime columns and perform time series analysis.
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


COLORS = {
    "primary"  : "#25C5E9",
    "secondary": "#238689",
    "accent"   : "#CAFFDE",
    "bg"       : "rgba(0,0,0,0)",
    "font"     : "#F2FFF6",
    "grid"     : "rgba(37,197,233,0.1)",
}

LAYOUT_BASE = dict(
    plot_bgcolor =COLORS["bg"],
    paper_bgcolor=COLORS["bg"],
    font         =dict(color=COLORS["font"], size=11),
    xaxis        =dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    yaxis        =dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    margin       =dict(t=40, b=40, l=50, r=20),
    height       =300,
)


def fig_to_dict(fig) -> dict:
    return json.loads(fig.to_json())


class TimeSeries:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.num_cols = df.select_dtypes(include="number").columns.tolist()

        self.dt_cols = df.select_dtypes(
            include=["datetime", "datetimetz"]
        ).columns.tolist()

        # Auto-detect kolom tanggal khusus untuk Time Series.
        #
        # PENTING — dua perbaikan bug di sini:
        #   1) `break` sebelumnya berada DI LUAR blok `if`, sehingga loop selalu
        #      berhenti setelah kolom pertama, tidak peduli apakah kolom itu
        #      benar-benar tanggal. Akibatnya kolom tanggal asli (mis. "Date")
        #      tidak pernah diperiksa kalau bukan kolom pertama.
        #   2) Sebelumnya SEMUA kolom (termasuk kolom numerik seperti ID/index,
        #      mis. "Unnamed: 0" atau "Employee_ID") ikut dicoba dikonversi ke
        #      datetime. pd.to_datetime() pada deretan angka (mis. 0,1,2,3,...)
        #      tidak melempar error — ia menafsirkannya sebagai nanodetik sejak
        #      epoch — sehingga kolom ID/index sering salah terdeteksi sebagai
        #      kolom tanggal. Sekarang hanya kolom non-numerik (object/string)
        #      yang dicoba, dan kolom yang terpilih dikeluarkan dari num_cols
        #      supaya tidak terjadi duplikasi kolom saat df[[dt_col, num_col]].
        if not self.dt_cols:
            for col in df.columns:
                if col in self.num_cols:
                    continue
                try:
                    sample = pd.to_datetime(df[col], errors="coerce")
                except Exception:
                    continue
                if sample.notna().sum() >= len(df) * 0.7:
                    self.df = df.copy()
                    self.df[col] = sample
                    self.dt_cols = [col]
                    break

        # Pastikan kolom tanggal tidak pernah ikut dianggap kolom numerik,
        # baik hasil auto-detect di atas maupun kolom yang memang sudah
        # bertipe datetime sejak awal (mis. dari DataLoader).
        if self.dt_cols:
            self.num_cols = [c for c in self.num_cols if c not in self.dt_cols]

    def analyze(self) -> dict:
        if not self.dt_cols or not self.num_cols:
            return {"has_timeseries": False, "charts": []}

        dt_col = self.dt_cols[0]
        charts = []
        for num_col in self.num_cols[:4]:
            df2 = self.df[[dt_col, num_col]].dropna().sort_values(dt_col)
            if len(df2) < 3:
                continue
            charts.append(self._ts_line(df2, dt_col, num_col))
            charts.append(self._moving_avg(df2, dt_col, num_col))
            charts.append(self._rolling_mean(df2, dt_col, num_col))
            charts.append(self._trend_line(df2, dt_col, num_col))

        return {
            "has_timeseries": True,
            "date_column"   : dt_col,
            "numeric_columns": self.num_cols,
            "charts"        : charts,
        }

    # ── Charts ────────────────────────────────────────────────────────────────
    def _ts_line(self, df, dt_col, num_col):
        fig = go.Figure(go.Scatter(
            x=df[dt_col], y=df[num_col],
            mode="lines",
            line=dict(color=COLORS["primary"], width=1.5),
            name=num_col,
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Time Series · {num_col}")
        return {"type": "Time Series Line Chart", "column": num_col, "fig": fig_to_dict(fig)}

    def _moving_avg(self, df, dt_col, num_col, window=7):
        ma = df[num_col].rolling(window=window, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[dt_col], y=df[num_col],
                                  mode="lines", opacity=0.4,
                                  line=dict(color=COLORS["primary"], width=1),
                                  name="Original"))
        fig.add_trace(go.Scatter(x=df[dt_col], y=ma,
                                  mode="lines",
                                  line=dict(color=COLORS["accent"], width=2),
                                  name=f"MA({window})"))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Moving Avg ({window}-period) · {num_col}")
        return {"type": "Moving Average", "column": num_col, "fig": fig_to_dict(fig)}

    def _rolling_mean(self, df, dt_col, num_col, window=30):
        rm = df[num_col].rolling(window=window, min_periods=1).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[dt_col], y=df[num_col],
                                  mode="lines", opacity=0.35,
                                  line=dict(color=COLORS["secondary"], width=1),
                                  name="Original"))
        fig.add_trace(go.Scatter(x=df[dt_col], y=rm,
                                  mode="lines",
                                  line=dict(color=COLORS["primary"], width=2.5),
                                  name=f"Rolling ({window}d)"))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Rolling Mean ({window}-period) · {num_col}")
        return {"type": "Rolling Mean", "column": num_col, "fig": fig_to_dict(fig)}

    def _trend_line(self, df, dt_col, num_col):
        y   = df[num_col].values
        x_n = np.arange(len(y))
        try:
            m, b = np.polyfit(x_n, y, 1)
        except Exception:
            return self._ts_line(df, dt_col, num_col)
        trend = m * x_n + b
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df[dt_col], y=y,
                                  mode="lines", opacity=0.5,
                                  line=dict(color=COLORS["primary"], width=1.2),
                                  name="Data"))
        fig.add_trace(go.Scatter(x=df[dt_col], y=trend,
                                  mode="lines",
                                  line=dict(color=COLORS["accent"], width=2, dash="dash"),
                                  name="Trend"))
        dir_label = "↑ Upward" if m > 0 else "↓ Downward"
        fig.update_layout(**LAYOUT_BASE,
                          title_text=f"Trend Line ({dir_label}) · {num_col}")
        return {"type": "Trend Line", "column": num_col, "fig": fig_to_dict(fig)}
