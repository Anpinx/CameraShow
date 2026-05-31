export type StreamStatus = 'offline' | 'connecting' | 'online';

export type RecordingStatus = 'idle' | 'recording';

export interface CameraInfo {
  ip: string;
  connected: boolean;
  resolution: string;
}

export interface CaptureItem {
  id: string;
  filename: string;
  thumbnailUrl: string;
  fullUrl: string;
  capturedAt: string;
}

export interface RecordItem {
  id: string;
  filename: string;
  thumbnailUrl: string;
  fullUrl: string;
  recordedAt: string;
}

export type MediaKind = 'image' | 'video';

export interface MediaItem {
  id: string;
  kind: MediaKind;
  filename: string;
  thumbnailUrl: string;
  fullUrl: string;
  createdAt: string;
}

export interface RecordStatus {
  status: RecordingStatus;
  filename?: string;
  startedAt?: string;
  frameCount?: number;
  filepath?: string;
}

export interface AppSettings {
  savePath: string;
  recordSavePath: string;
}

export interface AppState {
  streamStatus: StreamStatus;
  camera: CameraInfo;
  savePath: string;
  recordSavePath: string;
  recording: RecordStatus;
  recentItems: MediaItem[];
  selectedItemId: string | null;
  viewingFile: boolean;
  viewingFileKind: MediaKind | null;
  displayUrl: string | null;
}

export interface ElectronAPI {
  minimize: () => Promise<void>;
  maximize: () => Promise<void>;
  close: () => Promise<void>;
  selectDirectory: (defaultPath?: string) => Promise<string | null>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
