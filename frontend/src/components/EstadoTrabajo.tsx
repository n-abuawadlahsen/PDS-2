import { useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";
import { comprobar } from "../lib/errores";
import { fechaLegible } from "../lib/textosTarea";
import { useConsulta } from "../hooks/useConsulta";
import { Aviso, ErrorCarga, etiqueta } from "./ui";

export interface Trabajo {
  id: string;
  estado: string;
  intentos: number;
  max_intentos: number;
  proximo_intento_en: string | null;
  terminado_en: string | null;
}
export function EstadoTrabajo({
  ruta,
  zona,
  alTerminar,
  cadencia = 2000,
}: {
  ruta: string;
  zona: string;
  alTerminar?: (trabajo: Trabajo) => void;
  cadencia?: number;
}) {
  const [terminado, setTerminado] = useState(false);
  const notificado = useRef("");
  const consulta = useConsulta(
    ruta,
    async (signal) => {
      const r = await apiFetch(ruta, { signal });
      await comprobar(r);
      return r.json() as Promise<Trabajo>;
    },
    terminado ? 0 : cadencia,
  );
  const trabajo = consulta.datos;
  useEffect(() => {
    if (
      trabajo &&
      ["OK", "CANCELADO", "REQUIERE_ATENCION"].includes(trabajo.estado) &&
      notificado.current !== `${trabajo.id}:${trabajo.estado}`
    ) {
      notificado.current = `${trabajo.id}:${trabajo.estado}`;
      setTerminado(true);
      alTerminar?.(trabajo);
    }
  }, [trabajo, alTerminar]);
  return (
    <div aria-live="polite">
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {trabajo && (
        <Aviso
          tipo={trabajo.estado === "REQUIERE_ATENCION" ? "warning" : "info"}
        >
          Trabajo: {etiqueta(trabajo.estado)}. Intentos: {trabajo.intentos} de{" "}
          {trabajo.max_intentos}.
          {trabajo.estado === "REINTENTAR" && trabajo.proximo_intento_en && (
            <>
              {" "}
              Próximo intento: {fechaLegible(trabajo.proximo_intento_en, zona)}.
            </>
          )}
          {trabajo.estado === "REQUIERE_ATENCION" && (
            <>
              {" "}
              El proceso requiere atención. Revisa los resultados disponibles
              antes de solicitar otro intento.
            </>
          )}
        </Aviso>
      )}
    </div>
  );
}
