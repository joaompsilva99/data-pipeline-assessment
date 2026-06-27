class PipelineError(Exception):
    """Base class for all pipeline errors."""

    pass


class DownloadError(PipelineError):
    """Raised when a download operation fails."""

    pass
