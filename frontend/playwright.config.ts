import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1,
  use: { baseURL: 'http://127.0.0.1:4174', trace: 'retain-on-failure',
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {} },
  webServer: [
    { command: 'python ../cloud/app.py', url: 'http://127.0.0.1:18081/healthz', env: {PORT:'18081', DB_PATH:'../artifacts/frontend-e2e.sqlite3'} },
    { command: 'npm run preview', url: 'http://127.0.0.1:4174', env: {API_TARGET:'http://127.0.0.1:18081'} }
  ],
});
