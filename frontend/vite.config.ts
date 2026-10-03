import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const api = env.API_PROXY_TARGET || "http://127.0.0.1:8000";
  return {
    plugins: [react(), tailwindcss()],
    resolve: { alias: { "@": new URL("./src", import.meta.url).pathname } },
    server: {
      proxy: {
        "/api": api,
        "/auth": api,
        "/salud": api,
        "/estado": api,
      },
    },
  };
});
