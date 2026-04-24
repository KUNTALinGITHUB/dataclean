import re
import pandas as pd


def fix_columns(df: pd.DataFrame, report=None) -> pd.DataFrame:
    """
    Normalize all column names to snake_case.
    - Strips leading/trailing whitespace
    - Converts to lowercase
    - Replaces spaces and special characters with underscores
    - Removes duplicate underscores
    """
    new_columns = {}

    for col in df.columns:
        new_col = col.strip()
        new_col = new_col.lower()
        new_col = re.sub(r"[^\w\s]", "_", new_col)
        new_col = re.sub(r"[\s]+", "_", new_col)
        new_col = re.sub(r"_+", "_", new_col)
        new_col = new_col.strip("_")

        if new_col != col:
            new_columns[col] = new_col
            if report:
                report.log("columns", col, f"renamed to '{new_col}'")

    df = df.rename(columns=new_columns)
    return df