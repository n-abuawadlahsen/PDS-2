import { useEffect, useRef, useState, type ReactNode } from "react";
import { API_BASE_URL } from "../lib/api";
import { Aviso } from "./ui";

// La pagina de arranque del alojamiento puede responder HTML incluso con 200.
// Solo una respuesta JSON de nuestra API permite iniciar la navegacion POST.
async function esperarApi(signal: AbortSignal): Promise<void> {
  const limite = Date.now() + 120_000;
  while (!signal.aborted && Date.now() < limite) {
    const intento = new AbortController();
    const cancelar = () => intento.abort();
    signal.addEventListener("abort", cancelar, { once: true });
    const timeout = window.setTimeout(cancelar, 8_000);
    try {
      const r = await fetch(`${API_BASE_URL}/api/salud`, {
        signal: intento.signal,
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (r.ok && r.headers.get("content-type")?.includes("application/json")) {
        const datos: unknown = await r.json();
        if (
          datos &&
          typeof datos === "object" &&
          "estado" in datos &&
          datos.estado === "ok" &&
          "servicio" in datos &&
          datos.servicio === "api"
        )
          return;
      }
    } catch {
      // Un timeout o una respuesta intermedia se reintenta dentro del limite.
    } finally {
      window.clearTimeout(timeout);
      signal.removeEventListener("abort", cancelar);
    }
    await new Promise<void>((resolve) => {
      if (signal.aborted) return resolve();
      const terminar = () => {
        window.clearTimeout(timer);
        signal.removeEventListener("abort", terminar);
        resolve();
      };
      const timer = window.setTimeout(terminar, 1_500);
      signal.addEventListener("abort", terminar, { once: true });
    });
  }
  throw new Error(
    "No pudimos conectar con el servicio. Intenta nuevamente en unos momentos.",
  );
}

export function FormularioAcceso({
  action,
  children,
  texto,
  disabled = false,
}: {
  action: "/auth/google/inicio" | "/auth/confirmar";
  children?: ReactNode;
  texto: string;
  disabled?: boolean;
}) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");
  const peticion = useRef<AbortController | null>(null);
  useEffect(() => {
    // Al volver con Atras desde Google, no dejar bloqueado el formulario del bfcache.
    const volver = () => {
      peticion.current = null;
      setEnviando(false);
    };
    window.addEventListener("pageshow", volver);
    return () => {
      peticion.current?.abort();
      window.removeEventListener("pageshow", volver);
    };
  }, []);
  useEffect(() => {
    if (disabled && peticion.current) {
      peticion.current.abort();
      peticion.current = null;
      setEnviando(false);
    }
  }, [disabled]);
  return (
    <form
      method="POST"
      action={`${API_BASE_URL}${action}`}
      onSubmit={async (e) => {
        e.preventDefault();
        if (disabled || peticion.current) return;
        const formulario = e.currentTarget;
        const control = new AbortController();
        peticion.current = control;
        setError("");
        setEnviando(true);
        try {
          await esperarApi(control.signal);
          if (!control.signal.aborted && formulario.isConnected)
            formulario.submit();
        } catch (err) {
          if (!control.signal.aborted) {
            setError(
              err instanceof Error ? err.message : "No pudimos conectar.",
            );
            setEnviando(false);
            peticion.current = null;
          }
        }
      }}
    >
      {children}
      {error && <Aviso tipo="error">{error}</Aviso>}
      <button className="primary" type="submit" disabled={disabled || enviando}>
        {enviando ? "Preparando acceso…" : texto}
      </button>
      {enviando && (
        <p className="help" role="status">
          Estamos conectando con el servicio. Si estaba inactivo, puede tardar
          hasta dos minutos. Continuaremos automáticamente.
        </p>
      )}
    </form>
  );
}
