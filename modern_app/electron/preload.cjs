const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('itchy', {
  runWorker(command, payload, onEvent) {
    const listener = (_event, message) => {
      if (typeof onEvent === 'function') onEvent(message);
    };
    ipcRenderer.on('worker:event', listener);
    return ipcRenderer.invoke('worker:run', command, payload).finally(() => {
      ipcRenderer.removeListener('worker:event', listener);
    });
  },
});
