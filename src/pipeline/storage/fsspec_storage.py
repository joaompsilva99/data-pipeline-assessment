import logging
import pandas as pd
from pipeline.storage.base_storage import StorageBase
from pipeline.exceptions import StorageError

logger = logging.getLogger(__name__)


class FsspecStorage(StorageBase):
    """StorageBase implementation using fsspec.

    A single interface that supports various filesystems
    such as disk, S3(s3://), Azure Blob storage (az://),
    google cloud storage (gcs://), through a single destination
    uri.
    """

    def write_csv(self, df: pd.DataFrame, destination: str) -> None:
        """Write a DataFrame as CSV via pandas' fsspec integration.

        Args:
            df: The DataFrame to write.
            destination: Any fsspec-compatible URI or local path.
        """
        logger.info(f"Writing df as csv to {destination}")
        try:
            # this method contains support for fsspec.open
            df.to_csv(destination, index=False)
        except Exception as e:
            error_message = f"Failed writing df as csv to {destination}"
            logger.error(f"{error_message}: {e}")
            raise StorageError(error_message)
        logger.info(f"Sucessfully wrote to {destination}")
