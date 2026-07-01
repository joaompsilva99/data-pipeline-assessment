import pandas as pd
import logging
from pathlib import Path
from pipeline.clients.downloader import Downloader
from pipeline.extractor import ZipExtractor
from pipeline.instrument_parser import InstrumentParser
from pipeline.instrument_transformer import InstrumentTransformer
from pipeline.pipeline import Pipeline
from pipeline.registry import EsmaRegistryClient
from pipeline.storage.fsspec_storage import FsspecStorage

logger = logging.getLogger(__name__)


def test_full_pipeline_real_data(tmp_path: Path) -> None:
    """Full pipeline against the real ESMA registry endpoint."""

    # Testing with local filesystem, but can be changed to other fsspec
    # compatible storage, s3 (s3://my-bucket/output.csv), azure (az://), etc
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
        registry_url=(
            "https://registers.esma.europa.eu/solr/esma_registers_firds_files/select"
            "?q=*&fq=publication_date:%5B2021-01-17T00:00:00Z+TO+2021-01-19T23:59:59Z%5D"
            "&wt=xml&indent=true&start=0&rows=100"
        ),
        destination=destination,
    )

    written = pd.read_csv(destination)

    logger.info(f"Total instruments: {len(written)}")
    logger.info(f"Instruments with lowercase 'a': {(written['a_count'] > 0).sum()}")
    logger.info(f"Missing FullNm: {written['FinInstrmGnlAttrbts.FullNm'].isna().sum()}")
    logger.info(f"Max a_count: {written['a_count'].max()}")

    assert len(written) > 0
    assert "FinInstrmGnlAttrbts.Id" in written.columns
    assert "a_count" in written.columns
    assert "contains_a" in written.columns

    # real Instrument example
    matching = written[written["FinInstrmGnlAttrbts.Id"] == "AT0000A2B3D9"]
    assert len(matching) > 0

    instrument = matching.iloc[0]
    logger.info(f"Known instrument AT0000A2B3D9: {instrument.to_dict()}")
    assert instrument["FinInstrmGnlAttrbts.FullNm"] == "EGB OE TL.Z./SARTORIUS V"
    assert instrument["a_count"] == 0  # no lowercase 'a' in "EGB OE TL.Z./SARTORIUS V"
    assert instrument["contains_a"] == "NO"
