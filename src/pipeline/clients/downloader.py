import logging
import requests
from pipeline.exceptions import DownloadError

logger = logging.getLogger(__name__)


class Downloader:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    # Downloads the content from the given URL and returns it as bytes.
    def download(self, url: str) -> bytes:
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download from {url}: {e}")
            # from e shows traceback with exact error raised
            raise DownloadError(f"Failed to download from {url}: {e}") from e

        logger.debug("Downloaded %d bytes from %s", len(response.content), url)
        return response.content
