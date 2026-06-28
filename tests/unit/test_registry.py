import pytest
from unittest.mock import Mock
from pathlib import Path
from pipeline.exceptions import NoMatchingRecordError, ParseError
from pipeline.registry import EsmaRegistryClient


XML_SAMPLE_PATH = Path(__file__).parent.parent / "fixtures" / "registry_response.xml"


@pytest.fixture
def sample_xml_bytes() -> bytes:
    """Load the registry_response sample XML."""
    return XML_SAMPLE_PATH.read_bytes()


@pytest.fixture
def client() -> EsmaRegistryClient:
    """Create an EsmaRegistryClient for parse/select tests."""
    return EsmaRegistryClient(downloader=Mock())


class TestParse:
    """Tests for EsmaRegistryClient.parse_xml()."""

    def test_returns_one_record_per_doc(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """parse_xml() yields one FileRecord per doc element."""
        records = list(client.parse_xml(sample_xml_bytes))
        assert len(records) == 4

    def test_extracts_correct_fields(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """parse_xml() correctly extracts all expected fields for the first record."""
        records = list(client.parse_xml(sample_xml_bytes))
        first = records[0]

        assert first.id == "46015"
        assert first.file_name == "DLTINS_20210117_01of01.zip"
        assert first.file_type == "DLTINS"
        assert (
            str(first.download_link)
            == "https://firds.esma.europa.eu/firds/DLTINS_20210117_01of01.zip"
        )

    def test_raises_parse_error_when_required_field_missing(
        self, client: EsmaRegistryClient
    ) -> None:
        """parse_xml() raises ParseError when a <doc> is missing a required field."""
        malformed_xml = b"""<?xml version="1.0"?>
        <response>
          <result>
            <doc>
              <str name="id">123</str>
            </doc>
          </result>
        </response>"""

        with pytest.raises(ParseError):
            list(client.parse_xml(malformed_xml))


class TestSelect:
    """Tests for EsmaRegistryClient.select_record()"""

    def test_returns_second_dltins_record(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """select_record() with index=1 returns the second DLTINS record"""
        records = client.parse_xml(sample_xml_bytes)
        selected = client.select_record(records, file_type="DLTINS", index=1)

        assert selected.id == "46051"
        assert selected.file_name == "DLTINS_20210119_01of02.zip"
        assert selected.file_type == "DLTINS"

    def test_raises_when_index_out_of_range(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """select_record() raises NoMatchingRecordError when index goes out of bounds"""
        records = client.parse_xml(sample_xml_bytes)

        with pytest.raises(NoMatchingRecordError):
            client.select_record(records, file_type="DLTINS", index=10)

    def test_raises_when_file_type_not_found(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """select_record() raises NoMatchingRecordError when no record matches file_type"""
        records = client.parse_xml(sample_xml_bytes)

        with pytest.raises(NoMatchingRecordError):
            client.select_record(records, file_type="NOTREAL", index=0)

    def test_stops_early_without_exhausting_iterator(
        self, client: EsmaRegistryClient, sample_xml_bytes: bytes
    ) -> None:
        """select_record() returns as soon as the target is found, without consuming the rest of the iterator."""
        records = client.parse_xml(sample_xml_bytes)
        client.select_record(records, file_type="DLTINS", index=1)

        # Only 2 of the 4 records should have been consumed from the generator
        # since the matching record is found at index 1
        remaining = list(records)
        assert len(remaining) == 2
