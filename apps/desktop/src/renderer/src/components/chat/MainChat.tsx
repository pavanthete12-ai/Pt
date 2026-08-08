import { motion } from 'framer-motion';
import { Paperclip, Send, Sparkles } from 'lucide-react';
import { GlassPanel } from '../layout/GlassPanel';

const messages = [
  { role: 'system', body: 'Shadow AI desktop shell initialized. No backend features are active yet.' },
  { role: 'user', body: 'Prepare the command surface for agent orchestration.' },
  { role: 'assistant', body: 'Interface modules are ready: dashboard, projects, memory, browser, files, voice, and settings.' }
];

export function MainChat(): JSX.Element {
  return (
    <GlassPanel className="flex min-h-[440px] flex-col" resizable="vertical">
      <div className="flex items-center justify-between border-b border-white/10 p-5">
        <div className="flex items-center gap-3"><Sparkles className="h-5 w-5 text-cyan-300" /><div><h3 className="font-semibold text-white">Main Chat</h3><p className="text-xs text-slate-500">Frontend-only command console</p></div></div>
      </div>
      <div className="flex-1 space-y-4 overflow-auto p-5">
        {messages.map((message, index) => (
          <motion.div key={`${message.role}-${index}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }} className={`max-w-[82%] rounded-2xl border p-4 text-sm leading-6 ${message.role === 'user' ? 'ml-auto border-cyan-300/20 bg-cyan-300/10 text-cyan-50' : 'border-white/10 bg-white/5 text-slate-300'}`}>
            {message.body}
          </motion.div>
        ))}
      </div>
      <div className="border-t border-white/10 p-4"><div className="flex items-center gap-3 rounded-2xl border border-cyan-300/15 bg-slate-900/70 px-4 py-3"><Paperclip className="h-4 w-4 text-slate-500" /><input className="flex-1 bg-transparent text-sm text-white outline-none placeholder:text-slate-600" placeholder="Type instruction or command..." /><button type="button" className="rounded-xl bg-cyan-300 px-3 py-2 text-slate-950"><Send className="h-4 w-4" /></button></div></div>
    </GlassPanel>
  );
}
