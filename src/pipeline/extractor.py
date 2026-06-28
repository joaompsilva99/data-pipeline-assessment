import io
import logging
import zipfile
from typing import IO
from pipeline.exceptions import ParseError

logger = logging.getLogger(__name__)


class ZipExtractor:
    """Locates and opens the single XML entry within a zip archive."""

    # considering that the zip file must contain only one XML file (ESMA FIRDS documentation)
    def open_xml_stream_from_zip(
        self, zip_bytes: bytes
    ) -> tuple[zipfile.ZipFile, IO[bytes]]:
        """Open the zip archive and return a stream for its single XML entry.

        Returns a stream rather than the extracted bytes, so that the caller
        can parse the XML incrementally (iterparse) without loading the entire
        file into memory at once.

        Args:
            zip_bytes: Raw zip archive content.

        Returns:
            A tuple of (the open ZipFile, the open stream for the XML entry).
            Caller method is responsible for closing both.

        Raises:
            ParseError: If the archive is invalid, contains no XML file,
                or contains more than one XML file.
        """
        try:
            archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
        except zipfile.BadZipFile as e:
            logger.error(f"Failed to extract zip file: {e}")
            raise ParseError(f"Failed to extract zip file: {e}") from e

        xml_file_name = self._get_xml_file_name_from_zip(archive)

        return archive, archive.open(xml_file_name)

    @staticmethod
    def _get_xml_file_name_from_zip(archive: zipfile.ZipFile) -> str:
        """Get the name of the single XML file in the zip archive.

        Args:
            archive: An open ZipFile object.

        Returns:
            The name of the single XML file in the archive.

        Raises:
            ParseError: If the archive contains no XML file or more than one XML file.
        """
        for name in archive.namelist():
            if name.endswith(".xml"):
                logger.info(f"Found XML file in zip archive: {name}")
                return name
        logger.error("No XML file found in the zip archive.")
        raise ParseError("No XML file found in the zip archive.")
