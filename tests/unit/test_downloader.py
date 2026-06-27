import pytest
import requests
import responses

from pipeline.exceptions import DownloadError
from pipeline.clients.downloader import Downloader


@responses.activate
def test_download_returns_content_on_success() -> None:
    """download() returns the response body bytes on a successful request."""
    url = "https://example.com/file.zip"
    responses.add(responses.GET, url, body=b"fake-zip-bytes", status=200)

    downloader = Downloader()
    result = downloader.download(url)

    assert result == b"fake-zip-bytes"


@responses.activate
def test_download_raises_download_error_on_http_error() -> None:
    """download() raises DownloadError when 400 or 500 error is returned."""
    url = "https://example.com/missing.zip"
    responses.add(responses.GET, url, status=404)

    downloader = Downloader()

    with pytest.raises(DownloadError):
        downloader.download(url)


@responses.activate
def test_download_raises_download_error_on_connection_failure() -> None:
    """download() raises DownloadError when the connection fails."""
    url = "https://example.com/unreachable.zip"
    responses.add(responses.GET, url, body=requests.exceptions.ConnectionError())

    downloader = Downloader()

    with pytest.raises(DownloadError):
        downloader.download(url)
