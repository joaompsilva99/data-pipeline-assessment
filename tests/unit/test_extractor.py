import io
import zipfile
import pytest
from pipeline.extractor import ZipExtractor
from pipeline.exceptions import ParseError


def _build_zip(files: dict[str, bytes]) -> bytes:
    """Build an in-memory zip archive containing the given files.

    Args:
        files: Mapping of filename -> file content to include in the zip.

    Returns:
        The zip archive's raw bytes.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


class TestOpenXmlStreamFromZip:
    """Tests for ZipExtractor.open_xml_stream_from_zip()."""

    def test_returns_stream_with_correct_content(self) -> None:
        """The returned stream yields the correct XML content when read."""
        xml_content = b"<root><doc>hello</doc></root>"
        zip_bytes = _build_zip({"instrument.xml": xml_content})

        extractor = ZipExtractor()
        archive, stream = extractor.open_xml_stream_from_zip(zip_bytes)

        try:
            assert stream.read() == xml_content
        finally:
            stream.close()
            archive.close()

    def test_finds_xml_alongside_other_files(self) -> None:
        """The XML entry is found even when other file types are present."""
        xml_content = b"<root>data</root>"
        zip_bytes = _build_zip(
            {"metadata.txt": b"some metadata", "instrument.xml": xml_content}
        )

        extractor = ZipExtractor()
        archive, stream = extractor.open_xml_stream_from_zip(zip_bytes)

        try:
            assert stream.read() == xml_content
        finally:
            stream.close()
            archive.close()

    def test_raises_when_no_xml_present(self) -> None:
        """Raises ParseError when the archive contains no .xml file."""
        zip_bytes = _build_zip({"readme.txt": b"not xml"})

        extractor = ZipExtractor()
        with pytest.raises(ParseError):
            extractor.open_xml_stream_from_zip(zip_bytes)

    def test_raises_on_invalid_zip(self) -> None:
        """Raises ParseError when given invalid/corrupted zip bytes."""
        invalid_zip_bytes = b"this is not a real zip file"

        extractor = ZipExtractor()
        with pytest.raises(ParseError):
            extractor.open_xml_stream_from_zip(invalid_zip_bytes)
