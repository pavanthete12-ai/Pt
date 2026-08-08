import { AnimatePresence, motion } from 'framer-motion';
import { useState } from 'react';
import { BottomStatusBar } from './components/layout/BottomStatusBar';
import { Sidebar } from './components/navigation/Sidebar';
import { TopNav } from './components/navigation/TopNav';
import { renderView } from './pages/pageRegistry';
import type { ViewId } from './types/navigation';

export function App(): JSX.Element {
  const [activeView, setActiveView] = useState<ViewId>('dashboard');

  return (
    <div className="relative h-screen overflow-hidden bg-shadow-bg text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(34,211,238,0.22),transparent_28%),radial-gradient(circle_at_80%_0%,rgba(59,130,246,0.18),transparent_26%),linear-gradient(135deg,rgba(15,23,42,0.2),rgba(2,6,23,0.95))]" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(34,211,238,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(34,211,238,0.05)_1px,transparent_1px)] bg-[size:48px_48px] opacity-30" />

      <div className="relative flex h-full">
        <Sidebar activeView={activeView} onNavigate={setActiveView} onAgentTown={() => setActiveView('dashboard')} />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopNav activeView={activeView} />
          <main className="min-h-0 flex-1 overflow-auto p-6">
            <AnimatePresence mode="wait">
              <motion.div key={activeView} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -14 }} transition={{ duration: 0.22 }}>
                {renderView(activeView)}
              </motion.div>
            </AnimatePresence>
          </main>
          <BottomStatusBar />
        </div>
      </div>
    </div>
  );
}
