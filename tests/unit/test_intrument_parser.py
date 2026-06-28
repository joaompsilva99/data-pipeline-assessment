import io
import pytest
from pipeline.exceptions import ParseError
from pipeline.instrument_parser import InstrumentParser


@pytest.fixture
def parser() -> InstrumentParser:
    """Create an InstrumentParser instance."""
    return InstrumentParser()


class TestParseXml:
    """Tests for InstrumentParser.parse_xml()."""

    def test_parses_complete_instrument(self, parser: InstrumentParser) -> None:
        """A fully populated <FinInstrm> is parsed into a matching Instrument."""
        xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
  <FinInstrmRptgRefDataDltaRpt>
    <FinInstrm>
      <ModfdRcrd>
        <FinInstrmGnlAttrbts>
          <Id>AT0000A2B3D9</Id>
          <FullNm>EGB OE TL.Z./SARTORIUS V</FullNm>
          <ShrtNm>ERSTE GRP/C WT SRT3 147.92 OE</ShrtNm>
          <ClssfctnTp>RWSNCA</ClssfctnTp>
          <NtnlCcy>EUR</NtnlCcy>
          <CmmdtyDerivInd>false</CmmdtyDerivInd>
        </FinInstrmGnlAttrbts>
        <Issr>PQOH26KWDF7CG10L6792</Issr>
      </ModfdRcrd>
    </FinInstrm>
  </FinInstrmRptgRefDataDltaRpt>
</Document>"""

        instruments = parser.parse_xml(io.BytesIO(xml_bytes))

        assert len(instruments) == 1
        instr = instruments[0]
        assert instr.Id == "AT0000A2B3D9"
        assert instr.FullNm == "EGB OE TL.Z./SARTORIUS V"
        assert instr.ClssfctnTp == "RWSNCA"
        assert instr.NtnlCcy == "EUR"
        assert instr.CmmdtyDerivInd == "false"
        assert instr.Issr == "PQOH26KWDF7CG10L6792"

    def test_parses_multiple_instruments(self, parser: InstrumentParser) -> None:
        """Multiple Instrument elements."""
        xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
  <FinInstrmRptgRefDataDltaRpt>
    <FinInstrm>
      <ModfdRcrd>
        <FinInstrmGnlAttrbts><Id>ID1</Id></FinInstrmGnlAttrbts>
        <Issr>ISSUER1</Issr>
      </ModfdRcrd>
    </FinInstrm>
    <FinInstrm>
      <ModfdRcrd>
        <FinInstrmGnlAttrbts><Id>ID2</Id></FinInstrmGnlAttrbts>
        <Issr>ISSUER2</Issr>
      </ModfdRcrd>
    </FinInstrm>
  </FinInstrmRptgRefDataDltaRpt>
</Document>"""

        instruments = parser.parse_xml(io.BytesIO(xml_bytes))

        assert len(instruments) == 2
        assert instruments[0].Id == "ID1"
        assert instruments[1].Id == "ID2"

    def test_missing_full_nm_results_in_none(self, parser: InstrumentParser) -> None:
        """An Instruments missing FullNm parses with FullNm=None without raising error"""
        xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
  <FinInstrmRptgRefDataDltaRpt>
    <FinInstrm>
      <ModfdRcrd>
        <FinInstrmGnlAttrbts>
          <Id>AT0000A2B3D9</Id>
          <ClssfctnTp>RWSNCA</ClssfctnTp>
        </FinInstrmGnlAttrbts>
        <Issr>PQOH26KWDF7CG10L6792</Issr>
      </ModfdRcrd>
    </FinInstrm>
  </FinInstrmRptgRefDataDltaRpt>
</Document>"""

        instruments = parser.parse_xml(io.BytesIO(xml_bytes))

        assert instruments[0].FullNm is None

    def test_missing_id_raises_parse_error(self, parser: InstrumentParser) -> None:
        """An Instrument missing the required Id field raises ParseError"""
        xml_bytes = b"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:auth.036.001.02">
  <FinInstrmRptgRefDataDltaRpt>
    <FinInstrm>
      <ModfdRcrd>
        <FinInstrmGnlAttrbts>
          <FullNm>Missing ID Instrument</FullNm>
        </FinInstrmGnlAttrbts>
        <Issr>PQOH26KWDF7CG10L6792</Issr>
      </ModfdRcrd>
    </FinInstrm>
  </FinInstrmRptgRefDataDltaRpt>
</Document>"""

        with pytest.raises(ParseError):
            parser.parse_xml(io.BytesIO(xml_bytes))
