import pandas as pd

# columns that should never be checked for outliers
SKIP_OUTLIER_HINTS = {"id", "index", "code", "zip", "phone", "year"}


def flag_outliers(
    df: pd.DataFrame,
    report=None,
    method: str = "iqr",
    threshold: float = 1.5
) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    for col in numeric_cols:
        # skip id-like and flag columns
        col_lower = col.lower()
        if any(hint in col_lower for hint in SKIP_OUTLIER_HINTS):
            continue
        if col_lower.endswith("_flag") or col_lower.endswith("_id"):
            continue

        series = df[col].dropna()

        # skip if too few values or too many nulls
        if len(series) < 4:
            continue
        if series.nunique() < 3:
            continue

        outlier_mask = pd.Series(False, index=df.index)

        if method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                continue

            lower = q1 - (threshold * iqr)
            upper = q3 + (threshold * iqr)

            outlier_mask = (df[col] < lower) | (df[col] > upper)
            outlier_mask = outlier_mask.fillna(False)

            if report and outlier_mask.sum() > 0:
                report.log(
                    "outliers", col,
                    f"{int(outlier_mask.sum())} outlier(s) flagged "
                    f"[IQR — valid range: {lower:.2f} to {upper:.2f}]"
                )

        elif method == "zscore":
            mean = series.mean()
            std = series.std()

            if std == 0:
                continue

            zscores = (df[col] - mean).abs() / std
            outlier_mask = zscores > threshold
            outlier_mask = outlier_mask.fillna(False)

            if report and outlier_mask.sum() > 0:
                report.log(
                    "outliers", col,
                    f"{int(outlier_mask.sum())} outlier(s) flagged "
                    f"[Z-score — threshold: ±{threshold}]"
                )

        flag_col = f"{col}_outlier_flag"
        df[flag_col] = outlier_mask.astype(bool)

    return df