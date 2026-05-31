"""Pydantic schemas aligned with frontend types."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CameraInfo(BaseModel):
    ip: str
    connected: bool
    resolution: str


class CaptureItem(BaseModel):
    id: str
    filename: str
    thumbnailUrl: str
    fullUrl: str
    capturedAt: str


class RecordItem(BaseModel):
    id: str
    filename: str
    thumbnailUrl: str
    fullUrl: str
    recordedAt: str


class StreamOpenResponse(BaseModel):
    streamUrl: str


class StreamStatusResponse(BaseModel):
    status: str
    streamUrl: str | None = None


class StreamCloseResponse(BaseModel):
    status: str


class SaveCaptureRequest(BaseModel):
    captureId: str
    path: str


class SaveRecordRequest(BaseModel):
    recordId: str
    path: str


class SavePathRequest(BaseModel):
    path: str


class PickDirectoryRequest(BaseModel):
    initialPath: str | None = None


class PickDirectoryResponse(BaseModel):
    path: str | None = None


class SettingsResponse(BaseModel):
    savePath: str
    recordSavePath: str


class RecordStatusResponse(BaseModel):
    status: str
    filename: str | None = None
    startedAt: str | None = None
    frameCount: int | None = None
    filepath: str | None = None


class RecordStopResponse(BaseModel):
    status: str
    filename: str
    filepath: str
    frameCount: int


class MessageResponse(BaseModel):
    message: str = Field(default="ok")
