import { IconBrowse, IconHelp, IconLog } from '@/components/icons';
import type { CameraInfo } from '@/types/camera';

interface InteractionBarProps {
  savePath: string;
  recordSavePath: string;
  camera: CameraInfo;
  onSelectPath: () => void;
  onSelectRecordPath: () => void;
}

export function InteractionBar({
  savePath,
  recordSavePath,
  camera,
  onSelectPath,
  onSelectRecordPath,
}: InteractionBarProps) {
  return (
    <footer className="interaction-bar" aria-label="系统交互与设置">
      <div className="interaction-bar__section">
        <h2 className="interaction-bar__heading">系统交互 &amp; 设置</h2>
        <div className="interaction-bar__paths">
          <div className="interaction-bar__path-group">
            <label className="status-row__label" htmlFor="save-path">
              图片保存路径
            </label>
            <div className="interaction-bar__path-row">
              <input
                id="save-path"
                className="path-input"
                type="text"
                readOnly
                value={savePath}
                aria-label="图片保存路径"
              />
              <button type="button" className="browse-btn" onClick={onSelectPath}>
                <IconBrowse aria-hidden />
                选择路径…
              </button>
            </div>
          </div>
          <div className="interaction-bar__path-group">
            <label className="status-row__label" htmlFor="record-save-path">
              录像保存路径
            </label>
            <div className="interaction-bar__path-row">
              <input
                id="record-save-path"
                className="path-input"
                type="text"
                readOnly
                value={recordSavePath}
                aria-label="录像保存路径"
              />
              <button type="button" className="browse-btn" onClick={onSelectRecordPath}>
                <IconBrowse aria-hidden />
                选择路径…
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="interaction-bar__center">
        <div className="status-led">
          <span
            className={`status-led__light ${camera.connected ? '' : 'status-led__light--off'}`}
            aria-hidden
          />
          <span>{camera.connected ? '相机已连接' : '相机未连接'}</span>
        </div>
        <div className="status-row">
          <span className="status-row__label">相机 IP</span>
          <span className="status-row__value">{camera.ip}</span>
        </div>
      </div>

      <div className="interaction-bar__extras">
        <button type="button" className="extra-link" aria-label="系统日志">
          <IconLog aria-hidden />
          系统日志
        </button>
        <button type="button" className="extra-link" aria-label="帮助">
          <IconHelp aria-hidden />
          帮助
        </button>
      </div>
    </footer>
  );
}
