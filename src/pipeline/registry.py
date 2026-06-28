import logging
from collections.abc import Iterator
from xml.etree import ElementTree
from pipeline.models.file_record import FileRecord
from pipeline.clients.downloader import Downloader
from pipeline.exceptions import ParseError, NoMatchingRecordError
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class EsmaRegistryClient:
    def __init__(self, downloader: Downloader):
        self.downloader = downloader

    def download_registry(self, url: str) -> bytes:
        """Download the ESMA registry file from the given URL.

        Args:
            url: The url to download the registry from.

        Returns:
            The bytes of the downloaded file.

        """
        return self.downloader.download(url)

    def parse_xml(self, xml_content: bytes) -> Iterator[FileRecord]:
        """Parse the xml content and yield FileRecord objects.

        Args:
            xml_content: the xml content to parse in bytes.

        Yields:
            One FileRecord object for each doc element in the xml.

        Raises:
            ParseError: If a xml doc element is invalid or missing fields.
        """

        root = ElementTree.fromstring(xml_content)
        for doc in root.iter("doc"):
            fields_dict = self._extract_fields(doc)
            try:
                # yield pauses execution here, making the caller method
                # handle the record before iterating to the next one.
                yield FileRecord(**fields_dict)
            except ValidationError as exc:
                logger.error(f"Failed to parse record: {fields_dict}. Error: {exc}")
                raise ParseError(f"Invalid xml element: {exc}") from exc

    def select_record(
        self, records: Iterator[FileRecord], file_type: str, index: int
    ) -> FileRecord:
        """Select a specific record that matches file_type and index

        Args:
            records: FileRecord iterator.
            file_type: The file type to filter.
            index: index which represents the order of the record to select after file_type filter.

        Returns:
            The selected FileRecord.

        Raises:
            NoMatchingRecordError: If no record matches the given file_type and index.
        """
        count = 0
        for record in records:
            if record.file_type != file_type:
                continue
            if count == index:
                logger.info(f"Selected record: {record}")
                return record
            count += 1

        logger.error(f"No record found for file_type={file_type} at index={index}")
        raise NoMatchingRecordError(
            f"No record found for file_type={file_type} at index={index}"
        )

    @staticmethod
    def _extract_fields(doc: ElementTree.Element) -> dict[str, str]:
        """Extract fields from doc element into dict"""
        fields_dict: dict[str, str] = {}
        for field in doc:
            name = field.get("name")
            text = field.text
            if name is not None and text is not None:
                fields_dict[name] = text
        return fields_dict
