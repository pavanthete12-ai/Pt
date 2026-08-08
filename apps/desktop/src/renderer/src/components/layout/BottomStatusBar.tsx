import { Circle, Cpu, Database, Wifi } from 'lucide-react';

export function BottomStatusBar(): JSX.Element {
  return (
    <footer className="flex h-12 items-center justify-between border-t border-cyan-300/10 bg-slate-950/60 px-6 text-xs text-slate-400 backdrop-blur-2xl">
      <div className="flex items-center gap-5">
        <span className="flex items-center gap-2 text-emerald-300"><Circle className="h-2.5 w-2.5 fill-current" /> Online</span>
        <span className="flex items-center gap-2"><Cpu className="h-4 w-4 text-cyan-300" /> Local runtime idle</span>
        <span className="flex items-center gap-2"><Database className="h-4 w-4 text-blue-300" /> SQLite ready</span>
      </div>
      <span className="flex items-center gap-2"><Wifi className="h-4 w-4 text-cyan-300" /> No backend connection required</span>
    </footer>
  );
}
