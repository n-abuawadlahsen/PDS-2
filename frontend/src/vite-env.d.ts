/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Origen de la API; vacio o ausente = mismo origen (proxy de Vercel). */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
