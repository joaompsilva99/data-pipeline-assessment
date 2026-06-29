# Data Pipeline

A  data pipeline that downloads reference data from a remote 
registry, extracts and transforms structured records, and persists the 
result to cloud storage (S3/Azure-compatible via `fsspec`).

Built for a data engineering technical assessment.

## Requirements

- Python >=3.11
- [Poetry](https://python-poetry.org/) for dependency management

## Setup

```bash
poetry install
```

Install the git hooks (runs ruff and mypy automatically on every commit):

```bash
poetry run pre-commit install
```

Running tests:

```bash
poetry run pytest
```

Run linting and type checking manually:

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy src
```

## Project structure

```bash
src/pipeline/
├── clients/
│   └── downloader.py         # Generic HTTP client used for all downloads
├── models/
│   └── records.py            # FileRecord, Instrument (pydantic models)
├── registry.py               # EsmaRegistryClient: fetch/parse/select registry files
├── extractor.py              # ZipExtractor: locate and open the XML entry in a zip
├── instrument_parser.py      # InstrumentParser: parse instrument XML into records
├── instrument_transformer.py # InstrumentTransformer: build DataFrame and CSV
└── exceptions.py             # Shared exception hierarchy
tests/
├── unit/                     # One test module per class, fully isolated
└── integration/              # Multi-class chains, with only HTTP mocked
```

## Design notes and assumptions

### XML parsing strategy
- The registry response is small and explicitly paginated/bounded by the
  `rows` query parameter (100 in our request), so it's parsed with
  `ElementTree.fromstring()`. Selection (`select_record`) still consumes
  the parsed records lazily where possible, stopping once the target
  record is found.
- The instrument XML (inside the downloaded zip) can be significantly
  larger than the zip itself. `ZipExtractor` returns a stream into the 
  zip entry rather than its extracted bytes, so the decompressed content
  is never fully materialized in memory at once. This stream is parsed
  with `iterparse`, which decompresses and reads incrementally as
  needed, releasing each `<FinInstrm>` element (`elem.clear()`) once its
  fields have been extracted.

## Abstraction choices
`EsmaRegistryClient`, `ZipExtractor`, `InstrumentParser`, and
`InstrumentTransformer` are concrete classes with no abstract base,
since each currently has exactly one real implementation and no
second data source/format is anticipated.`Downloader` is kept generic
because its reused for two different downloads (registry XML, instrument zip).
The storage layer (not yet implemented) is the one place an abstraction
is planned, since the document explicitly requires both S3 and Azure support.