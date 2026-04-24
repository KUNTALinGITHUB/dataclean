import pandas as pd
from rapidfuzz import fuzz, process


def _is_categorical_column(series: pd.Series, max_unique_ratio: float = 0.3) -> bool:
    """
    Check if a column looks categorical.
    Handles both object and Pandas 3 StringDtype.
    """
    if series.dtype != object and "str" not in str(series.dtype):
        return False

    total = len(series.dropna())
    if total == 0:
        return False

    unique = series.nunique()
    ratio = unique / total

    return ratio <= max_unique_ratio and unique <= 50


def _group_similar_labels(labels: list, threshold: int = 85) -> dict:
    """
    Group similar labels together using fuzzy matching.
    Returns a mapping of {original_label: canonical_label}.
    """
    mapping = {}
    canonical_labels = []

    for label in sorted(labels):
        label_str = str(label).strip()

        if not canonical_labels:
            canonical_labels.append(label_str)
            mapping[label_str] = label_str
            continue

        match = process.extractOne(
            label_str,
            canonical_labels,
            scorer=fuzz.ratio
        )

        if match and match[1] >= threshold:
            mapping[label_str] = match[0]
        else:
            canonical_labels.append(label_str)
            mapping[label_str] = label_str

    return mapping


def fix_categories(
    df: pd.DataFrame,
    report=None,
    threshold: int = 85
) -> pd.DataFrame:
    """
    Detect inconsistent category labels and normalize them.
    - Groups similar labels using fuzzy matching
    - Normalizes casing and whitespace
    - e.g. 'USA', 'U.S.A', 'united states' → 'USA'
    """
    for col in df.columns:
        if not _is_categorical_column(df[col]):
            continue

        # normalize: preserve pd.NA, only process real string values
        df[col] = df[col].apply(
            lambda x: x.strip().lower() if isinstance(x, str) else x
        )

        unique_labels = df[col].dropna().unique().tolist()

        if len(unique_labels) <= 1:
            continue

        mapping = _group_similar_labels(unique_labels, threshold=threshold)

        merges = {k: v for k, v in mapping.items() if k != v}

        if merges:
            df[col] = df[col].apply(
                lambda x: mapping.get(x, x) if isinstance(x, str) else x
            )

            if report:
                for original, canonical in merges.items():
                    report.log(
                        "categories", col,
                        f"'{original}' merged into '{canonical}'"
                    )

    return df