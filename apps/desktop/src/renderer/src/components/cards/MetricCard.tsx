import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  icon: LucideIcon;
  tone?: 'cyan' | 'blue' | 'violet' | 'amber';
}

const tones = {
  cyan: 'from-cyan-400/20 to-cyan-400/5 text-cyan-200',
  blue: 'from-blue-500/20 to-blue-500/5 text-blue-200',
  violet: 'from-violet-500/20 to-violet-500/5 text-violet-200',
  amber: 'from-amber-400/20 to-amber-400/5 text-amber-200'
};

export function MetricCard({ label, value, detail, icon: Icon, tone = 'cyan' }: MetricCardProps): JSX.Element {
  return (
    <motion.article whileHover={{ y: -4, scale: 1.01 }} transition={{ type: 'spring', stiffness: 260, damping: 22 }} className={`rounded-2xl border border-white/10 bg-gradient-to-br ${tones[tone]} p-5 shadow-xl shadow-cyan-950/20`}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-[0.28em] text-slate-400">{label}</span>
        <Icon className="h-5 w-5" />
      </div>
      <strong className="mt-5 block text-3xl font-semibold text-white">{value}</strong>
      <p className="mt-2 text-sm text-slate-400">{detail}</p>
    </motion.article>
  );
}
