"""
backend/visualization.py
Automated Visualization Analytics — all chart types using Plotly.
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import scipy.stats as sp_stats


# ── Colorful palette ─────────────────────────────────────────────────────────
# A vivid, varied qualitative palette used across every chart so each column /
# category / series gets its own distinct, eye-catching color instead of one
# flat teal tone everywhere.
PALETTE = [
    "#25C5E9",  # sky blue (brand)
    "#FF6B9D",  # pink
    "#FFD166",  # amber
    "#06D6A0",  # emerald
    "#A78BFA",  # violet
    "#FB923C",  # orange
    "#4ADE80",  # green
    "#60A5FA",  # blue
    "#F472B6",  # rose
    "#FBBF24",  # gold
    "#34D399",  # teal-green
    "#C084FC",  # purple
    "#F87171",  # coral red
    "#38BDF8",  # light blue
]

COLORS = {
    "bg"        : "rgba(0,0,0,0)",
    "font"      : "#F2FFF6",
    "grid"      : "rgba(148,163,184,0.15)",
    "ref_line"  : "#FFFFFF",   # neutral color for trend / reference lines
    "cumulative": "#FFD166",   # warm accent for pareto cumulative line
    "seq"       : PALETTE,
}

LAYOUT_BASE = dict(
    plot_bgcolor =COLORS["bg"],
    paper_bgcolor=COLORS["bg"],
    font         =dict(color=COLORS["font"], size=11),
    xaxis        =dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    yaxis        =dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    margin       =dict(t=40, b=40, l=50, r=20),
    height       =300,
    colorway     =PALETTE,
)


def fig_to_dict(fig) -> dict:
    return json.loads(fig.to_json())


def pick_color(i: int) -> str:
    """Cycle through the palette for the i-th column/series/category."""
    return PALETTE[i % len(PALETTE)]


def hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """Convert a '#RRGGBB' hex color into an 'rgba(r,g,b,a)' string."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


class Visualization:
    def __init__(self, df: pd.DataFrame):
        self.df      = df
        self.num_cols = df.select_dtypes(include="number").columns.tolist()
        self.cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # ── Entry point ───────────────────────────────────────────────────────────
    def generate_all(self) -> dict:
        return {
            "numerical"  : self._numerical_viz(),
            "categorical": self._categorical_viz(),
            "bivariate"  : self._bivariate_viz(),
            "cat_vs_num" : self._cat_vs_num_viz(),
        }

    # ── A) Numerical ──────────────────────────────────────────────────────────
    def _numerical_viz(self) -> list:
        out = []
        for i, col in enumerate(self.num_cols[:8]):   # limit to avoid browser overload
            s = self.df[col].dropna()
            if len(s) < 3:
                continue
            c = pick_color(i)
            out += [
                self._histogram(s, col, c),
                self._boxplot(s, col, c),
                self._density(s, col, c),
                self._qqplot(s, col, c),
                self._violin(s, col, c),
            ]
        return out

    def _histogram(self, s, col, color):
        fig = go.Figure(go.Histogram(
            x=s, name=col,
            marker_color=color,
            marker_line_color=COLORS["ref_line"],
            marker_line_width=0.5,
            opacity=0.85,
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Histogram · {col}")
        return {"type": "Histogram", "column": col, "fig": fig_to_dict(fig)}

    def _boxplot(self, s, col, color):
        fig = go.Figure(go.Box(
            y=s, name=col,
            marker_color=color,
            line_color=color,
            fillcolor=hex_to_rgba(color, 0.25),
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Boxplot · {col}")
        return {"type": "Boxplot", "column": col, "fig": fig_to_dict(fig)}

    def _density(self, s, col, color):
        kde   = sp_stats.gaussian_kde(s)
        x_rng = np.linspace(s.min(), s.max(), 200)
        fig   = go.Figure(go.Scatter(
            x=x_rng, y=kde(x_rng),
            mode="lines",
            fill="tozeroy",
            line=dict(color=color, width=2),
            fillcolor=hex_to_rgba(color, 0.2),
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Density Plot · {col}")
        return {"type": "Density Plot", "column": col, "fig": fig_to_dict(fig)}

    def _qqplot(self, s, col, color):
        qq    = sp_stats.probplot(s, dist="norm")
        x_pts = qq[0][0]
        y_pts = qq[0][1]
        slope, intercept = qq[1][0], qq[1][1]
        line_y = [slope * xi + intercept for xi in x_pts]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_pts, y=y_pts, mode="markers",
                                  marker=dict(color=color, size=4), name="Data"))
        fig.add_trace(go.Scatter(x=x_pts, y=line_y, mode="lines",
                                  line=dict(color=COLORS["ref_line"], dash="dash"), name="Normal Line"))
        fig.update_layout(**LAYOUT_BASE, title_text=f"QQ Plot · {col}")
        return {"type": "QQ Plot", "column": col, "fig": fig_to_dict(fig)}

    def _violin(self, s, col, color):
        fig = go.Figure(go.Violin(
            y=s, name=col,
            line_color=color,
            fillcolor=hex_to_rgba(color, 0.25),
            meanline_visible=True,
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Violin Plot · {col}")
        return {"type": "Violin Plot", "column": col, "fig": fig_to_dict(fig)}

    # ── B) Categorical ────────────────────────────────────────────────────────
    def _categorical_viz(self) -> list:
        out = []
        for col in self.cat_cols[:6]:
            vc = self.df[col].value_counts().head(15)
            if len(vc) == 0:
                continue
            colors = [pick_color(i) for i in range(len(vc))]
            out += [
                self._bar_chart(vc, col, colors),
                self._pie_chart(vc, col, colors),
                self._count_plot(vc, col, colors),
                self._pareto_chart(vc, col, colors),
            ]
        return out

    def _bar_chart(self, vc, col, colors):
        fig = go.Figure(go.Bar(
            x=vc.index.astype(str), y=vc.values,
            marker_color=colors,
            marker_line_color=COLORS["ref_line"],
            marker_line_width=0.5,
            text=vc.values, textposition="outside",
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Bar Chart · {col}")
        return {"type": "Bar Chart", "column": col, "fig": fig_to_dict(fig)}

    def _pie_chart(self, vc, col, colors):
        fig = go.Figure(go.Pie(
            labels=vc.index.astype(str), values=vc.values,
            marker=dict(colors=colors, line=dict(color=COLORS["bg"], width=1)),
            hole=0.3,
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Pie Chart · {col}")
        return {"type": "Pie Chart", "column": col, "fig": fig_to_dict(fig)}

    def _count_plot(self, vc, col, colors):
        fig = go.Figure(go.Bar(
            y=vc.index.astype(str), x=vc.values,
            orientation="h",
            marker_color=colors,
            text=vc.values, textposition="outside",
        ))
        layout = {**LAYOUT_BASE, "title_text": f"Count Plot · {col}"}
        layout["yaxis"] = dict(autorange="reversed",
                               gridcolor=COLORS["grid"],
                               zerolinecolor=COLORS["grid"])
        fig.update_layout(**layout)
        return {"type": "Count Plot", "column": col, "fig": fig_to_dict(fig)}

    def _pareto_chart(self, vc, col, colors):
        cumulative = vc.cumsum() / vc.sum() * 100
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=vc.index.astype(str), y=vc.values,
                              marker_color=colors, name="Count"),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=vc.index.astype(str), y=cumulative.values,
                                  mode="lines+markers",
                                  line=dict(color=COLORS["cumulative"], width=2),
                                  marker=dict(color=COLORS["cumulative"], size=6),
                                  name="Cumulative %"),
                      secondary_y=True)
        fig.update_layout(**LAYOUT_BASE, title_text=f"Pareto Chart · {col}")
        fig.update_yaxes(range=[0, 110], secondary_y=True,
                         ticksuffix="%", gridcolor=COLORS["grid"])
        return {"type": "Pareto Chart", "column": col, "fig": fig_to_dict(fig)}

    # ── C) Bivariate & Multivariate ───────────────────────────────────────────
    def _bivariate_viz(self) -> list:
        out  = []
        nums = self.num_cols[:6]

        if len(nums) >= 2:
            out.append(self._scatter(nums[0], nums[1]))
            out.append(self._regression_plot(nums[0], nums[1]))

        if len(nums) >= 2:
            out.append(self._corr_heatmap(nums))

        if len(nums) >= 3:
            out.append(self._bubble_chart(nums[0], nums[1], nums[2]))

        return out

    def _scatter(self, cx, cy):
        fig = go.Figure(go.Scatter(
            x=self.df[cx], y=self.df[cy],
            mode="markers",
            marker=dict(color=pick_color(0), size=5, opacity=0.75),
        ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Scatter · {cx} vs {cy}",
                          xaxis_title=cx, yaxis_title=cy)
        return {"type": "Scatter Plot", "column": f"{cx} vs {cy}", "fig": fig_to_dict(fig)}

    def _regression_plot(self, cx, cy):
        df2  = self.df[[cx, cy]].dropna()
        if len(df2) < 3:
            return self._scatter(cx, cy)
        m, b = np.polyfit(df2[cx], df2[cy], 1)
        x_ln = np.linspace(df2[cx].min(), df2[cx].max(), 100)
        fig  = go.Figure()
        fig.add_trace(go.Scatter(x=df2[cx], y=df2[cy], mode="markers",
                                  marker=dict(color=pick_color(1), size=5, opacity=0.65),
                                  name="Data"))
        fig.add_trace(go.Scatter(x=x_ln, y=m * x_ln + b, mode="lines",
                                  line=dict(color=COLORS["ref_line"], width=2, dash="dash"),
                                  name="Regression"))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Regression · {cx} vs {cy}")
        return {"type": "Regression Plot", "column": f"{cx} vs {cy}", "fig": fig_to_dict(fig)}

    def _corr_heatmap(self, cols):
        corr  = self.df[cols].corr()
        fig   = go.Figure(go.Heatmap(
            z=corr.values, x=cols, y=cols,
            colorscale="Picnic",
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate="%{text}",
            showscale=True,
            zmin=-1, zmax=1,
        ))
        layout = {**LAYOUT_BASE, "title_text": "Correlation Heatmap", "height": 350}
        fig.update_layout(**layout)
        return {"type": "Correlation Heatmap", "column": "All Numerics", "fig": fig_to_dict(fig)}

    def _bubble_chart(self, cx, cy, cz):
        df3   = self.df[[cx, cy, cz]].dropna()
        if len(df3) == 0:
            return self._scatter(cx, cy)
        smax  = df3[cz].max()
        sizes = (df3[cz] / smax * 40 + 5).clip(5, 50) if smax > 0 else [10] * len(df3)
        fig   = go.Figure(go.Scatter(
            x=df3[cx], y=df3[cy], mode="markers",
            marker=dict(size=sizes, color=df3[cz], colorscale="Turbo",
                        opacity=0.75, showscale=True,
                        colorbar=dict(title=cz, thickness=12),
                        line=dict(color=COLORS["ref_line"], width=0.5)),
        ))
        fig.update_layout(**LAYOUT_BASE,
                          title_text=f"Bubble · {cx} vs {cy} (size={cz})")
        return {"type": "Bubble Chart", "column": f"{cx}/{cy}/{cz}", "fig": fig_to_dict(fig)}

    # ── D) Categorical vs Numerical ───────────────────────────────────────────
    def _cat_vs_num_viz(self) -> list:
        out = []
        if not self.cat_cols or not self.num_cols:
            return out
        cat = self.cat_cols[0]
        num = self.num_cols[0]
        n2  = self.num_cols[1] if len(self.num_cols) > 1 else self.num_cols[0]

        out.append(self._box_by_cat(cat, num))
        out.append(self._violin_by_cat(cat, num))
        out.append(self._grouped_bar(cat, num, n2))
        out.append(self._strip_plot(cat, num))
        return out

    def _box_by_cat(self, cat, num):
        df2   = self.df[[cat, num]].dropna()
        cats  = df2[cat].value_counts().head(10).index.tolist()
        df2   = df2[df2[cat].isin(cats)]
        fig   = go.Figure()
        for i, c in enumerate(cats):
            color = pick_color(i)
            grp = df2[df2[cat] == c][num]
            fig.add_trace(go.Box(y=grp, name=str(c),
                                  fillcolor=hex_to_rgba(color, 0.3),
                                  line_color=color,
                                  marker_color=color))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Boxplot by {cat}")
        return {"type": "Boxplot by Category", "column": f"{cat} vs {num}", "fig": fig_to_dict(fig)}

    def _violin_by_cat(self, cat, num):
        df2   = self.df[[cat, num]].dropna()
        cats  = df2[cat].value_counts().head(8).index.tolist()
        df2   = df2[df2[cat].isin(cats)]
        fig   = go.Figure()
        for i, c in enumerate(cats):
            color = pick_color(i)
            grp = df2[df2[cat] == c][num]
            fig.add_trace(go.Violin(y=grp, name=str(c),
                                     line_color=color,
                                     fillcolor=hex_to_rgba(color, 0.25),
                                     meanline_visible=True))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Violin by {cat}")
        return {"type": "Violin by Category", "column": f"{cat} vs {num}", "fig": fig_to_dict(fig)}

    def _grouped_bar(self, cat, num, num2):
        df2   = self.df[[cat, num, num2]].dropna()
        cats  = df2[cat].value_counts().head(10).index.tolist()
        df2   = df2[df2[cat].isin(cats)]
        grp   = df2.groupby(cat)[[num, num2]].mean().reindex(cats)
        fig   = go.Figure()
        fig.add_trace(go.Bar(name=num, x=grp.index.astype(str), y=grp[num],
                              marker_color=pick_color(0)))
        fig.add_trace(go.Bar(name=num2, x=grp.index.astype(str), y=grp[num2],
                              marker_color=pick_color(1)))
        fig.update_layout(**LAYOUT_BASE, barmode="group",
                          title_text=f"Grouped Bar · {cat}")
        return {"type": "Grouped Bar Chart", "column": cat, "fig": fig_to_dict(fig)}

    def _strip_plot(self, cat, num):
        df2  = self.df[[cat, num]].dropna()
        cats = df2[cat].value_counts().head(10).index.tolist()
        df2  = df2[df2[cat].isin(cats)]
        fig  = go.Figure()
        for i, c in enumerate(cats):
            color = pick_color(i)
            grp = df2[df2[cat] == c][num]
            fig.add_trace(go.Scatter(
                x=[str(c)] * len(grp), y=grp,
                mode="markers",
                marker=dict(size=4, opacity=0.6, color=color),
                name=str(c),
            ))
        fig.update_layout(**LAYOUT_BASE, title_text=f"Strip Plot · {cat} vs {num}")
        return {"type": "Strip Plot", "column": f"{cat} vs {num}", "fig": fig_to_dict(fig)}
