/// <reference types="vite/client" />
import type { ShadowDesktopApi } from '../../../preload/preload';

declare global { interface Window { shadowAI: ShadowDesktopApi; } }
