import type { PropsWithChildren } from 'react';

interface GlassPanelProps extends PropsWithChildren {
  className?: string;
  resizable?: 'horizontal' | 'vertical' | 'both';
}

const resizeClass = {
  horizontal: 'resize-x overflow-auto',
  vertical: 'resize-y overflow-auto',
  both: 'resize overflow-auto'
};

export function GlassPanel({ children, className = '', resizable }: GlassPanelProps): JSX.Element {
  return (
    <section className={`rounded-3xl border border-cyan-300/15 bg-slate-950/45 shadow-2xl shadow-cyan-950/30 backdrop-blur-2xl ${resizable ? resizeClass[resizable] : ''} ${className}`}>
      {children}
    </section>
  );
}
