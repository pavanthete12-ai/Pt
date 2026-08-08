import type { Config } from 'tailwindcss';

export default {
  content: ['./src/renderer/index.html', './src/renderer/src/**/*.{ts,tsx}'],
  theme: { extend: { colors: { shadow: { bg: '#05090f', panel: '#0b1520', cyan: '#28f7ff', amber: '#f6a94b' } } } },
  plugins: []
} satisfies Config;
