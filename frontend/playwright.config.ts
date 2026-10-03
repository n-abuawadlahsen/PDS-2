import { defineConfig } from "@playwright/test";
const port = Number(process.env.PLAYWRIGHT_PORT || 4173);
export default defineConfig({
  testDir: "./tests",
  testIgnore: "**/*.backend.spec.ts",
  timeout: 30_000,
  fullyParallel: true,
  workers: 3,
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    viewport: { width: 1366, height: 768 },
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `npm run dev -- --host 127.0.0.1 --port ${port} --strictPort`,
    url: `http://127.0.0.1:${port}`,
    reuseExistingServer: false,
    env: { VITE_API_BASE_URL: "" },
  },
});
