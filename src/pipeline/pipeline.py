import logging
from collections.abc import Iterator
from pipeline.models.file_record import FileRecord
from pipeline.clients.downloader import Downloader
from pipeline.extractor import ZipExtractor
from pipeline.registry import EsmaRegistryClient
from pipeline.instrument_parser import InstrumentParser
from pipeline.instrument_transformer import InstrumentTransformer
from pipeline.storage.base_storage import StorageBase
from pipeline.exceptions import PipelineError

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        downloader: Downloader,
        registry_client: EsmaRegistryClient,
        extractor: ZipExtractor,
        parser: InstrumentParser,
        transformer: InstrumentTransformer,
        storage_base: StorageBase,
    ):
        """Initialize the pipeline's dependencies"""
        self._downloader = downloader
        self._registry_client = registry_client
        self._extractor = extractor
        self._parser = parser
        self._transformer = transformer
        self._storage_client = storage_base

    def run(
        self,
        registry_url: str,
        destination: str,
        file_type: str = "DLTINS",
        index: int = 1,
    ) -> None:
        """Runs the entire pipeline."""

        logger.info("Running pipeline")

        try:
            registry_xml = self._registry_client.download_registry(registry_url)

            records: Iterator[FileRecord] = self._registry_client.parse_xml(
                registry_xml
            )
            selected_record = self._registry_client.select_record(
                records, file_type, index
            )

            logger.info(f"Selected record: {selected_record.file_name}")

            zip_bytes = self._downloader.download(str(selected_record.download_link))

            archive, stream = self._extractor.open_xml_stream_from_zip(zip_bytes)

            try:
                instruments = self._parser.parse_xml(stream)
            finally:
                stream.close()
                archive.close()

            df = self._transformer.to_dataframe(instruments)
            self._storage_client.write_csv(df, destination)
        except PipelineError as e:
            logger.error(f"Pipeline run failed at step: {e}")
            raise

        logger.info("Pipeline run complete")
