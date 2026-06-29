import pandas as pd
import pytest
from pipeline.models.instrument import Instrument
from pipeline.instrument_transformer import InstrumentTransformer
from pathlib import Path


@pytest.fixture
def transformer() -> InstrumentTransformer:
    """Create an InstrumentTransformer instance."""
    return InstrumentTransformer()


def test_to_dataframe_produces_correct_columns(
    transformer: InstrumentTransformer,
) -> None:
    """The DataFrame has exactly the required columns"""
    instruments = [Instrument(Id="ID1", FullNm="Test Name", Issr="ISSUER1")]

    df = transformer.to_dataframe(instruments)

    expected_columns = {
        "FinInstrmGnlAttrbts.Id",
        "FinInstrmGnlAttrbts.FullNm",
        "FinInstrmGnlAttrbts.ClssfctnTp",
        "FinInstrmGnlAttrbts.CmmdtyDerivInd",
        "FinInstrmGnlAttrbts.NtnlCcy",
        "Issr",
        "a_count",
        "contains_a",
    }
    assert set(df.columns) == expected_columns


def test_a_count_counts_lowercase_a_only(transformer: InstrumentTransformer) -> None:
    """a_count counts only lowercase 'a', not uppercase 'A'"""
    instruments = [
        Instrument(Id="ID1", FullNm="aaaaAAA"),
        Instrument(Id="ID2", FullNm="AAAA"),
    ]

    df = transformer.to_dataframe(instruments)

    assert df.loc[0, "a_count"] == 4
    assert df.loc[1, "a_count"] == 0


def test_a_count_is_zero_when_full_nm_missing(
    transformer: InstrumentTransformer,
) -> None:
    """a_count is 0 when FullNm is missing"""
    instruments = [Instrument(Id="ID1", FullNm=None)]

    df = transformer.to_dataframe(instruments)

    assert df.loc[0, "a_count"] == 0


def test_contains_a_matches_a_count(transformer: InstrumentTransformer) -> None:
    """contains_a is 'YES' when a_count > 0, 'NO' when a_count is 0"""
    instruments = [
        Instrument(Id="ID1", FullNm="aaaA"),
        Instrument(Id="ID2", FullNm=None),
        Instrument(Id="ID3", FullNm="A"),
    ]

    df = transformer.to_dataframe(instruments)

    assert df.loc[0, "contains_a"] == "YES"
    assert df.loc[1, "contains_a"] == "NO"
    assert df.loc[2, "contains_a"] == "NO"


def test_process_contains_a_raises_without_a_count(
    transformer: InstrumentTransformer,
) -> None:
    """_process_contains_a raises ValueError if a_count doesn't exist yet."""
    df = pd.DataFrame({"FinInstrmGnlAttrbts.FullNm": ["test"]})

    with pytest.raises(ValueError, match="a_count"):
        transformer._process_contains_a(df)


def test_to_csv_writes_correct_content(
    transformer: InstrumentTransformer, tmp_path: Path
) -> None:
    """to_csv() writes a CSV file with the correct content."""
    instruments = [Instrument(Id="ID1", FullNm="aaaAA", Issr="ISSUER1")]
    df = transformer.to_dataframe(instruments)

    # pytest already handles tmp directories
    output_path = tmp_path / "output.csv"

    transformer.to_csv(df, str(output_path))

    written = pd.read_csv(output_path)
    assert written.loc[0, "FinInstrmGnlAttrbts.Id"] == "ID1"
    assert written.loc[0, "a_count"] == 3
    assert written.loc[0, "contains_a"] == "YES"
