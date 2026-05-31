import { IconCamera } from '@/components/icons';
import type { CameraInfo, MediaKind, StreamStatus } from '@/types/camera';
import { streamStatusLabel } from '@/hooks/useCameraApp';

interface MediaDisplayProps {
  displayUrl: string | null;
  streamStatus: StreamStatus;
  camera: CameraInfo;
  viewingFile: boolean;
  viewingFileKind: MediaKind | null;
}

export function MediaDisplay({
  displayUrl,
  streamStatus,
  camera,
  viewingFile,
  viewingFileKind,
}: MediaDisplayProps) {
  const isOnline = streamStatus === 'online';
  const isConnecting = streamStatus === 'connecting';
  const isViewingVideo = viewingFile && viewingFileKind === 'video';

  const modeLabel = viewingFile
    ? viewingFileKind === 'video'
      ? '视频'
      : '图片'
    : '实时';

  return (
    <section className="media-area" aria-label="媒体画面展示">
      <div className="media-area__inner">
        {displayUrl ? (
          <>
            {isViewingVideo ? (
              <video
                key={displayUrl}
                className="media-area__content"
                src={displayUrl}
                controls
                autoPlay
                playsInline
                preload="auto"
              />
            ) : (
              <img
                className="media-area__content"
                src={displayUrl}
                alt={viewingFile ? '查看图片' : '实时视频流'}
              />
            )}
            {!isViewingVideo && <div className="media-scanline" aria-hidden />}
            {!isViewingVideo && <div className="media-vignette" aria-hidden />}
          </>
        ) : (
          <div className="media-area__placeholder" role="status">
            <IconCamera className="media-area__placeholder-icon" aria-hidden />
            <p className="media-area__placeholder-text">等待视频流连接</p>
            <p className="media-area__placeholder-sub">
              点击左侧「打开视频流」开始预览
            </p>
          </div>
        )}

        <div className="media-overlay" aria-live="polite">
          <span className="media-overlay__badge">
            <span
              className={`media-overlay__dot ${
                isOnline
                  ? ''
                  : isConnecting
                    ? 'media-overlay__dot--connecting'
                    : 'media-overlay__dot--offline'
              }`}
              aria-hidden
            />
            [{modeLabel}]
          </span>
          <span>状态：{streamStatusLabel(streamStatus)}</span>
          <span className="media-overlay__sep">|</span>
          <span>分辨率：{camera.resolution}</span>
          <span className="media-overlay__sep">|</span>
          <span>IP: {camera.ip}</span>
        </div>

        {viewingFile && viewingFileKind === 'image' && (
          <div className="media-mode-tag">IMAGE VIEW</div>
        )}
        {viewingFile && viewingFileKind === 'video' && (
          <div className="media-mode-tag">VIDEO VIEW</div>
        )}
        {isOnline && !viewingFile && <div className="media-mode-tag">LIVE</div>}
      </div>
    </section>
  );
}
