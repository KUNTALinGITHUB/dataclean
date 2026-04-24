import pandas as pd

NULL_PATTERNS = {
    "n/a", "na", "null", "none", "nil",
    "-", "--", "?", "??", ".",
    "missing", "unknown", "undefined",
    "nan", "nat", "not available",
    "not applicable", ""
}


def fix_nulls(df: pd.DataFrame, report=None) -> pd.DataFrame:
    """
    Detect and unify all hidden null values into real pd.NA.
    Catches disguised nulls like 'N/A', 'null', '?', 'unknown', etc.
    Also catches sentinel numeric values like -999, 9999999.
    """
    for col in df.columns:
        # detect string-based hidden nulls
        mask = df[col].astype(str).str.strip().str.lower().isin(NULL_PATTERNS)
        count = int(mask.sum())

        if count > 0:
            df.loc[mask, col] = pd.NA
            if report:
                report.log("nulls", col, f"{count} hidden null(s) unified to pd.NA")

        # detect numeric sentinel values
        if pd.api.types.is_numeric_dtype(df[col]):
            sentinels = [-1, -99, -999, -9999, 9999, 99999, 9999999]
            for val in sentinels:
                sent_mask = df[col] == val
                sent_count = int(sent_mask.sum())
                if sent_count > 0:
                    df.loc[sent_mask, col] = pd.NA
                    if report:
                        report.log(
                            "nulls", col,
                            f"{sent_count} sentinel value(s) ({val}) converted to pd.NA"
                        )

    return df