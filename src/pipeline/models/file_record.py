from pydantic import BaseModel, HttpUrl, ConfigDict


class FileRecord(BaseModel):
    """Represents a single record of a file."""

    # makes FileRecord immutable, can not change attributes after creation
    model_config = ConfigDict(frozen=True)

    id: str
    file_name: str
    file_type: str
    download_link: HttpUrl
