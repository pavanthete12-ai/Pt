import { Bot, Files, FolderKanban, Globe2, LayoutDashboard, Mic2, Settings, Sparkles } from 'lucide-react';
import type { NavigationItem } from '../types/navigation';

export const primaryNavigation: NavigationItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, description: 'System overview' },
  { id: 'projects', label: 'Projects', icon: FolderKanban, description: 'Workspace operations' },
  { id: 'memory', label: 'Memory', icon: Sparkles, description: 'Knowledge graph' },
  { id: 'browser', label: 'Browser', icon: Globe2, description: 'Research surface' },
  { id: 'files', label: 'Files', icon: Files, description: 'Local vault' },
  { id: 'voice', label: 'Voice', icon: Mic2, description: 'Audio command deck' },
  { id: 'settings', label: 'Settings', icon: Settings, description: 'Control center' }
];

export const agentTownAction = { label: 'Agent Town', icon: Bot };
