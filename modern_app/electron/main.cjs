const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const { spawn } = require('node:child_process');
const readline = require('node:readline');
const fs = require('node:fs');

const isDev = !app.isPackaged;
let mainWindow = null;

function log(message) {
  try {
    const line = `[${new Date().toISOString()}] ${message}\n`;
    fs.appendFileSync(path.join(app.getPath('userData'), 'itchy-modern.log'), line, 'utf8');
  } catch {
    // Logging must never keep the app from opening.
  }
}

function rootPath() {
  return isDev ? path.resolve(__dirname, '..', '..') : path.resolve(process.resourcesPath);
}

function pythonExecutable() {
  if (process.platform === 'win32') return 'python';
  return 'python3';
}

function bundledWorkerExe() {
  return path.join(rootPath(), 'itchy-worker.exe');
}

function createWindow() {
  log(`createWindow start packaged=${app.isPackaged}`);
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 820,
    minWidth: 1100,
    minHeight: 720,
    title: 'ITCHY YouTube Downloader',
    icon: path.join(rootPath(), 'logo.ico'),
    backgroundColor: '#08111d',
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.on('closed', () => {
    log('window closed');
    mainWindow = null;
  });
  mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, validatedURL) => {
    log(`did-fail-load ${errorCode} ${errorDescription} ${validatedURL}`);
  });
  mainWindow.webContents.on('render-process-gone', (_event, details) => {
    log(`render-process-gone ${JSON.stringify(details)}`);
  });
  mainWindow.webContents.on('console-message', (_event, level, message) => {
    log(`renderer console ${level}: ${message}`);
  });
  mainWindow.webContents.on('did-finish-load', async () => {
    try {
      const text = await mainWindow.webContents.executeJavaScript('document.body.innerText.slice(0, 500)');
      log(`did-finish-load body="${String(text).replace(/\s+/g, ' ').slice(0, 300)}"`);
    } catch (error) {
      log(`did-finish-load inspect failed: ${error.message}`);
    }
  });

  if (isDev) {
    mainWindow.loadURL('http://127.0.0.1:5173');
  } else {
    const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
    log(`loadFile ${indexPath}`);
    mainWindow.loadFile(indexPath);
  }
}

app.whenReady().then(() => {
  log('app ready');
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('worker:run', async (event, command, payload) => {
  return new Promise((resolve, reject) => {
    const workerExe = bundledWorkerExe();
    const hasBundledWorker = fs.existsSync(workerExe);
    const worker = path.join(rootPath(), 'python_core', 'worker.py');
    const executable = hasBundledWorker ? workerExe : pythonExecutable();
    const args = hasBundledWorker
      ? [command, '--payload', JSON.stringify(payload || {})]
      : [worker, command, '--payload', JSON.stringify(payload || {})];
    const child = spawn(executable, args, {
      cwd: rootPath(),
      windowsHide: true,
    });

    let lastResult = null;
    let stderr = '';

    const rl = readline.createInterface({ input: child.stdout });
    rl.on('line', (line) => {
      if (!line.trim()) return;
      try {
        const message = JSON.parse(line);
        if (message.event === 'result' || message.event === 'done') {
          lastResult = message;
        }
        event.sender.send('worker:event', message);
      } catch {
        event.sender.send('worker:event', { event: 'log', message: line });
      }
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve(lastResult || { event: 'result' });
      } else {
        reject(new Error(stderr.trim() || `Worker exited with code ${code}`));
      }
    });
  });
});
