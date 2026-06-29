import logging
import pandas as pd
import numpy as np
from pipeline.models.instrument import Instrument
from pathlib import Path

logger = logging.getLogger(__name__)


class InstrumentTransformer:
    COLUMN_RENAME = {
        "Id": "FinInstrmGnlAttrbts.Id",
        "FullNm": "FinInstrmGnlAttrbts.FullNm",
        "ClssfctnTp": "FinInstrmGnlAttrbts.ClssfctnTp",
        "CmmdtyDerivInd": "FinInstrmGnlAttrbts.CmmdtyDerivInd",
        "NtnlCcy": "FinInstrmGnlAttrbts.NtnlCcy",
        "Issr": "Issr",
    }

    def to_dataframe(self, instruments: list[Instrument]) -> pd.DataFrame:
        """Convert parsed instruments into a DataFrame with the required columns.

        Args:
            instruments: The complete list of parsed Instrument objects.

        Returns:
            A dataframe with the required processed data.
        """
        rows = [instrument.model_dump() for instrument in instruments]

        df = pd.DataFrame(rows)
        df = df.rename(columns=self.COLUMN_RENAME)

        self._process_a_count(df)
        self._process_contains_a(df)

        return df

    def to_csv(self, df: pd.DataFrame, path: str | Path) -> None:
        """Write the DataFrame to a CSV file.

        Args:
            df: The DataFrame to write.
            path: Output file path.
        """
        df.to_csv(path, index=False)
        logger.info(f"Wrote {len(df)} rows to {path}")

    def _process_a_count(self, df: pd.DataFrame) -> None:
        """Add the a_count column: 'a' occurrences in FullNm column.

        Args:
            df: The DataFrame to mutate in place. Missing values
            will be treated as 0.
        """
        # fillna fills missing data rows (NaN/None)-> ""
        # use pd.series str for string methods
        df["a_count"] = df["FinInstrmGnlAttrbts.FullNm"].fillna("").str.count("a")

    def _process_contains_a(self, df: pd.DataFrame) -> None:
        """Derive the contains_a column from a_count.

        Args:
            df: The DataFrame to mutate in place. Must already have an
                'a_count' column.

        Raises:
            ValueError: If 'a_count' is not already present in df.
        """

        # np.where is implemented in C and operates on the whole array at
        # once, avoiding the per-row Python function calls that .apply() uses
        # df["contains_a"] = df["a_count"].apply(lambda x: "YES" if x > 0 else "NO")
        if "a_count" not in df.columns:
            raise ValueError(
                "'a_count' column must exist in order to create 'contains_a' column"
            )
        df["contains_a"] = np.where(df["a_count"] > 0, "YES", "NO")
