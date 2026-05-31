import { useCallback, useEffect, useRef, useState } from 'react';
import {
  capturePhoto,
  closeStream,
  fetchCameraInfo,
  fetchCaptures,
  fetchRecords,
  fetchRecordStatus,
  fetchSettings,
  fetchStreamStatus,
  openStream,
  saveCapture,
  saveRecord,
  startRecording,
  stopRecording,
  updateRecordSavePath,
  updateSavePath,
  pickDirectoryViaApi,
} from '@/api/cameraApi';
import { connectStatusSocket } from '@/api/statusSocket';
import type {
  AppState,
  CaptureItem,
  MediaItem,
  RecordItem,
  RecordStatus,
  StreamStatus,
} from '@/types/camera';

const MAX_RECENT_ITEMS = 10;

const IDLE_RECORDING: RecordStatus = { status: 'idle' };

/** Trailing slash; forward slashes work on Windows, Linux, and macOS. */
function normalizePath(path: string): string {
  if (!path) return path;
  const normalized = path.replace(/\\/g, '/');
  return normalized.endsWith('/') ? normalized : `${normalized}/`;
}

async function pickDirectory(currentPath: string): Promise<string | null> {
  const initialPath = currentPath.replace(/[/\\]+$/, '');

  if (window.electronAPI?.selectDirectory) {
    try {
      return await window.electronAPI.selectDirectory(initialPath || undefined);
    } catch {
      // Fall through to backend picker below.
    }
  }

  const { path } = await pickDirectoryViaApi(initialPath);
  return path;
}

function captureToMediaItem(item: CaptureItem): MediaItem {
  return {
    id: item.id,
    kind: 'image',
    filename: item.filename,
    thumbnailUrl: item.thumbnailUrl,
    fullUrl: item.fullUrl,
    createdAt: item.capturedAt,
  };
}

function recordToMediaItem(item: RecordItem): MediaItem {
  return {
    id: item.id,
    kind: 'video',
    filename: item.filename,
    thumbnailUrl: item.thumbnailUrl,
    fullUrl: item.fullUrl,
    createdAt: item.recordedAt,
  };
}

function mergeRecentItems(existing: MediaItem[], incoming: MediaItem): MediaItem[] {
  const filtered = existing.filter((item) => item.id !== incoming.id);
  return [incoming, ...filtered]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, MAX_RECENT_ITEMS);
}

function buildRecentItems(captures: CaptureItem[], records: RecordItem[]): MediaItem[] {
  const items = [
    ...captures.map(captureToMediaItem),
    ...records.map(recordToMediaItem),
  ];
  return items
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, MAX_RECENT_ITEMS);
}

export function useCameraApp() {
  const [state, setState] = useState<AppState>({
    streamStatus: 'offline',
    camera: { ip: '—', connected: false, resolution: '1080p' },
    savePath: '',
    recordSavePath: '',
    recording: IDLE_RECORDING,
    recentItems: [],
    selectedItemId: null,
    viewingFile: false,
    viewingFileKind: null,
    displayUrl: null,
  });
  const [toast, setToast] = useState<string | null>(null);
  const [recordingBusy, setRecordingBusy] = useState(false);
  const liveStreamUrlRef = useRef<string | null>(null);
  const viewingFileRef = useRef(false);
  const recordingBusyRef = useRef(false);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast(null), 2800);
  }, []);

  const restoreLiveView = useCallback(() => {
    viewingFileRef.current = false;
    setState((s) => {
      if (s.streamStatus !== 'online' || !liveStreamUrlRef.current) {
        return {
          ...s,
          viewingFile: false,
          viewingFileKind: null,
        };
      }
      return {
        ...s,
        viewingFile: false,
        viewingFileKind: null,
        displayUrl: liveStreamUrlRef.current,
      };
    });
  }, []);

  const mergeMediaItem = useCallback((item: MediaItem) => {
    setState((s) => {
      const recentItems = mergeRecentItems(s.recentItems, item);
      return {
        ...s,
        recentItems,
        selectedItemId: item.id,
      };
    });
  }, []);

  useEffect(() => {
    viewingFileRef.current = state.viewingFile;
  }, [state.viewingFile]);

  useEffect(() => {
    let cancelled = false;

    const bootstrap = async () => {
      try {
        const [camera, captures, records, stream, settings, recordStatus] = await Promise.all([
          fetchCameraInfo(),
          fetchCaptures(),
          fetchRecords(),
          fetchStreamStatus(),
          fetchSettings(),
          fetchRecordStatus(),
        ]);
        if (cancelled) return;

        const recentItems = buildRecentItems(captures, records);

        if (stream.streamUrl) {
          liveStreamUrlRef.current = stream.streamUrl;
        }

        setState((s) => ({
          ...s,
          camera,
          recentItems,
          selectedItemId: recentItems[0]?.id ?? null,
          streamStatus: stream.status,
          savePath: normalizePath(settings.savePath),
          recordSavePath: normalizePath(settings.recordSavePath),
          recording: recordStatus,
          displayUrl:
            stream.status === 'online' && stream.streamUrl ? stream.streamUrl : null,
        }));
      } catch (error) {
        if (!cancelled) {
          showToast(error instanceof Error ? error.message : '后端连接失败');
        }
      }
    };

    void bootstrap();

    const disconnectSocket = connectStatusSocket({
      onStreamStatus: ({ status, streamUrl }) => {
        if (streamUrl) {
          liveStreamUrlRef.current = streamUrl;
        }
        if (status !== 'online') {
          liveStreamUrlRef.current = null;
        }

        setState((s) => {
          const viewingFile = viewingFileRef.current;
          if (viewingFile && status === 'online') {
            return {
              ...s,
              streamStatus: status,
              recording: status === 'online' ? s.recording : IDLE_RECORDING,
            };
          }
          return {
            ...s,
            streamStatus: status,
            displayUrl: status === 'online' ? liveStreamUrlRef.current : null,
            viewingFile: status === 'online' ? viewingFile : false,
            viewingFileKind: status === 'online' ? s.viewingFileKind : null,
            recording: status === 'online' ? s.recording : IDLE_RECORDING,
          };
        });
      },
      onCaptureCreated: (item) => {
        mergeMediaItem(captureToMediaItem(item));
      },
      onRecordCreated: (item) => {
        mergeMediaItem(recordToMediaItem(item));
      },
      onCaptureSaved: ({ captureId }) => {
        setState((s) => ({
          ...s,
          selectedItemId: s.selectedItemId ?? captureId,
        }));
      },
      onSavePathUpdated: (path) => {
        setState((s) => ({ ...s, savePath: normalizePath(path) }));
      },
      onRecordSavePathUpdated: (path) => {
        setState((s) => ({ ...s, recordSavePath: normalizePath(path) }));
      },
      onRecordStatus: (recording) => {
        setState((s) => ({ ...s, recording }));
      },
      onRecordStopped: () => {
        setState((s) => ({ ...s, recording: IDLE_RECORDING }));
      },
    });

    return () => {
      cancelled = true;
      disconnectSocket();
    };
  }, [mergeMediaItem, showToast]);

  const openVideoStream = useCallback(async () => {
    setState((s) => ({
      ...s,
      streamStatus: 'connecting',
      viewingFile: false,
      viewingFileKind: null,
      displayUrl: null,
    }));
    try {
      const { streamUrl } = await openStream();
      liveStreamUrlRef.current = streamUrl;
      setState((s) => ({
        ...s,
        streamStatus: 'online',
        displayUrl: streamUrl,
        viewingFile: false,
        viewingFileKind: null,
        camera: { ...s.camera, connected: true },
      }));
      showToast('视频流已连接');
    } catch (error) {
      liveStreamUrlRef.current = null;
      setState((s) => ({
        ...s,
        streamStatus: 'offline',
        displayUrl: null,
      }));
      showToast(error instanceof Error ? error.message : '打开视频流失败');
    }
  }, [showToast]);

  const closeVideoStream = useCallback(async () => {
    try {
      await closeStream();
      liveStreamUrlRef.current = null;
      setState((s) => ({
        ...s,
        streamStatus: 'offline',
        displayUrl: null,
        viewingFile: false,
        viewingFileKind: null,
        recording: IDLE_RECORDING,
        camera: { ...s.camera, connected: false },
      }));
      showToast('视频流已关闭');
    } catch (error) {
      showToast(error instanceof Error ? error.message : '关闭视频流失败');
    }
  }, [showToast]);

  const takePhoto = useCallback(async () => {
    if (state.streamStatus !== 'online' || state.recording.status === 'recording') return;
    restoreLiveView();
    try {
      const item = await capturePhoto();
      mergeMediaItem(captureToMediaItem(item));
      showToast('拍照成功');
    } catch (error) {
      showToast(error instanceof Error ? error.message : '拍照失败');
    }
  }, [
    mergeMediaItem,
    restoreLiveView,
    showToast,
    state.recording.status,
    state.streamStatus,
  ]);

  const syncRecordingFromServer = useCallback(async () => {
    try {
      const recording = await fetchRecordStatus();
      setState((s) => ({ ...s, recording }));
      return recording;
    } catch {
      return null;
    }
  }, []);

  const toggleRecording = useCallback(async () => {
    if (state.streamStatus !== 'online' || recordingBusyRef.current) return;

    restoreLiveView();

    if (state.recording.status === 'recording') {
      recordingBusyRef.current = true;
      setRecordingBusy(true);
      try {
        const result = await stopRecording();
        setState((s) => ({ ...s, recording: IDLE_RECORDING }));
        showToast(`录像已保存: ${result.filepath}`);
      } catch (error) {
        const recording = await syncRecordingFromServer();
        if (recording?.status === 'idle') {
          return;
        }
        showToast(error instanceof Error ? error.message : '停止录像失败');
      } finally {
        recordingBusyRef.current = false;
        setRecordingBusy(false);
      }
      return;
    }

    recordingBusyRef.current = true;
    setRecordingBusy(true);
    try {
      const recording = await startRecording();
      setState((s) => ({ ...s, recording }));
      showToast('开始录像');
    } catch (error) {
      showToast(error instanceof Error ? error.message : '开始录像失败');
    } finally {
      recordingBusyRef.current = false;
      setRecordingBusy(false);
    }
  }, [restoreLiveView, showToast, state.recording.status, state.streamStatus, syncRecordingFromServer]);

  const viewSelectedFile = useCallback(() => {
    const item = state.recentItems.find((entry) => entry.id === state.selectedItemId);
    if (!item) return;
    setState((s) => ({
      ...s,
      viewingFile: true,
      viewingFileKind: item.kind,
      displayUrl: item.fullUrl,
    }));
  }, [state.recentItems, state.selectedItemId]);

  const saveSelectedFile = useCallback(async () => {
    const item = state.recentItems.find((entry) => entry.id === state.selectedItemId);
    if (!item) return;
    try {
      if (item.kind === 'image') {
        await saveCapture(item.id, state.savePath);
        showToast(`已保存至 ${state.savePath}${item.filename}`);
        return;
      }
      await saveRecord(item.id, state.recordSavePath);
      showToast(`已保存至 ${state.recordSavePath}${item.filename}`);
    } catch (error) {
      showToast(error instanceof Error ? error.message : '保存失败');
    }
  }, [state.recentItems, state.recordSavePath, state.savePath, state.selectedItemId, showToast]);

  const selectItem = useCallback((id: string) => {
    setState((s) => ({ ...s, selectedItemId: id }));
  }, []);

  const selectSavePath = useCallback(async () => {
    try {
      const path = await pickDirectory(state.savePath);
      if (!path) return;

      const normalized = normalizePath(path);
      await updateSavePath(normalized);
      setState((s) => ({ ...s, savePath: normalized }));
      showToast('图片保存路径已更新');
    } catch (error) {
      showToast(error instanceof Error ? error.message : '无法打开目录选择器');
    }
  }, [state.savePath, showToast]);

  const selectRecordSavePath = useCallback(async () => {
    try {
      const path = await pickDirectory(state.recordSavePath);
      if (!path) return;

      const normalized = normalizePath(path);
      await updateRecordSavePath(normalized);
      setState((s) => ({ ...s, recordSavePath: normalized }));
      showToast('录像保存路径已更新');
    } catch (error) {
      showToast(error instanceof Error ? error.message : '无法打开目录选择器');
    }
  }, [state.recordSavePath, showToast]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (
        e.code === 'Space' &&
        state.streamStatus === 'online' &&
        state.recording.status !== 'recording'
      ) {
        e.preventDefault();
        void takePhoto();
      }
      if (e.key === 'Escape' && state.viewingFile) {
        setState((s) => ({
          ...s,
          viewingFile: false,
          viewingFileKind: null,
          displayUrl: s.streamStatus === 'online' ? liveStreamUrlRef.current : null,
        }));
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [state.streamStatus, state.recording.status, takePhoto]);

  return {
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
  };
}

export function streamStatusLabel(status: StreamStatus): string {
  switch (status) {
    case 'online':
      return '在线';
    case 'connecting':
      return '连接中';
    default:
      return '离线';
  }
}
