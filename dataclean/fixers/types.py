import pandas as pd


def fix_types(df: pd.DataFrame, report=None) -> pd.DataFrame:
    """
    Detect and fix mixed types in columns.
    - Finds the dominant type in each column
    - Attempts safe coercion to that type
    - Flags values that couldn't be converted
    """
    for col in df.columns:
        # skip columns that are already fully null
        if df[col].dropna().empty:
            continue

        total_non_null = df[col].notna().sum()

        if total_non_null == 0:
            continue

        numeric_converted = pd.to_numeric(df[col], errors="coerce")
        numeric_count = numeric_converted.notna().sum()
        numeric_ratio = numeric_count / total_non_null

        # if 80%+ of values are numeric, coerce the whole column
        if numeric_ratio >= 0.8:
            failed = int(total_non_null - numeric_count)
            df[col] = numeric_converted

            if report and failed > 0:
                report.log(
                    "types", col,
                    f"coerced to numeric — {failed} value(s) could not convert and set to NaN"
                )
            elif report and numeric_ratio < 1.0:
                report.log(
                    "types", col,
                    f"coerced to numeric successfully"
                )

        else:
            # treat as string column — handle both object and Pandas 3 StringDtype
            is_string_col = df[col].dtype == object or "str" in str(df[col].dtype)
            if is_string_col:
                # strip whitespace but preserve pd.NA
                df[col] = df[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
                if report:
                    report.log(
                        "types", col,
                        f"kept as string — stripped whitespace from all values"
                    )

    return df