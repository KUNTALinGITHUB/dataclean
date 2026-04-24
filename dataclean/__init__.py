from .cleaner import clean
from .fixers.columns import fix_columns
from .fixers.nulls import fix_nulls
from .fixers.types import fix_types
from .fixers.dates import fix_dates
from .fixers.duplicates import fix_duplicates
from .fixers.categories import fix_categories
from .fixers.outliers import flag_outliers
from .fixers.encoding import fix_encoding, fix_string_encoding
from .report import CleanReport

__version__ = "0.1.2"
__author__ = "KUNTALinGITHUB"
__doc__ = "A Python library for automated data cleaning and auditing with detailed reporting. developed by Kuntal Pal (Independent Researcher, Kolkata, India). email: kuntal.pal7550@gmail.com"
__license__ = "MIT"

__all__ = [
    "clean",
    "fix_columns",
    "fix_nulls",
    "fix_types",
    "fix_dates",
    "fix_duplicates",
    "fix_categories",
    "flag_outliers",
    "fix_encoding",
    "fix_string_encoding",
    "CleanReport",
]