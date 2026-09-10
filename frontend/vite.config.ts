import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
const target = process.env.API_TARGET || 'http://127.0.0.1:8081';
const proxy = Object.fromEntries(['/api', '/healthz', '/readyz'].map(path => [path, { target }]));
export default defineConfig({
  plugins: [react()],
  server: { host: '127.0.0.1', port: 5173, strictPort: true, proxy },
  preview: { host: '127.0.0.1', port: 4174, strictPort: true, proxy },
  build: { chunkSizeWarningLimit: 750 },
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], include: ['src/**/*.test.ts', 'src/**/*.test.tsx'], restoreMocks: true },
});
