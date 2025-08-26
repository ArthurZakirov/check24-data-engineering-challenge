import plotly.io as pio
pio.renderers.default = "browser"  # or "iframe", "png", etc.
import pandas as pd
import argparse
import os
import numpy as np
import matplotlib.pyplot as plt
from visual import plot_cause_vs_effect, plot_lines_by_segment, plot_combined_cause_vs_effect, plot_combined_plotly
import statsmodels.api as sm

# NOTE: elasticity doesnt make sense for negative prices, since the demand would be infinite if you get money for free (but the prices are only for 24 months, not lifetime)
# TODO: perform same analysis with cashback instead of price
# TODO: sales can be expressed as count * price (currently I use only count)
# TODO: make lines in visuals thicker based on weight (num sales & low SE)

def load_and_prepare_data(
    drop_columns: list[str], contract_duration: int
) -> pd.DataFrame:
    file = os.getenv("DATA_FILE_PATH", "aufgabe_2/Data Engineer - data_case.csv")
    df = pd.read_csv(file)

    df.drop(columns=drop_columns, inplace=True)
    df.loc[:, "dateTime"] = pd.to_datetime(df["dateTime"])
    df.sort_values(by="dateTime").reset_index(drop=True, inplace=True)

    # df["monthlyBilledPrice"] = (
    #     df["averageMonthlyPrice"] + df["cashback"] / contract_duration
    # )  # neglect delivery costs
    return df


def get_constant_cause_cols(
    df: pd.DataFrame, manipulated_cause: str, neglect_effect_of: list[str]
) -> list[str]:
    return [
        col
        for col in df.columns
        if col != manipulated_cause and not col in neglect_effect_of
    ]


def filter_unique_cause_combos(
    df: pd.DataFrame,
    manipulated_cause: str,
    constant_cause_cols: list[str],
    min_recorded_sales: int = 2,
    min_distinct_cause_values: int = 2,
    effect: str = "sales",
) -> pd.DataFrame:
    total_cause_cols = [*constant_cause_cols, manipulated_cause]

    df_unique_cause_combos = (
        df.value_counts(subset=total_cause_cols)
        .reset_index(name=effect)
        .sort_values(by=effect, ascending=False, ignore_index=True)
    )

    df_variation = df_unique_cause_combos.groupby(constant_cause_cols).filter(
        lambda x: (x[manipulated_cause].nunique() >= min_distinct_cause_values)
        and (x[effect].sum() >= min_recorded_sales)
    )
    return df_variation


def compute_elasticity(x: pd.Series, y: pd.Series) -> tuple[float, float]:
    lnP = np.log(x)
    lnQ = np.log(y)
    model = sm.WLS(lnQ, sm.add_constant(lnP)).fit()
    elasticity, standard_error = model.params[1], model.bse[1]
    return elasticity, standard_error


def compute_correlations(
    df: pd.DataFrame, x: str, y: str, corr_methods=["pearson", "spearman"]
) -> dict[str, float]:
    return {
        corr_method: df[x].corr(df[y], method=corr_method)
        for corr_method in corr_methods
    }


def generate_result_row(
    manipulated_cause: str,
    effect: str,
    constant_cause_cols: list[str],
    key: tuple,
    group: pd.DataFrame,
    elasticity: float,
    standard_error: float,
    corrs: dict[str, float],
) -> dict[str, float]:
    result_row = {
        **dict(zip(constant_cause_cols, key)),
        "spearman": corrs["spearman"],
        "pearson": corrs["pearson"],
        "elasticity": elasticity,
        "standard_error": standard_error,
        "unique_cause_values": group[manipulated_cause].nunique(),
        "sales": group[effect].sum(),
    }
    return result_row


def aggregate_metrics_over_segments(
    df: pd.DataFrame, segment_by: str
) -> pd.DataFrame:
    def _aggregate(df_segment):
        return pd.Series(
            {
                "pearson_wmean": np.average(
                    df_segment["pearson"], weights=df_segment["sales"]
                ),
                # "elasticity_wmean": np.average(
                #     df_segment["elasticity"], weights=df_segment["sales"]
                # ),
                # "elasticity_wmean_se": np.average(
                #     df_segment["elasticity"],
                #     weights=1 / df_segment["standard_error"] ** 2,
                # ),
            }
        )
    if segment_by is not None:
        return df.groupby(segment_by).apply(_aggregate).reset_index()
    else:
        return _aggregate(df).to_frame().T


def run_pipeline(
       drop_columns: list[str],
       manipulated_cause: str,
       effect: str,
       segment_by: str,
       contract_duration: int,
       min_recorded_sales: int,
       min_distinct_cause_values: int,
       neglect_effect_of: list[str],
       show_plots: bool
   ):

    df = load_and_prepare_data(
        drop_columns=drop_columns, contract_duration=contract_duration
    )

    constant_cause_cols = get_constant_cause_cols(
        df=df, manipulated_cause=manipulated_cause, neglect_effect_of=neglect_effect_of
    )
    df_filtered = filter_unique_cause_combos(
        df=df,
        manipulated_cause=manipulated_cause,
        constant_cause_cols=constant_cause_cols,
        min_recorded_sales=min_recorded_sales,
        min_distinct_cause_values=min_distinct_cause_values,
        effect=effect,
    )
    groups = df_filtered.groupby(constant_cause_cols)
    if show_plots:
        plot_args = dict(
            grouped_iterable=groups,
            cause=manipulated_cause,
            effect=effect,
            constant_cause_cols=constant_cause_cols,
        )
            
        plot_lines_by_segment(
            **plot_args,
            title=f"{effect.capitalize()} vs {manipulated_cause} (lines only)",
            html_out="lines_only.html",
            segment_by=segment_by,
        )

        plot_combined_plotly(
            **plot_args,
            title=f"{effect.capitalize()} vs {manipulated_cause} (scatter + lines)",
            html_out="scatter_and_lines.html",
        )

    results = []
    for key, group in groups:
        # elasticity, standard_error = compute_elasticity(
        #     group[manipulated_cause], group[effect]
        # )
        elasticity=0
        standard_error=0

        corrs = compute_correlations(group, manipulated_cause, effect)
        result_row = generate_result_row(
            manipulated_cause,
            effect,
            constant_cause_cols,
            key,
            group,
            elasticity,
            standard_error,
            corrs,
        )
        results.append(result_row)

    df_results = pd.DataFrame(results)
    df_aggregated = aggregate_metrics_over_segments(df_results, segment_by)
    return df_aggregated


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop_columns", nargs="+", default=[
        "hasInternetFlat",  # because True for all
        "positionInTheList",  # because NULL for all
        "providerReviewsAmount",  # because NULL for all
    ])
    parser.add_argument("--manipulated_cause", default="averageMonthlyPrice")
    parser.add_argument("--effect", default="sales")
    parser.add_argument("--segment_by", default="transferType") # transferType, hasMultimediaFlat
    parser.add_argument("--contract_duration", type=int, default=24)
    parser.add_argument("--min_recorded_sales", type=int, default=10)
    parser.add_argument("--min_distinct_cause_values", type=int, default=3)
    parser.add_argument("--neglect_effect_of", nargs="+", default=[
        "providerName",  # neglect, since potential associations (e.g. trust) with provider is already reflected in ratings, price etc.
        "dateTime",  # neglect, (because we integrate over it) since we are not interested in condition of purchase behaviour depending on time of day, but on a more macro (datetime agnostic) level, which the 24h snapshot of data satisfies
        "deviceoutput",  # neglect, (because we integrate over it) since we (as pricing strategists) we can't influence the device people use, furthermore the proportion of device types is likely to be consistent over time
    ])
    parser.add_argument("--show_plots", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    df = run_pipeline(
        drop_columns=args.drop_columns,
        manipulated_cause=args.manipulated_cause,
        effect=args.effect,
        segment_by=args.segment_by,
        contract_duration=args.contract_duration,
        min_recorded_sales=args.min_recorded_sales,
        min_distinct_cause_values=args.min_distinct_cause_values,
        neglect_effect_of=args.neglect_effect_of,
        show_plots=args.show_plots
    )
    print(df)