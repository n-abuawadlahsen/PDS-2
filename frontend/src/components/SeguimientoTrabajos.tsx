import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useCurso } from "./Layout";
import { ErrorCarga, Estado, Mensajes, etiqueta } from "./ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { fechaLegible } from "../lib/textosTarea";
import { obtenerTrabajo, solicitarSincronizacion, trabajoDetenido } from "../lib/seguimientoOperacion";

export function SeguimientoTrabajos({ ids, terminado }: { ids: string[]; terminado: () => void }) {
  const { curso } = useCurso();
  const clave = ids.join(",");
  const [sondear, setSondear] = useState(true);
  const completado = useRef("");
  const callback = useRef(terminado);
  callback.current = terminado;
  const trabajos = useConsulta(`trabajos-${curso.id}-${clave}`, (signal) =>
    Promise.all(clave.split(",").filter(Boolean).map((id) => obtenerTrabajo(curso.id, id, signal))),
    sondear ? 2000 : 0);
  useEffect(() => {
    setSondear(true);
    const timer = window.setTimeout(() => setSondear(false), 60_000);
    return () => window.clearTimeout(timer);
  }, [clave]);
  useEffect(() => {
    if (!trabajos.datos?.length || !trabajos.datos.every(trabajoDetenido)) return;
    setSondear(false);
    if (completado.current !== clave) {
      completado.current = clave;
      callback.current();
    }
  }, [trabajos.datos, clave]);
  const pendientes = trabajos.datos?.some((t) => !trabajoDetenido(t));
  return <div role="status" aria-live="polite">
    {trabajos.error && <ErrorCarga error={trabajos.error} reintentar={trabajos.recargar} />}
    {trabajos.datos?.map((t) => <p className="help" key={t.id}>
      {({ sync_roster: "Estudiantes", sync_grupos: "Grupos", sync_tareas_y_fechas: "Tareas y fechas", crear_registro_github: "Registro de GitHub" } as Record<string,string>)[t.tipo] ?? etiqueta(t.tipo)}: <Estado valor={t.estado} />
      {t.proximo_intento_en && !trabajoDetenido(t) && <> · Próximo intento: {fechaLegible(t.proximo_intento_en, curso.zona_horaria)}</>}
      {t.requiere_atencion && <> · No se confirmó la actualización. Revisa las conexiones y Operación.</>}
    </p>)}
    {!sondear && pendientes && <p>El trabajo sigue pendiente; puedes seguirlo en <Link to={`/cursos/${curso.id}/operacion`}>Operación</Link>.</p>}
    {!sondear && <button disabled={trabajos.cargando} onClick={trabajos.recargar}>Consultar estado del proceso</button>}
  </div>;
}

export function SincronizarCanvas({ actualizado, titulo = "Sincronizar con Canvas" }: { actualizado: () => void; titulo?: string }) {
  const { curso, puede } = useCurso();
  const op = useOperacion();
  const clave = `pds-sync-${curso.id}`;
  const [solicitud, setSolicitud] = useState<{ ids: string[]; disponible: string } | null>(() => {
    try { return JSON.parse(sessionStorage.getItem(clave) ?? "null"); } catch { return null; }
  });
  const [ahora, setAhora] = useState(Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setAhora(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  const espera = solicitud ? Math.max(0, Math.ceil((Date.parse(solicitud.disponible) - ahora) / 1000)) : 0;
  if (!puede("curso.ver")) return null;
  return <div>
    <button disabled={op.ocupado || espera > 0} onClick={() => void op.ejecutar(async () => {
      const r = await solicitarSincronizacion(curso.id);
      const siguiente = { ids: r.trabajos.map((t) => t.id), disponible: r.disponible_en };
      setSolicitud(siguiente);
      sessionStorage.setItem(clave, JSON.stringify(siguiente));
    }, "La lectura de Canvas quedó solicitada.")}>{op.ocupado ? "Solicitando…" : espera > 0 ? `Disponible de nuevo en ${espera} s` : titulo}</button>
    <p className="help">Los repositorios se crean solos a medida que llega la información. Este botón sólo adelanta la lectura de Canvas.</p>
    <Mensajes {...op} />
    {!!solicitud?.ids.length && <SeguimientoTrabajos ids={solicitud.ids} terminado={actualizado} />}
  </div>;
}
