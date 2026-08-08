import { contextBridge, ipcRenderer } from 'electron';

const shadowApi = { getVersion: (): Promise<string> => ipcRenderer.invoke('app:version') };

contextBridge.exposeInMainWorld('shadowAI', shadowApi);

export type ShadowDesktopApi = typeof shadowApi;
