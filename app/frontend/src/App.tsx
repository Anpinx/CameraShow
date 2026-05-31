import { TitleBar } from '@/components/TitleBar/TitleBar';
import { VideoControlPanel } from '@/components/VideoControlPanel/VideoControlPanel';
import { MediaDisplay } from '@/components/MediaDisplay/MediaDisplay';
import { FileViewPanel } from '@/components/FileViewPanel/FileViewPanel';
import { InteractionBar } from '@/components/InteractionBar/InteractionBar';
import { useCameraApp } from '@/hooks/useCameraApp';
import { useViewportScale } from '@/hooks/useViewportScale';

export default function App() {
  const canvasRef = useViewportScale();
  const {
    state,
    toast,
    recordingBusy,
    openVideoStream,
    closeVideoStream,
    takePhoto,
    toggleRecording,
    viewSelectedFile,
    saveSelectedFile,
    selectItem,
    selectSavePath,
    selectRecordSavePath,
  } = useCameraApp();

  return (
    <div className="app-viewport">
      <div className="app-canvas" ref={canvasRef}>
        <TitleBar />

        <div className="main-layout">
          <VideoControlPanel
            streamStatus={state.streamStatus}
            recordingStatus={state.recording.status}
            recordingBusy={recordingBusy}
            onOpenStream={openVideoStream}
            onCapture={takePhoto}
            onToggleRecording={toggleRecording}
            onCloseStream={closeVideoStream}
          />

          <MediaDisplay
            displayUrl={state.displayUrl}
            streamStatus={state.streamStatus}
            camera={state.camera}
            viewingFile={state.viewingFile}
            viewingFileKind={state.viewingFileKind}
          />

          <FileViewPanel
            recentItems={state.recentItems}
            selectedItemId={state.selectedItemId}
            onSelectItem={selectItem}
            onViewFile={viewSelectedFile}
            onSaveFile={saveSelectedFile}
          />
        </div>

        <InteractionBar
          savePath={state.savePath}
          recordSavePath={state.recordSavePath}
          camera={state.camera}
          onSelectPath={selectSavePath}
          onSelectRecordPath={selectRecordSavePath}
        />
      </div>

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  );
}
