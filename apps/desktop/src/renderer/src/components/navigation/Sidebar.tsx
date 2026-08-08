import { motion } from 'framer-motion';
import { agentTownAction, primaryNavigation } from '../../data/navigation';
import type { ViewId } from '../../types/navigation';

interface SidebarProps {
  activeView: ViewId;
  onNavigate: (view: ViewId) => void;
  onAgentTown: () => void;
}

export function Sidebar({ activeView, onNavigate, onAgentTown }: SidebarProps): JSX.Element {
  const AgentIcon = agentTownAction.icon;

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-cyan-300/10 bg-slate-950/55 p-5 backdrop-blur-2xl">
      <div className="rounded-3xl border border-cyan-300/20 bg-cyan-300/5 p-4 shadow-lg shadow-cyan-950/30">
        <p className="text-xs uppercase tracking-[0.45em] text-cyan-300">Shadow</p>
        <h1 className="mt-2 text-2xl font-semibold text-white">AI OS</h1>
      </div>
      <button type="button" onClick={onAgentTown} className="mt-5 flex items-center gap-3 rounded-2xl border border-cyan-300/25 bg-cyan-400/10 px-4 py-3 text-left text-cyan-100 shadow-lg shadow-cyan-950/30 transition hover:border-cyan-200/60 hover:bg-cyan-300/15">
        <AgentIcon className="h-5 w-5" />
        <span><span className="block text-sm font-semibold">Agent Town</span><span className="text-xs text-cyan-200/70">Open agent simulation</span></span>
      </button>
      <nav className="mt-6 space-y-2">
        {primaryNavigation.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;
          return (
            <button key={item.id} type="button" onClick={() => onNavigate(item.id)} className={`relative flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition ${isActive ? 'text-white' : 'text-slate-400 hover:bg-white/5 hover:text-cyan-100'}`}>
              {isActive && <motion.span layoutId="sidebar-active" className="absolute inset-0 rounded-2xl bg-cyan-300/10 ring-1 ring-cyan-300/25" />}
              <Icon className="relative h-5 w-5" />
              <span className="relative"><span className="block text-sm font-medium">{item.label}</span><span className="text-xs text-slate-500">{item.description}</span></span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
