import { Bell, Command, Search } from 'lucide-react';
import type { ViewId } from '../../types/navigation';

interface TopNavProps {
  activeView: ViewId;
}

export function TopNav({ activeView }: TopNavProps): JSX.Element {
  return (
    <header className="flex h-20 items-center justify-between border-b border-cyan-300/10 bg-slate-950/35 px-6 backdrop-blur-2xl">
      <div>
        <p className="text-xs uppercase tracking-[0.35em] text-cyan-300">Command Surface</p>
        <h2 className="mt-1 text-xl font-semibold capitalize text-white">{activeView}</h2>
      </div>
      <div className="flex items-center gap-3">
        <div className="hidden w-96 items-center gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-slate-400 lg:flex">
          <Search className="h-4 w-4 text-cyan-300" />
          <span className="text-sm">Search agents, memory, files, commands...</span>
          <Command className="ml-auto h-4 w-4" />
        </div>
        <button type="button" className="rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-300 transition hover:border-cyan-300/40 hover:text-cyan-200"><Bell className="h-5 w-5" /></button>
      </div>
    </header>
  );
}
