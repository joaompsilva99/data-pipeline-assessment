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

Run the real data integration test (requires internet access):

```bash
poetry run pytest tests/integration/integration_test_real.py -v -s --log-cli-level=DEBUG
```

Run the sample data integration test:
```bash
poetry run pytest tests/integration/integration_test.py -v -s --log-cli-level=DEBUG
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
│   └── downloader.py              # Generic HTTP client used for all downloads
├── models/
│   └── records.py                 # FileRecord, Instrument (pydantic models)
├── storage/
│   ├── base.py                    # StorageClient ABC
│   └── fsspec_storage.py          # FsspecStorageClient: writes to any fsspec backend
├── registry.py                    # EsmaRegistryClient: fetch/parse/select registry files
├── extractor.py                   # ZipExtractor: locate and open the XML entry in a zip
├── instrument_parser.py           # InstrumentParser: parse instrument XML into records
├── instrument_transformer.py      # InstrumentTransformer: build DataFrame and CSV
├── exceptions.py                  # Shared exception hierarchy
└── pipeline.py                    # Pipeline: orchestrates all components
tests/
├── unit/                          # One test module per class, fully isolated
├── integration/                   # Multi-class chains, with only HTTP mocked
│   ├── integration_test.py        # Full pipeline with mocked HTTP, file samples
│   └── integration_test_real.py   # Full pipeline using the real data
```

## Current status:
All requirements implemented and tested:

- Fetching and parsing the ESMA registry response, selecting the second
  DLTINS file
- Downloading and locating the XML entry within the resulting zip archive
- Parsing the instrument XML into structured `Instrument` records
- Transforming parsed instruments into the required CSV format, including
  the `a_count` and `contains_a` derived columns
- Writing the result to fsspec compatible destinations 

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

### Abstraction choices
`EsmaRegistryClient`, `ZipExtractor`, `InstrumentParser`, and
`InstrumentTransformer` are concrete classes with no abstract base,
since each currently has exactly one real implementation and no
second data source/format is anticipated.`Downloader` is kept generic
because its reused for two different downloads (registry XML, instrument zip).
For the storage specific classes abstraction was implemented.

### Memory:
- The zip is held in memory in full, due to its size.
- The decompressed XML is never materialized in memory at once (iterparse)
- The parsed `Instrument` objects are collected into a complete list, since
  `InstrumentTransformer` requires the full dataset to build one DataFrame.
  This is the point where data is fully materialized in memory, this can be
  improved in the future.
- `df.to_csv(destination)` (in storage phase) streams directly from
  the DataFrame into the fsspec destination, without materializing
  the full CSV text as an intermediate string, here we avoid an extra
  in memory copy.

### Future improvements:
- Instead of holding every instrument at once to build the dataframe, we
  we could explore accumulating batches of instruments, build a smaller
  dataframe per batch and upload each batch incrementally. In order for
  the upload result to be a single CSV file, the storage would need to
  support this kind of appending per chunk, taking into account the 
  current uploading strategy.


### Storage design
The `write_csv` methodl, implemented by the `FsspecStorage` class,
calls `df.to_csv(destination)` directly, letting pandas invoke fsspec
internally. This approach streams rows incrementally into the destination
without materializing the full CSV string in memory first.

`FsspecStorage` satisfies multiple types of filesystems via a
single implementation, since fsspec resolves the backend automatically
 from the URI scheme (`s3://`, `az://`, local path, etc.)

During design I thought of making StorageBase method more generic, so that
the write method was agnostic to the technology (pandas) and file_type. 
With the declaration of the method looking like the following:
  - `write(destination, write_fn: Callable[[IO[str]], None])`
This would also separate specific transformation technology and file
handling from the storage layer's responsibilities. However, due to it
making the code more complex and the single current requirement, I opted
for the simpler `write_csv(df, destination)` approach.

### S3 testing limitation

S3 mocking is not included in the automated test suite due to an
incompatibility between s3fs (which uses async aiobotocore internally)
and available mocking libraries in this environment, such as moto.

Storage integration is verified via a local filesystem path in the automated
integration test. However, the implementation would be the same only the 
uri would need to be changed (s3:// (aws), az:// (azure), etc).