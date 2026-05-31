import { IconCamera, IconPlay, IconRecord, IconStop } from '@/components/icons';
import type { RecordingStatus, StreamStatus } from '@/types/camera';

interface VideoControlPanelProps {
  streamStatus: StreamStatus;
  recordingStatus: RecordingStatus;
  recordingBusy?: boolean;
  onOpenStream: () => void;
  onCapture: () => void;
  onToggleRecording: () => void;
  onCloseStream: () => void;
}

export function VideoControlPanel({
  streamStatus,
  recordingStatus,
  recordingBusy = false,
  onOpenStream,
  onCapture,
  onToggleRecording,
  onCloseStream,
}: VideoControlPanelProps) {
  const isOnline = streamStatus === 'online';
  const isConnecting = streamStatus === 'connecting';
  const isOffline = streamStatus === 'offline';
  const isRecording = recordingStatus === 'recording';

  return (
    <aside className="side-panel side-panel--left" aria-label="视频与拍照控制">
      <h2 className="panel-heading">视频 &amp; 拍照</h2>

      <button
        type="button"
        className={`ctrl-btn ${isOffline ? 'ctrl-btn--primary' : ''}`}
        onClick={onOpenStream}
        disabled={!isOffline}
        aria-label="打开视频流"
      >
        <IconPlay />
        <span>{isConnecting ? '连接中…' : '打开视频流'}</span>
      </button>

      <button
        type="button"
        className="ctrl-btn"
        onClick={onCapture}
        disabled={!isOnline || isRecording}
        aria-label="拍照"
      >
        <IconCamera />
        <span>拍照</span>
        <span className="ctrl-btn__hint">Space</span>
      </button>

      <button
        type="button"
        className={`ctrl-btn ${isRecording ? 'ctrl-btn--recording' : ''}`}
        onClick={onToggleRecording}
        disabled={!isOnline || recordingBusy}
        aria-label={isRecording ? '停止录像' : '开始录像'}
        aria-pressed={isRecording}
      >
        <IconRecord />
        <span>{isRecording ? '停止录像' : '开始录像'}</span>
      </button>

      <button
        type="button"
        className="ctrl-btn"
        onClick={onCloseStream}
        disabled={isOffline || isConnecting}
        aria-label="关闭视频流"
      >
        <IconStop />
        <span>关闭视频流</span>
      </button>
    </aside>
  );
}
