import { Bot, Brain, FolderKanban, Zap } from 'lucide-react';
import { MetricCard } from '../components/cards/MetricCard';
import { MainChat } from '../components/chat/MainChat';
import { GlassPanel } from '../components/layout/GlassPanel';

export function Dashboard(): JSX.Element {
  return (
    <div className="grid gap-5 xl:grid-cols-[1fr_380px]">
      <div className="space-y-5">
        <div className="grid gap-4 md:grid-cols-4">
          <MetricCard label="Agents" value="12" detail="Ready for future runtime" icon={Bot} />
          <MetricCard label="Projects" value="04" detail="Workspace shells" icon={FolderKanban} tone="blue" />
          <MetricCard label="Memory" value="8.2k" detail="Indexed placeholders" icon={Brain} tone="violet" />
          <MetricCard label="Latency" value="12ms" detail="UI response budget" icon={Zap} tone="amber" />
        </div>
        <MainChat />
      </div>
      <GlassPanel className="min-h-[620px] p-5" resizable="horizontal">
        <h3 className="text-lg font-semibold text-white">Mission Control</h3>
        <div className="mt-5 space-y-4">
          {['Neural Link', 'Agent Queue', 'Memory Sync', 'Plugin Registry'].map((item, index) => (
            <div key={item} className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
              <div className="flex items-center justify-between"><span className="text-sm text-slate-300">{item}</span><span className="text-xs text-cyan-300">0{index + 1}</span></div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800"><div className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-blue-500" style={{ width: `${72 - index * 9}%` }} /></div>
            </div>
          ))}
        </div>
      </GlassPanel>
    </div>
  );
}
