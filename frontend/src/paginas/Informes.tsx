import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  enviarInformeASuscritos,
  enviarmeInforme,
  obtenerInformeDia,
  obtenerInformes,
  obtenerVistaPreviaInforme,
  type InformeDia,
  type InformesCurso,
} from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "var(--color-text-secondary)" } as const;

const ESTADO: Record<string, string> = {
  GENERADO: "Generado",
  SIN_TAREAS_ACTIVAS: "Sin tareas activas: no se envió",
  NO_GENERADO: "No se generó",
};

function fechaCorta(iso: string): string {
  const [a, m, d] = iso.split("-");
  return `${d}-${m}-${a}`;
}

function Documento({ html }: { html: string }) {
  // El informe se muestra aislado: el HTML congelado no puede ejecutar nada.
  return <iframe title="Informe" sandbox="" srcDoc={html} style={{ width: "100%", minHeight: "70vh", border: "1px solid var(--color-border)" }} />;
}

/** Histórico del informe docente diario, vista previa y envíos manuales
 * (SPEC 11 S11.3.2, S11.5.4). */
export function Informes() {
  const { cursoId, fecha } = useParams<{ cursoId: string; fecha?: string }>();
  const [lista, setLista] = useState<InformesCurso | null>(null);
  const [dia, setDia] = useState<InformeDia | null>(null);
  const [vista, setVista] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!cursoId) return;
    obtenerInformes(cursoId).then(setLista);
  }, [cursoId]);

  useEffect(() => {
    if (!cursoId || !fecha) {
      setDia(null);
      return;
    }
    obtenerInformeDia(cursoId, fecha).then(setDia);
  }, [cursoId, fecha]);

  if (!cursoId || !lista) return <p>Cargando…</p>;

  async function onVistaPrevia() {
    if (!cursoId) return;
    const v = await obtenerVistaPreviaInforme(cursoId);
    setVista(v.hay_tareas_activas ? v.html : null);
    setMensaje(v.hay_tareas_activas ? null : v.mensaje);
  }

  async function onEnviarme() {
    if (!cursoId) return;
    setError(null);
    const r = await enviarmeInforme(cursoId);
    if (r.ok) setMensaje("Te enviamos el informe de hoy. Puede tardar unos minutos en llegar.");
    else setError(r.error);
  }

  async function onEnviarATodos() {
    if (!cursoId) return;
    setError(null);
    const r = await enviarInformeASuscritos(cursoId);
    if (r.ok) setMensaje(`Informe encolado para ${r.datos?.encolados ?? 0} personas suscritas.`);
    else setError(r.status === 403 ? "Solo quien administra el curso puede enviarlo a todos." : r.error);
  }

  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link> · <Link to={`/cursos/${cursoId}/mis-notificaciones`}>Mis notificaciones</Link>
      </p>
      <h1>Informe docente diario</h1>
      <p style={ESTILO_MOTIVO}>
        {lista.se_genera_desde
          ? `El informe diario de este curso se genera desde el ${fechaCorta(lista.se_genera_desde)}.`
          : "Todavía no se ha generado ningún informe para este curso."}{" "}
        Llega a las 07:00 mientras haya alguna tarea activa.
      </p>
      {mensaje && <p style={{ background: "var(--color-success-background)", padding: "0.5rem" }}>{mensaje}</p>}
      {error && <p style={{ background: "var(--color-error-background)", padding: "0.5rem" }}>{error}</p>}
      <p>
        <button onClick={onVistaPrevia}>Vista previa del informe de hoy</button>{" "}
        <button onClick={onEnviarme}>Enviarme el informe de hoy</button>{" "}
        <button onClick={onEnviarATodos}>Generar y enviar ahora a los suscritos</button>
      </p>
      {vista && (
        <section>
          <h2>Vista previa (no se guarda ni se envía)</h2>
          <Documento html={vista} />
        </section>
      )}
      {fecha && (
        <section>
          <h2>Informe del {fechaCorta(fecha)}</h2>
          {!dia ? (
            <p>No hay informe de ese día.</p>
          ) : dia.html ? (
            <Documento html={dia.html} />
          ) : (
            <p>{ESTADO[dia.estado] ?? dia.estado}</p>
          )}
        </section>
      )}
      <h2>Días anteriores</h2>
      <ul>
        {lista.informes.map((i) => (
          <li key={i.fecha}>
            <Link to={`/cursos/${cursoId}/informes/${i.fecha}`}>{fechaCorta(i.fecha)}</Link> · {ESTADO[i.estado] ?? i.estado}
            {i.origen === "MANUAL" && " · generado a mano"}
          </li>
        ))}
      </ul>
    </main>
  );
}
