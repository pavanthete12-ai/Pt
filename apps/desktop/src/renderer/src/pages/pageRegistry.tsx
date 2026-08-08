import { Files, FolderKanban, Globe2, Mic2, Settings, Sparkles } from 'lucide-react';
import type { ViewId } from '../types/navigation';
import { Dashboard } from './Dashboard';
import { GenericPage } from './GenericPage';

export function renderView(view: ViewId): JSX.Element {
  if (view === 'dashboard') return <Dashboard />;

  const pages = {
    projects: { title: 'Projects', eyebrow: 'Workspace Grid', description: 'Organize future missions, task boards, and agent workstreams from one modular project cockpit.', icon: FolderKanban, modules: ['Active Builds', 'Project Timeline', 'Task Matrix', 'Deployment Notes'] },
    memory: { title: 'Memory', eyebrow: 'Neural Archive', description: 'Visualize future long-term memory, embeddings, annotations, and knowledge graph operations.', icon: Sparkles, modules: ['Knowledge Graph', 'Recall Streams', 'Memory Policies', 'Embeddings Vault'] },
    browser: { title: 'Browser', eyebrow: 'Research Portal', description: 'Prepare a browser-style research surface for future web sessions, citations, captures, and summaries.', icon: Globe2, modules: ['Session Tabs', 'Source Cards', 'Capture Queue', 'Research Timeline'] },
    files: { title: 'Files', eyebrow: 'Local Vault', description: 'Browse future local assets, generated artifacts, transcripts, and plugin-owned storage zones.', icon: Files, modules: ['Vault Index', 'Recent Artifacts', 'Secure Imports', 'Export Queue'] },
    voice: { title: 'Voice', eyebrow: 'Audio Deck', description: 'Control future voice interactions, wake modes, transcription streams, and speech profiles.', icon: Mic2, modules: ['Input Monitor', 'Voice Profiles', 'Transcripts', 'Command History'] },
    settings: { title: 'Settings', eyebrow: 'Control Center', description: 'Configure future models, privacy, plugins, interface preferences, and desktop runtime behavior.', icon: Settings, modules: ['Appearance', 'Model Defaults', 'Privacy', 'Plugin Permissions'] }
  } satisfies Record<Exclude<ViewId, 'dashboard'>, Parameters<typeof GenericPage>[0]>;

  return <GenericPage {...pages[view]} />;
}
