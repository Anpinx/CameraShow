import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import fs from 'fs';
import path from 'path';

const isDev = !app.isPackaged;

function createWindow() {
  const win = new BrowserWindow({
    width: 1280,
    height: 720,
    minWidth: 960,
    minHeight: 540,
    frame: false,
    backgroundColor: '#0a0e14',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    win.loadURL('http://localhost:5173');
    win.webContents.openDevTools({ mode: 'detach' });
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('window:minimize', (e) => {
  BrowserWindow.fromWebContents(e.sender)?.minimize();
});

ipcMain.handle('window:maximize', (e) => {
  const win = BrowserWindow.fromWebContents(e.sender);
  if (!win) return;
  if (win.isMaximized()) win.unmaximize();
  else win.maximize();
});

ipcMain.handle('window:close', (e) => {
  BrowserWindow.fromWebContents(e.sender)?.close();
});

function resolveDialogDefaultPath(raw?: string): string | undefined {
  if (!raw?.trim()) return undefined;

  const normalized = path.normalize(raw.trim().replace(/[/\\]+$/, ''));
  if (!normalized) return undefined;

  try {
    if (!fs.existsSync(normalized)) return undefined;
    const stat = fs.statSync(normalized);
    return stat.isDirectory() ? normalized : undefined;
  } catch {
    return undefined;
  }
}

ipcMain.handle('dialog:selectDirectory', async (e, defaultPath?: string) => {
  const win = BrowserWindow.fromWebContents(e.sender);
  if (!win) return null;

  win.show();
  win.focus();

  const resolvedDefaultPath = resolveDialogDefaultPath(defaultPath);
  const result = await dialog.showOpenDialog(win, {
    title: '选择文件夹',
    properties: ['openDirectory', 'createDirectory'],
    ...(resolvedDefaultPath ? { defaultPath: resolvedDefaultPath } : {}),
  });
  return result.canceled ? null : result.filePaths[0] ?? null;
});
