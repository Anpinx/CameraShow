import { IconFolder, IconSave } from '@/components/icons';
import type { MediaItem } from '@/types/camera';

interface FileViewPanelProps {
  recentItems: MediaItem[];
  selectedItemId: string | null;
  onSelectItem: (id: string) => void;
  onViewFile: () => void;
  onSaveFile: () => void;
}

export function FileViewPanel({
  recentItems,
  selectedItemId,
  onSelectItem,
  onViewFile,
  onSaveFile,
}: FileViewPanelProps) {
  const hasSelection = recentItems.some((item) => item.id === selectedItemId);
  const recentFiles = recentItems.slice(0, 3);

  return (
    <aside className="side-panel side-panel--right" aria-label="文件与查看控制">
      <h2 className="panel-heading">最近拍摄</h2>

      <div className="thumb-gallery" role="list">
        {recentFiles.length > 0 ? (
          recentFiles.map((item) => (
            <div
              key={item.id}
              role="listitem"
              className={`thumb-item ${selectedItemId === item.id ? 'thumb-item--selected' : ''}`}
              onClick={() => onSelectItem(item.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectItem(item.id);
                }
              }}
              tabIndex={0}
              aria-label={`选择 ${item.filename}`}
              aria-selected={selectedItemId === item.id}
            >
              <img src={item.thumbnailUrl} alt={item.filename} loading="lazy" />
              {item.kind === 'video' && <span className="thumb-item__badge">视频</span>}
              <span className="thumb-item__label">{item.filename}</span>
            </div>
          ))
        ) : (
          <div className="thumb-empty">暂无拍摄记录</div>
        )}
      </div>

      <h2 className="panel-heading">文件操作</h2>

      <button
        type="button"
        className="ctrl-btn"
        onClick={onViewFile}
        disabled={!hasSelection}
        aria-label="查看文件"
      >
        <IconFolder />
        <span>查看文件</span>
      </button>

      <button
        type="button"
        className="ctrl-btn"
        onClick={onSaveFile}
        disabled={!hasSelection}
        aria-label="保存文件"
      >
        <IconSave />
        <span>保存文件</span>
      </button>
    </aside>
  );
}
