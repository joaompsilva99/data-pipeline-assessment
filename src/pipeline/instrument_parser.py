import logging
from typing import IO
from xml.etree import ElementTree
from pydantic import ValidationError
from pipeline.models.instrument import Instrument
from pipeline.exceptions import ParseError

logger = logging.getLogger(__name__)


class InstrumentParser:
    """Parses FIRDS instrument XML into Instrument records."""

    def parse_xml(self, source: IO[bytes]) -> list[Instrument]:
        """Parse a FIRDS instrument XML stream into Instrument objects.

        Args:
            source: A stream containing the instrument XML (returned by ZipExtractor class)

        Returns:
            A list of Instrument objects.

        Raises:
            ParseError: If a <FinInstrm> element can not be turned into
            Instrument model object.
        """

        result: list[Instrument] = []
        for _, elem in ElementTree.iterparse(source, events=("end",)):
            if self._local_name(elem.tag) != "FinInstrm":
                continue
            try:
                result.append(self._build_instrument(elem))
            except ValidationError as exc:
                logger.error(f"Failed to parse instrument: {exc}")
                raise ParseError(f"Invalid FinInstrm element: {exc}") from exc
            finally:
                # free memory after processing each element
                elem.clear()

        logger.info(f"Parsed {len(result)} instruments")
        return result

    def _build_instrument(self, elem: ElementTree.Element) -> Instrument:
        """Extract the required fields from a FinInstrm element into Instrument object.

        Args:
            elem: The complete FinInstrm element.

        Returns:
            The respective Instrument.
        """
        found_elements_dict = self._find_all_elements_by_tags(
            elem, {"FinInstrmGnlAttrbts", "Issr"}
        )

        gnl_attrbts = found_elements_dict.get("FinInstrmGnlAttrbts")

        fields: dict[str, str] = {}
        if gnl_attrbts is not None:
            self._extract_fields(gnl_attrbts, fields)

        # does not contain multiple fields
        issr = found_elements_dict.get("Issr")
        if issr is not None and issr.text is not None:
            fields["Issr"] = issr.text

        return Instrument(**fields)

    def _find_all_elements_by_tags(
        self, parent: ElementTree.Element, tags: set[str]
    ) -> dict[str, ElementTree.Element]:
        """Find multiple descendant elements by tag name in a single pass.

        Searches recursively (any depth), since the record wrapper tag
        between FinInstrm and its fields can vary. Stops early once
        every requested tag has been found.

        Args:
            parent: The element to search within.
            tags: The set of tag names to search for.

        Returns:
            A dict mapping each found tag name to its element.
        """
        found_elements: dict[str, ElementTree.Element] = {}
        remaining_elements = set(tags)

        for child in parent.iter():
            local_name = self._local_name(child.tag)
            if local_name in remaining_elements:
                found_elements[local_name] = child
                remaining_elements.discard(local_name)
                if not remaining_elements:
                    break

        return found_elements

    @staticmethod
    def _local_name(tag: str) -> str:
        """Strip the namespace from a tag, returning just its local name."""
        return tag.split("}")[-1]

    def _extract_fields(
        self, elem: ElementTree.Element, fields: dict[str, str]
    ) -> None:
        """Extract elem children into the given fields dict."""
        for child in elem:
            text = child.text
            if text is not None:
                fields[self._local_name(child.tag)] = text
