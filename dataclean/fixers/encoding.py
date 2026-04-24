import chardet
import pandas as pd


def detect_encoding(filepath: str) -> str:
    """
    Detect the encoding of a file using chardet.
    Returns the detected encoding string (e.g. 'utf-8', 'latin-1').
    """
    with open(filepath, "rb") as f:
        raw = f.read()
    result = chardet.detect(raw)
    encoding = result.get("encoding", "utf-8")
    confidence = result.get("confidence", 0)

    if not encoding or confidence < 0.5:
        encoding = "utf-8"

    return encoding


def fix_encoding(filepath: str, report=None) -> str:
    """
    Detect and report the encoding of a file.
    Returns the detected encoding so the loader can use it.
    Works at file level before DataFrame is created.
    """
    try:
        encoding = detect_encoding(filepath)

        if report:
            report.log(
                "encoding", filepath,
                f"detected encoding: '{encoding}' — file will be loaded with this encoding"
            )

        return encoding

    except Exception as e:
        if report:
            report.log(
                "encoding", filepath,
                f"could not detect encoding — defaulting to utf-8. Error: {e}"
            )
        return "utf-8"


def _try_fix_string(val) -> tuple:
    """
    Try to re-encode a single string value from latin-1 to utf-8.
    Returns (fixed_value, was_changed).
    """
    if pd.isna(val):
        return val, False
    try:
        fixed = val.encode("latin-1").decode("utf-8")
        return (fixed, True) if fixed != val else (val, False)
    except Exception:
        return val, False


def fix_string_encoding(df: pd.DataFrame, report=None) -> pd.DataFrame:
    """
    Fix broken unicode characters in string columns.
    Attempts to re-encode mangled strings back to clean utf-8.
    e.g. 'Jos\\xef' → 'José'
    """
    for col in df.select_dtypes(include=["object", "str"]).columns:
        results = df[col].apply(_try_fix_string)

        fixed_values = results.apply(lambda x: x[0])
        fixed_count = results.apply(lambda x: x[1]).sum()

        df[col] = fixed_values

        if report and fixed_count > 0:
            report.log(
                "encoding", col,
                f"{fixed_count} string(s) re-encoded from latin-1 to utf-8"
            )

    return df