import pandas as pd
from rapidfuzz import fuzz


def _rows_are_similar(row1: pd.Series, row2: pd.Series, threshold: int = 85) -> bool:
    """
    Compare two rows using fuzzy matching.
    """
    scores = []

    for val1, val2 in zip(row1, row2):
        # both null → equal
        if pd.isna(val1) and pd.isna(val2):
            scores.append(100)
            continue

        # one null → not equal
        if pd.isna(val1) or pd.isna(val2):
            scores.append(0)
            continue

        score = fuzz.ratio(str(val1).lower().strip(), str(val2).lower().strip())
        scores.append(score)

    if not scores:
        return False

    return (sum(scores) / len(scores)) >= threshold


def fix_duplicates(
    df: pd.DataFrame,
    report=None,
    threshold: int = 85,
    method: str = "exact",
    exclude_cols: list = None
) -> pd.DataFrame:
    """
    Detect and remove duplicate rows.

    Parameters
    ----------
    method : "exact" or "fuzzy"
    threshold : similarity % for fuzzy matching
    exclude_cols : list of columns to ignore (e.g., ID columns)
    """

    if exclude_cols is None:
        exclude_cols = []

    # Columns used for comparison
    subset_cols = [col for col in df.columns if col not in exclude_cols]

    original_len = len(df)

    # ---------------- Exact Duplicates ---------------- #
    df = df.drop_duplicates(subset=subset_cols)
    exact_removed = original_len - len(df)

    if report and exact_removed > 0:
        report.log(
            "duplicates",
            f"{subset_cols}",
            f"{exact_removed} exact duplicate row(s) removed"
        )

    # ---------------- Fuzzy Duplicates ---------------- #
    if method == "fuzzy":
        df = df.reset_index(drop=True)
        to_drop = set()

        rows = df[subset_cols].values.tolist()
        indices = list(range(len(rows)))

        # ⚠️ Performance guard (avoid O(n^2) explosion)
        if len(rows) > 2000:
            if report:
                report.log(
                    "duplicates",
                    "fuzzy",
                    "skipped fuzzy deduplication (dataset too large)"
                )
            return df

        for i in indices:
            if i in to_drop:
                continue

            for j in indices[i + 1:]:
                if j in to_drop:
                    continue

                if _rows_are_similar(
                    pd.Series(rows[i]),
                    pd.Series(rows[j]),
                    threshold=threshold
                ):
                    to_drop.add(j)

        fuzzy_removed = len(to_drop)

        if fuzzy_removed > 0:
            df = df.drop(index=list(to_drop)).reset_index(drop=True)

            if report:
                report.log(
                    "duplicates",
                    f"{subset_cols}",
                    f"{fuzzy_removed} fuzzy duplicate row(s) removed "
                    f"(threshold={threshold}%)"
                )

    return df