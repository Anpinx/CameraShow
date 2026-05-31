import type { CaptureItem, RecordItem, RecordStatus, StreamStatus } from '@/types/camera';
import { getWsBase } from '@/api/cameraApi';

export interface StreamStatusPayload {
  status: StreamStatus;
  streamUrl?: string;
}

export interface StatusSocketHandlers {
  onStreamStatus?: (data: StreamStatusPayload) => void;
  onCaptureCreated?: (item: CaptureItem) => void;
  onRecordCreated?: (item: RecordItem) => void;
  onCaptureSaved?: (data: { captureId: string; path: string }) => void;
  onSavePathUpdated?: (path: string) => void;
  onRecordSavePathUpdated?: (path: string) => void;
  onRecordStatus?: (data: RecordStatus) => void;
  onRecordStopped?: (data: { filename: string; filepath: string; frameCount: number }) => void;
  onConnectionChange?: (connected: boolean) => void;
}

interface StatusMessage {
  event: string;
  data: unknown;
}

const RECONNECT_MS = 3000;

export function connectStatusSocket(handlers: StatusSocketHandlers): () => void {
  let ws: WebSocket | null = null;
  let disposed = false;
  let reconnectTimer: number | undefined;

  const connect = () => {
    if (disposed) return;

    ws = new WebSocket(`${getWsBase()}/api/ws/status`);

    ws.onopen = () => {
      handlers.onConnectionChange?.(true);
    };

    ws.onmessage = (event) => {
      let message: StatusMessage;
      try {
        message = JSON.parse(String(event.data)) as StatusMessage;
      } catch {
        return;
      }

      switch (message.event) {
        case 'stream.status':
          handlers.onStreamStatus?.(message.data as StreamStatusPayload);
          break;
        case 'capture.created':
          handlers.onCaptureCreated?.(message.data as CaptureItem);
          break;
        case 'record.created':
          handlers.onRecordCreated?.(message.data as RecordItem);
          break;
        case 'capture.saved':
          handlers.onCaptureSaved?.(message.data as { captureId: string; path: string });
          break;
        case 'settings.save_path':
          handlers.onSavePathUpdated?.((message.data as { path: string }).path);
          break;
        case 'settings.record_save_path':
          handlers.onRecordSavePathUpdated?.((message.data as { path: string }).path);
          break;
        case 'record.status':
          handlers.onRecordStatus?.(message.data as RecordStatus);
          break;
        case 'record.stopped':
          handlers.onRecordStopped?.(
            message.data as { filename: string; filepath: string; frameCount: number },
          );
          break;
        default:
          break;
      }
    };

    ws.onclose = () => {
      handlers.onConnectionChange?.(false);
      if (!disposed) {
        reconnectTimer = window.setTimeout(connect, RECONNECT_MS);
      }
    };

    ws.onerror = () => {
      ws?.close();
    };
  };

  connect();

  return () => {
    disposed = true;
    if (reconnectTimer !== undefined) {
      window.clearTimeout(reconnectTimer);
    }
    ws?.close();
  };
}
