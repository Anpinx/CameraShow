import { IconApp, IconClose, IconMaximize, IconMinimize } from '@/components/icons';

export function TitleBar() {
  const handleMinimize = () => window.electronAPI?.minimize();
  const handleMaximize = () => window.electronAPI?.maximize();
  const handleClose = () => window.electronAPI?.close();

  return (
    <header className="title-bar">
      <div className="title-bar__brand">
        <IconApp className="title-bar__icon" aria-hidden />
        <span className="title-bar__title">工业相机智能控制平台</span>
        <span className="title-bar__subtitle">Camera Intelligence Control</span>
      </div>
      <div className="title-bar__controls">
        <button
          type="button"
          className="title-bar__btn"
          aria-label="最小化"
          onClick={handleMinimize}
        >
          <IconMinimize />
        </button>
        <button
          type="button"
          className="title-bar__btn"
          aria-label="最大化"
          onClick={handleMaximize}
        >
          <IconMaximize />
        </button>
        <button
          type="button"
          className="title-bar__btn title-bar__btn--close"
          aria-label="关闭"
          onClick={handleClose}
        >
          <IconClose />
        </button>
      </div>
    </header>
  );
}
