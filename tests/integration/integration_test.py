import io
import zipfile
from pathlib import Path

import pandas as pd
import responses

from pipeline.clients.downloader import Downloader
from pipeline.extractor import ZipExtractor
from pipeline.instrument_parser import InstrumentParser
from pipeline.instrument_transformer import InstrumentTransformer
from pipeline.pipeline import Pipeline
from pipeline.registry import EsmaRegistryClient
from pipeline.storage.fsspec_storage import FsspecStorage

REGISTRY_URL = "https://registers.esma.europa.eu/solr/fake-query"
ZIP_URL = "https://firds.esma.europa.eu/firds/DLTINS_20210119_01of02.zip"

REGISTRY_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<response>
<result name="response" numFound="2" start="0" numFoundExact="true">
<doc>
<str name="_root_">46015</str>
<str name="id">46015</str>
<str name="published_instrument_file_id">46015</str>
<str name="file_name">DLTINS_20210117_01of01.zip</str>
<str name="file_type">DLTINS</str>
<date name="publication_date">2021-01-17T00:00:00Z</date>
<str name="download_link">https://firds.esma.europa.eu/firds/DLTINS_20210117_01of01.zip</str>
<str name="checksum">852b2dde71cf114289ad95ada2a4e406</str>
<long name="_version_">1869131847024246919</long>
<date name="timestamp">2026-06-27T06:50:36.199Z</date>
</doc>
<doc>
<str name="_root_">46051</str>
<str name="id">46051</str>
<str name="published_instrument_file_id">46051</str>
<str name="file_name">DLTINS_20210119_01of02.zip</str>
<str name="file_type">DLTINS</str>
<date name="publication_date">2021-01-19T00:00:00Z</date>
<str name="download_link">{ZIP_URL}</str>
<str name="checksum">3533fe597fc721ed139198503fe87910</str>
<long name="_version_">1869131847060947096</long>
<date name="timestamp">2026-06-27T06:50:36.199Z</date>
</doc>
</result>
</response>"""

INSTRUMENT_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<BizData xmlns="urn:iso:std:iso:20022:tech:xsd:head.003.001.01">
<Pyld>
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
<FinInstrm>
<ModfdRcrd>
<FinInstrmGnlAttrbts>
<Id>AT0000A2BJ35</Id>
<FullNm>Raiffeisen Centrobank AG TurboL O.End SAP</FullNm>
<ShrtNm>RCB/L CTF OE SAP</ShrtNm>
<ClssfctnTp>RFSTCB</ClssfctnTp>
<NtnlCcy>EUR</NtnlCcy>
<CmmdtyDerivInd>false</CmmdtyDerivInd>
</FinInstrmGnlAttrbts>
<Issr>529900M2F7D5795H1A49</Issr>
</ModfdRcrd>
</FinInstrm>
<FinInstrm>
<ModfdRcrd>
<FinInstrmGnlAttrbts>
<Id>AT0000A2BJ36</Id>
<ClssfctnTp>RFSTCB</ClssfctnTp>
<NtnlCcy>EUR</NtnlCcy>
<CmmdtyDerivInd>false</CmmdtyDerivInd>
</FinInstrmGnlAttrbts>
<Issr>529900M2F7D5795H1A49</Issr>
</ModfdRcrd>
</FinInstrm>
</FinInstrmRptgRefDataDltaRpt>
</Document>
</Pyld>
</BizData>"""


def _build_zip(files: dict[str, bytes]) -> bytes:
    """Build an in-memory zip archive containing the given files."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buffer.getvalue()


@responses.activate
def test_full_chain_registry_to_csv(tmp_path: Path) -> None:
    """Full pipeline: registry fetch -> select -> download -> extract ->
    parse -> transform -> CSV, using real classes throughout with only
    HTTP mocked."""
    zip_bytes = _build_zip({"instrument.xml": INSTRUMENT_XML})
    responses.add(responses.GET, REGISTRY_URL, body=REGISTRY_XML, status=200)
    responses.add(responses.GET, ZIP_URL, body=zip_bytes, status=200)

    destination = str(tmp_path / "output.csv")

    pipeline = Pipeline(
        downloader=Downloader(),
        registry_client=EsmaRegistryClient(Downloader()),
        extractor=ZipExtractor(),
        parser=InstrumentParser(),
        transformer=InstrumentTransformer(),
        storage_base=FsspecStorage(),
    )
    pipeline.run(
        registry_url=REGISTRY_URL,
        destination=destination,
    )

    written = pd.read_csv(destination)

    assert len(written) == 3

    # EGB OE TL.Z./SARTORIUS V — no lowercase 'a'
    assert written.loc[0, "FinInstrmGnlAttrbts.Id"] == "AT0000A2B3D9"
    assert written.loc[0, "FinInstrmGnlAttrbts.FullNm"] == "EGB OE TL.Z./SARTORIUS V"
    assert written.loc[0, "a_count"] == 0
    assert written.loc[0, "contains_a"] == "NO"

    # Raiffeisen Centrobank AG TurboL O.End SAP — 2 lowercase 'a'
    assert written.loc[1, "FinInstrmGnlAttrbts.Id"] == "AT0000A2BJ35"
    assert written.loc[1, "a_count"] == 2
    assert written.loc[1, "contains_a"] == "YES"

    # missing FullNm — a_count must be 0 per the brief
    assert written.loc[2, "FinInstrmGnlAttrbts.Id"] == "AT0000A2BJ36"
    assert pd.isna(written.loc[2, "FinInstrmGnlAttrbts.FullNm"])
    assert written.loc[2, "a_count"] == 0
    assert written.loc[2, "contains_a"] == "NO"
