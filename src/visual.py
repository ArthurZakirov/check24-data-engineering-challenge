import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.colors import qualitative as qual
from itertools import cycle

pio.renderers.default = "browser"


def _fmt_value(v):
    if pd.isna(v):
        return "NA"
    if isinstance(v, (np.bool_, bool)):
        return "True" if bool(v) else "False"
    if isinstance(v, (np.floating, float)):
        v = float(v)
        return f"{int(v)}" if v.is_integer() else f"{v:.3g}"
    return str(v).strip()

def key_to_label(key: tuple, cols: list[str]) -> str:
    return ", ".join(f"{c}={_fmt_value(v)}" for c, v in zip(cols, key))


def plot_combined_plotly(
    grouped_iterable, 
    cause: str,
    effect: str,
    constant_cause_cols: list[str],
    title: str | None = None,
    max_groups: int | None = None,   
    html_out: str | None = None
):
    frames = []
    for i, (key, group) in enumerate(grouped_iterable):
        if max_groups is not None and i >= max_groups:
            break
        label = key_to_label(key, constant_cause_cols)
        g = group[[cause, effect]].dropna().copy()
        if g.empty: 
            continue
        g["Group"] = label
        frames.append(g)
    if not frames:
        return None

    plot_df = pd.concat(frames, ignore_index=True)

    fig = px.scatter(
        plot_df,
        x=cause,
        y=effect,
        color="Group",
        hover_data=[cause, effect, "Group"],
        trendline="ols",            
        title=title or f"{effect.capitalize()} vs {cause}",
    )
    fig.update_layout(legend_title_text="Group")
    fig.show()

    if html_out:
        pio.write_html(fig, file=html_out)

    return fig



def plot_combined_cause_vs_effect(
    grouped_iterable,  
    cause: str,
    effect: str = "sales",
    title: str | None = None,
    max_legend_items: int | None = 20,  
):
    fig, ax = plt.subplots(figsize=(7.5, 5))
    cmap = get_cmap("tab20")
    color_iter = cycle([cmap(i) for i in range(cmap.N)])

    handles = []
    labels = []

    for idx, (key, group) in enumerate(grouped_iterable):
        color = next(color_iter)
        g = group[[cause, effect]].dropna()
        if g.empty:
            continue

        h = ax.scatter(g[cause], g[effect], s=22, alpha=0.8, label=str(key), color=color)
        if idx < (max_legend_items or 0):
            handles.append(h)
            labels.append(str(key))

        if len(g) >= 2:
            x = g[cause].to_numpy()
            y = g[effect].to_numpy()
            slope, intercept = np.polyfit(x, y, deg=1)
            xline = np.array([x.min(), x.max()])
            yline = slope * xline + intercept
            ax.plot(xline, yline, linewidth=1.5, alpha=0.8, color=color)

    ax.set_xlabel(cause)
    ax.set_ylabel(effect.capitalize())
    ax.set_title(title or f"{effect.capitalize()} vs {cause} (combined)")

    if handles:
        ax.legend(handles, labels, title="Group", loc="best", frameon=True)

    ax.grid(True, linestyle="--", alpha=0.25)
    return fig, ax


def plot_lines_by_segment(
    grouped_iterable,           
    cause: str,
    effect: str,
    constant_cause_cols: list[str],
    segment_by: str | None,
    title: str | None = None,
    html_out: str | None = None
):
    fig = go.Figure()

    palette = qual.Plotly + qual.D3 + qual.Set3 + qual.Dark24 + qual.Light24
    seg_to_color = {}
    seen_segments = set()
    color_idx = 0

    for key, group in grouped_iterable:
        g = group[[cause, effect]].dropna()
        if len(g) < 2:
            continue

        key_dict = dict(zip(constant_cause_cols, key))
        seg_val = key_dict[segment_by] if segment_by in key_dict else "All"
        seg_label = f"{segment_by}={seg_val}" if segment_by else "All"

        if seg_label not in seg_to_color:
            seg_to_color[seg_label] = palette[color_idx % len(palette)]
            color_idx += 1
        color = seg_to_color[seg_label]

        x = g[cause].to_numpy()
        y = g[effect].to_numpy()
        slope, intercept = np.polyfit(x, y, deg=1)
        xline = np.array([x.min(), x.max()])
        yline = slope * xline + intercept

        fig.add_trace(
            go.Scatter(
                x=xline,
                y=yline,
                mode="lines",
                line=dict(width=2, color=color),
                name=seg_label,
                legendgroup=seg_label,
                showlegend=seg_label not in seen_segments,
                hovertemplate=(
                    f"<b>{seg_label}</b><br>"
                    f"slope={slope:.3g}, intercept={intercept:.3g}<extra></extra>"
                ),
            )
        )
        seen_segments.add(seg_label)

    fig.update_layout(
        title=title or f"{effect.capitalize()} vs {cause} (trend lines only)",
        xaxis_title=cause,
        yaxis_title=effect.capitalize(),
        legend_title="Segment",
        margin=dict(l=60, r=20, t=60, b=50),
    )

    if html_out:
        fig.write_html(html_out, auto_open=True)
    else:
        fig.show()

    return fig