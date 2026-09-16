import { useCallback, useEffect, useRef, useState } from "react";
import { mensajeError } from "../lib/errores";

/** Una consulta por ciclo; descarta respuestas obsoletas y conserva datos al refrescar. */
export function useConsulta<T>(
  clave: string,
  consultar: (signal: AbortSignal) => Promise<T>,
  intervalo = 0,
) {
  const consulta = useRef(consultar);
  consulta.current = consultar;
  const [revision, setRevision] = useState(0);
  const [estado, setEstado] = useState<{
    clave: string;
    datos: T | null;
    error: string | null;
    cargando: boolean;
  }>({ clave, datos: null, error: null, cargando: true });
  const recargar = useCallback(() => setRevision((n) => n + 1), []);
  useEffect(() => {
    let vigente = true;
    const controlador = new AbortController();
    let temporizador: ReturnType<typeof setTimeout> | undefined;
    async function cargar() {
      setEstado((e) => ({
        clave,
        datos: e.clave === clave ? e.datos : null,
        error: null,
        cargando: true,
      }));
      try {
        const datos = await consulta.current(controlador.signal);
        if (vigente) setEstado({ clave, datos, error: null, cargando: false });
      } catch (error) {
        if (vigente)
          setEstado((e) => ({
            ...e,
            error: mensajeError(error),
            cargando: false,
          }));
      } finally {
        if (vigente && intervalo) temporizador = setTimeout(cargar, intervalo);
      }
    }
    // Deferir evita duplicar lecturas del primer montaje de StrictMode.
    temporizador = setTimeout(cargar, 0);
    return () => {
      vigente = false;
      controlador.abort();
      clearTimeout(temporizador);
    };
  }, [clave, revision, intervalo]);
  const actualizar = useCallback(
    (datos: T) => setEstado({ clave, datos, error: null, cargando: false }),
    [clave],
  );
  return {
    actualizar,
    ...(estado.clave === clave
      ? estado
      : { datos: null, error: null, cargando: true }),
    recargar,
  };
}

export function useOperacion() {
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const bloqueo = useRef(false);
  const montado = useRef(true);
  useEffect(() => {
    montado.current = true;
    return () => {
      montado.current = false;
    };
  }, []);
  async function ejecutar<T>(
    accion: () => Promise<T>,
    exito?: string,
  ): Promise<T | undefined> {
    if (bloqueo.current) return undefined;
    bloqueo.current = true;
    setOcupado(true);
    setError(null);
    setMensaje(null);
    try {
      const resultado = await accion();
      if (montado.current && exito) setMensaje(exito);
      return resultado;
    } catch (e) {
      if (montado.current) setError(mensajeError(e));
    } finally {
      bloqueo.current = false;
      if (montado.current) setOcupado(false);
    }
  }
  return { ocupado, error, mensaje, ejecutar, setError, setMensaje };
}
