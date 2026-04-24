import pandas as pd
from pathlib import Path

from .report import CleanReport
from .fixers.columns import fix_columns
from .fixers.nulls import fix_nulls
from .fixers.types import fix_types
from .fixers.dates import fix_dates
from .fixers.duplicates import fix_duplicates
from .fixers.categories import fix_categories
from .fixers.outliers import flag_outliers
from .fixers.encoding import fix_encoding, fix_string_encoding


SUPPORTED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


def _load(source, encoding: str = "utf-8") -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        return source.copy()

    path = Path(source)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {source}")

    ext = path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{ext}'. "
            f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    if ext == ".csv":
        return pd.read_csv(source, encoding=encoding, low_memory=False)
    elif ext == ".json":
        return pd.read_json(source, encoding=encoding)
    elif ext in {".xlsx", ".xls"}:
        return pd.read_excel(source)


def clean(
    source,
    fix: str = "all",
    output: str = None,
    fuzzy_duplicates: bool = False,
    outlier_method: str = "iqr",
    category_threshold: int = 85,
    duplicate_threshold: int = 85,
) -> tuple:
    """
    Main entry point for dataclean.

    Parameters
    ----------
    source            : file path (CSV/JSON/Excel) or existing DataFrame
    fix               : 'all' or list of fixers e.g. ['columns', 'nulls']
    output            : optional path to save the cleaned file
    fuzzy_duplicates  : use fuzzy matching for deduplication
    outlier_method    : 'iqr' or 'zscore'
    category_threshold: similarity % for category merging (default 85)
    duplicate_threshold: similarity % for fuzzy dedup (default 85)

    Returns
    -------
    (clean_df, report) — cleaned DataFrame and full audit report
    """
    report = CleanReport()

    # ── Load ────────────────────────────────────────────────
    encoding = "utf-8"
    if not isinstance(source, pd.DataFrame):
        encoding = fix_encoding(source, report)

    try:
        df = _load(source, encoding=encoding)
    except UnicodeDecodeError:
        df = _load(source, encoding="latin-1")
        report.log("encoding", str(source), "fallback to latin-1 encoding")

    def should_run(name):
        return fix == "all" or name in fix

    # ── Step 1: Normalize column names ──────────────────────
    if should_run("columns"):
        df = fix_columns(df, report)

    # ── Step 2: Fix string encoding ─────────────────────────
    if should_run("encoding"):
        df = fix_string_encoding(df, report)

    # ── Step 3: Unify hidden nulls & sentinels ──────────────
    if should_run("nulls"):
        df = fix_nulls(df, report)

    # ── Step 4: Fix mixed types ─────────────────────────────
    if should_run("types"):
        df = fix_types(df, report)

    # ── Step 5: Normalize dates ─────────────────────────────
    if should_run("dates"):
        df = fix_dates(df, report)

    # ── Step 6: Remove duplicates ───────────────────────────
    if should_run("duplicates"):
        id_cols = [
            col for col in df.columns
            if col.lower() == "id"
            or col.lower().endswith("_id")
            or col.lower().startswith("id_")
        ]
        df = fix_duplicates(
            df,
            report,
            method="fuzzy" if fuzzy_duplicates else "exact",
            threshold=duplicate_threshold,
            exclude_cols=id_cols
        )

    # ── Step 7: Normalize category labels ───────────────────
    if should_run("categories"):
        df = fix_categories(df, report, threshold=category_threshold)

    # ── Step 8: Flag outliers ────────────────────────────────
    if should_run("outliers"):
        df = flag_outliers(df, report, method=outlier_method)

    # ── Step 9: Reset index ──────────────────────────────────
    df = df.reset_index(drop=True)

    # ── Step 10: Save output ─────────────────────────────────
    if output:
        out_path = Path(output)
        ext = out_path.suffix.lower()
        if ext == ".csv":
            df.to_csv(output, index=False)
        elif ext in {".xlsx", ".xls"}:
            df.to_excel(output, index=False)
        elif ext == ".json":
            df.to_json(output, orient="records", indent=2)
        report.log("output", str(output), f"cleaned file saved to '{output}'")

    return df, report