class PipelineError(Exception):
    """Base class for all pipeline errors."""

    pass


class DownloadError(PipelineError):
    """Raised when a download operation fails."""

    pass


class ParseError(PipelineError):
    """Raised when parsing of a file or response fails."""

    pass


class NoMatchingRecordError(PipelineError):
    """Raised when no matching record is found in the registry."""

    pass
