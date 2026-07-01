import pandas as pd
import pytest
from pipeline.storage.fsspec_storage import FsspecStorage
from pathlib import Path
from unittest.mock import patch
from pipeline.exceptions import StorageError


@pytest.fixture
def client() -> FsspecStorage:
    return FsspecStorage()


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "FinInstrmGnlAttrbts.Id": ["ID1", "ID2"],
            "FinInstrmGnlAttrbts.FullNm": ["Name One", None],
            "a_count": [1, 0],
            "contains_a": ["YES", "NO"],
        }
    )


def test_write_csv_to_local_path(
    client: FsspecStorage,
    sample_df: pd.DataFrame,
    tmp_path: Path,
) -> None:
    """write_csv() writes correct CSV content to a local path"""
    destination = str(tmp_path / "output.csv")

    client.write_csv(sample_df, destination)

    written = pd.read_csv(destination)
    assert len(written) == 2
    assert written.loc[0, "FinInstrmGnlAttrbts.Id"] == "ID1"
    assert written.loc[0, "a_count"] == 1
    assert written.loc[0, "contains_a"] == "YES"


def test_write_csv_raises_storage_error(
    client: FsspecStorage, sample_df: pd.DataFrame, tmp_path: Path
) -> None:
    destination = str(tmp_path / "output.csv")

    with patch.object(pd.DataFrame, "to_csv", side_effect=Exception("disk error")):
        with pytest.raises(StorageError):
            client.write_csv(sample_df, destination)


#! could not resolve dependency issues between
# s3fs (async aiobotocore) and mocking library moto:
# def test_write_csv_to_s3(
#     client: FsspecStorage,
#     sample_df: pd.DataFrame,
# ) -> None:
#     """write_csv() writes correct CSV content to S3 via moto."""
#     boto3 = pytest.importorskip("boto3")
#     moto = pytest.importorskip("moto")

#     with moto.mock_aws():
#         boto3.client("s3", region_name="us-east-1").create_bucket(
#             Bucket="test-bucket"
#         )

#         client.write_csv(sample_df, "s3://test-bucket/output.csv")

#         s3 = boto3.client("s3", region_name="us-east-1")
#         obj = s3.get_object(Bucket="test-bucket", Key="output.csv")
#         content = obj["Body"].read().decode("utf-8")

#         assert "ID1" in content
#         assert "ID2" in content
#         assert "a_count" in content
