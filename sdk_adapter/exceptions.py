"""SDK-specific exceptions."""


class SDKError(Exception):
    """Base SDK error."""


class CameraNotFoundError(SDKError):
    """No camera device available."""


class CameraBusyError(SDKError):
    """Camera is already in use."""


class StreamNotRunningError(SDKError):
    """Video stream is not active."""


class CaptureError(SDKError):
    """Failed to capture a frame."""


class RecordingError(SDKError):
    """Failed to record video."""


class RecordingAlreadyActiveError(RecordingError):
    """A recording session is already in progress."""


class RecordingNotActiveError(RecordingError):
    """No active recording session."""
