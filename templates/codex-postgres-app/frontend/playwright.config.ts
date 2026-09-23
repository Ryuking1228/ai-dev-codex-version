import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', retries: 0, workers: 1,
  reporter: [['list'], ['json', { outputFile: '../.app-state/e2e-results.json' }]],
  use: { baseURL: process.env.APP_URL || 'http://127.0.0.1:8000', trace: 'retain-on-failure' }
});
