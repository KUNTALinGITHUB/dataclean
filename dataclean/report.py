import pandas as pd
from datetime import datetime


class CleanReport:
    """
    Audit trail for all changes made by dataclean.
    Tracks every fix applied — what changed, which column, and why.
    """

    def __init__(self):
        self.changes = []
        self.started_at = datetime.now()

    def log(self, fixer: str, column: str, message: str):
        """Record a single change made by a fixer."""
        self.changes.append({
            "fixer":   fixer,
            "column":  column,
            "detail":  message,
            "time":    datetime.now().strftime("%H:%M:%S")
        })

    def summary(self):
        """Print a human-readable summary of all changes."""
        if not self.changes:
            print("No changes were made — data looks clean!")
            return

        print(f"\n{'='*55}")
        print(f"  dataclean report — {len(self.changes)} change(s) made")
        print(f"{'='*55}")

        current_fixer = None
        for c in self.changes:
            if c["fixer"] != current_fixer:
                current_fixer = c["fixer"]
                print(f"\n  [{current_fixer.upper()}]")
            print(f"    • {c['column']}: {c['detail']}")

        print(f"\n{'='*55}")
        duration = (datetime.now() - self.started_at).total_seconds()
        print(f"  completed in {duration:.2f}s")
        print(f"{'='*55}\n")

    def to_dict(self) -> list:
        """Return changes as a list of dicts."""
        return self.changes

    def to_df(self) -> pd.DataFrame:
        """Return changes as a pandas DataFrame."""
        if not self.changes:
            return pd.DataFrame(
                columns=["fixer", "column", "detail", "time"]
            )
        return pd.DataFrame(self.changes)

    def has_changes(self) -> bool:
        """Return True if any changes were made."""
        return len(self.changes) > 0

    def changes_for(self, fixer: str) -> list:
        """Return only changes made by a specific fixer."""
        return [c for c in self.changes if c["fixer"] == fixer]

    def __repr__(self):
        return f"CleanReport({len(self.changes)} change(s))"