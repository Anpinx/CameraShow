/**
 * 后端 API — 对接 Python FastAPI 服务
 * Base URL 可通过环境变量 VITE_API_BASE 配置
 */

import type {
  AppSettings,
  CameraInfo,
  CaptureItem,
  RecordItem,
  RecordingStatus,
  RecordStatus,
  StreamStatus,
} from '@/types/camera';

const DEFAULT_API_BASE = 'http://127.0.0.1:8000';

export function getApiBase(): string {
  return import.meta.env.VITE_API_BASE ?? DEFAULT_API_BASE;
}

export function getWsBase(): string {
  return getApiBase().replace(/^http/i, 'ws');
}

async function parseError(res: Response, path: string): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: unknown };
    const { detail } = body;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first.msg) return first.msg;
    }
  } catch {
    // ignore parse errors
  }
  return `API ${path} failed: ${res.status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiBase()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    throw new Error(await parseError(res, path));
  }
  return res.json() as Promise<T>;
}

/** GET /api/camera/info */
export function fetchCameraInfo(): Promise<CameraInfo> {
  return request<CameraInfo>('/api/camera/info');
}

/** POST /api/stream/open */
export function openStream(): Promise<{ streamUrl: string }> {
  return request('/api/stream/open', { method: 'POST' });
}

/** POST /api/stream/close */
export function closeStream(): Promise<{ status: StreamStatus }> {
  return request('/api/stream/close', { method: 'POST' });
}

/** POST /api/capture */
export function capturePhoto(): Promise<CaptureItem> {
  return request('/api/capture', { method: 'POST' });
}

/** GET /api/captures */
export function fetchCaptures(): Promise<CaptureItem[]> {
  return request<CaptureItem[]>('/api/captures');
}

/** GET /api/records */
export function fetchRecords(): Promise<RecordItem[]> {
  return request<RecordItem[]>('/api/records');
}

/** POST /api/captures/save */
export function saveCapture(captureId: string, path: string): Promise<{ message: string }> {
  return request('/api/captures/save', {
    method: 'POST',
    body: JSON.stringify({ captureId, path }),
  });
}

/** POST /api/records/save */
export function saveRecord(recordId: string, path: string): Promise<{ message: string }> {
  return request('/api/records/save', {
    method: 'POST',
    body: JSON.stringify({ recordId, path }),
  });
}

/** POST /api/settings/pick-directory — native folder picker fallback */
export function pickDirectoryViaApi(
  initialPath?: string,
): Promise<{ path: string | null }> {
  return request('/api/settings/pick-directory', {
    method: 'POST',
    body: JSON.stringify({ initialPath: initialPath ?? '' }),
  });
}

/** PUT /api/settings/save-path */
export function updateSavePath(path: string): Promise<{ message: string }> {
  return request('/api/settings/save-path', {
    method: 'PUT',
    body: JSON.stringify({ path }),
  });
}

/** GET /api/stream/status */
export function fetchStreamStatus(): Promise<{ status: StreamStatus; streamUrl?: string }> {
  return request('/api/stream/status');
}

/** GET /api/settings */
export function fetchSettings(): Promise<AppSettings> {
  return request<AppSettings>('/api/settings');
}

/** PUT /api/settings/record-save-path */
export function updateRecordSavePath(path: string): Promise<{ message: string }> {
  return request('/api/settings/record-save-path', {
    method: 'PUT',
    body: JSON.stringify({ path }),
  });
}

/** POST /api/record/start */
export function startRecording(): Promise<RecordStatus> {
  return request<RecordStatus>('/api/record/start', { method: 'POST' });
}

/** POST /api/record/stop */
export function stopRecording(): Promise<{
  status: RecordingStatus;
  filename: string;
  filepath: string;
  frameCount: number;
}> {
  return request('/api/record/stop', { method: 'POST' });
}

/** GET /api/record/status */
export function fetchRecordStatus(): Promise<RecordStatus> {
  return request<RecordStatus>('/api/record/status');
}
