import logging
import requests
from pipeline.exceptions import DownloadError

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, timeout: int = 30):
        """Init the Downloader.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    def download(self, url: str) -> bytes:
        """Download the content from the given URL and return it as bytes.

        Args:
            url: The url to fetch the content from.

        Returns:
            The response content as bytes.

        Raises:
            DownloadError: If the download fails due to an HTTP error or connection issue.
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download from {url}: {e}")
            # from e shows traceback with exact error raised
            raise DownloadError(f"Failed to download from {url}: {e}") from e

        logger.debug("Downloaded %d bytes from %s", len(response.content), url)
        return response.content
