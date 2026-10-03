import { defineConfig } from "@playwright/test";

/** Opcional: API real + PostgreSQL efímero; jamás carga credenciales del equipo. */
export default defineConfig({
  testDir: "./tests",
  testMatch: "**/*.backend.spec.ts",
  workers: 1,
  timeout: 90_000,
  use: {
    baseURL: "http://127.0.0.1:4187",
    viewport: { width: 1366, height: 768 },
    trace: "off",
    actionTimeout: 15_000,
  },
  webServer: [
    {
      command: "../backend/.venv/bin/python tests/serve_backend.py",
      url: "http://127.0.0.1:8017/api/salud",
      timeout: 120_000,
      reuseExistingServer: false,
      gracefulShutdown: { signal: "SIGTERM", timeout: 15_000 },
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4187 --strictPort",
      url: "http://127.0.0.1:4187",
      env: { VITE_API_BASE_URL: "", API_PROXY_TARGET: "http://127.0.0.1:8017" },
      reuseExistingServer: false,
    },
  ],
});
