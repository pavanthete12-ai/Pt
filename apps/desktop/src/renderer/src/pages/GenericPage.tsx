import type { LucideIcon } from 'lucide-react';
import { motion } from 'framer-motion';
import { GlassPanel } from '../components/layout/GlassPanel';

interface GenericPageProps {
  title: string;
  eyebrow: string;
  description: string;
  icon: LucideIcon;
  modules: string[];
}

export function GenericPage({ title, eyebrow, description, icon: Icon, modules }: GenericPageProps): JSX.Element {
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
      <GlassPanel className="min-h-[620px] p-8" resizable="both">
        <div className="flex items-center gap-4"><div className="rounded-2xl border border-cyan-300/20 bg-cyan-300/10 p-4 text-cyan-200"><Icon className="h-7 w-7" /></div><div><p className="text-xs uppercase tracking-[0.35em] text-cyan-300">{eyebrow}</p><h2 className="mt-2 text-4xl font-semibold text-white">{title}</h2></div></div>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-400">{description}</p>
        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {modules.map((module, index) => (
            <motion.div key={module} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.06 }} whileHover={{ y: -3 }} className="rounded-2xl border border-white/10 bg-white/[0.04] p-5">
              <span className="text-xs uppercase tracking-[0.3em] text-slate-500">Module {index + 1}</span>
              <h3 className="mt-3 text-lg font-semibold text-white">{module}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-500">Reserved frontend surface for production feature implementation.</p>
            </motion.div>
          ))}
        </div>
      </GlassPanel>
      <GlassPanel className="p-5">
        <h3 className="text-lg font-semibold text-white">Panel Controls</h3>
        <p className="mt-2 text-sm text-slate-500">This glass panel is modular and ready to connect to future state, agent, and plugin services.</p>
        <div className="mt-6 space-y-3">{['Resizable layout', 'Animated cards', 'Neon states'].map((label) => <div key={label} className="rounded-xl border border-cyan-300/10 bg-cyan-300/5 px-4 py-3 text-sm text-cyan-100">{label}</div>)}</div>
      </GlassPanel>
    </div>
  );
}
