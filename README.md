# Data Pipeline

A configurable data pipeline that downloads reference data from a remote 
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