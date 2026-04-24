import pandas as pd
from dateutil import parser as dateutil_parser


COMMON_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
    "%d-%m-%Y", "%m-%d-%Y", "%Y/%m/%d",
    "%d %b %Y", "%d %B %Y", "%b %d %Y",
    "%B %d %Y", "%Y%m%d", "%Y.%m.%d",
]

DATE_COLUMN_HINTS = {
    "date", "time", "day", "month", "year",
    "dob", "joined", "created", "updated", "birth"
}

# columns that should NEVER be treated as dates
NON_DATE_HINTS = {"id", "age", "salary", "price", "count", "num", "amount"}


def _try_parse_date(value):
    if pd.isna(value):
        return pd.NaT

    val_str = str(value).strip()

    # reject pure short integers — age, id, count etc.
    if val_str.isdigit() and len(val_str) <= 4:
        return None

    # handle unix timestamps (exactly 10 digits)
    if val_str.isdigit() and len(val_str) == 10:
        try:
            return pd.to_datetime(int(val_str), unit="s")
        except Exception:
            pass

    # try common formats first
    for fmt in COMMON_DATE_FORMATS:
        try:
            return pd.to_datetime(val_str, format=fmt)
        except Exception:
            continue

    # fall back to dateutil
    try:
        return dateutil_parser.parse(val_str, dayfirst=False)
    except Exception:
        return None


def _is_date_column(series: pd.Series) -> bool:
    col_name = str(series.name).lower()

    # hard reject non-date columns by name
    if any(hint in col_name for hint in NON_DATE_HINTS):
        return False

    # accept by name hint
    if any(hint in col_name for hint in DATE_COLUMN_HINTS):
        # still verify at least one value parses
        sample = series.dropna().astype(str).head(5)
        for val in sample:
            if val.isdigit() and len(val) <= 4:
                return False
        return True

    # sample values and check parse rate
    sample = series.dropna().astype(str).head(20)
    if len(sample) == 0:
        return False

    # reject if column looks purely numeric (short integers)
    numeric_short = sum(
        1 for v in sample if v.isdigit() and len(v) <= 4
    )
    if numeric_short / len(sample) >= 0.5:
        return False

    success = 0
    for val in sample:
        result = _try_parse_date(val)
        if result is not None and not pd.isna(result):
            success += 1

    return (success / len(sample)) >= 0.7


def fix_dates(
    df: pd.DataFrame,
    report=None,
    target_format: str = "%Y-%m-%d",
    as_string: bool = True
) -> pd.DataFrame:
    """
    Auto-detect date columns and normalize them to a single format.
    """
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            continue

        if not _is_date_column(df[col]):
            continue

        parsed = df[col].apply(_try_parse_date)
        success_count = int(parsed.notna().sum())
        fail_count = int(df[col].notna().sum() - success_count)

        if success_count > 0:
            datetime_col = pd.to_datetime(parsed, errors="coerce")

            if as_string:
                df[col] = datetime_col.apply(
                    lambda x: x.strftime(target_format) if not pd.isna(x) else pd.NA
                )
            else:
                df[col] = datetime_col

            if report:
                report.log(
                    "dates", col,
                    f"normalized {success_count} date(s) to '{target_format}'"
                    + (f" — {fail_count} could not be parsed" if fail_count > 0 else "")
                )

    return df