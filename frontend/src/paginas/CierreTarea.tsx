import { useState } from "react";
import {
  archivarTarea,
  desarchivarTarea,
  enviarAvisoArchivado,
  type EstadoArchivado,
} from "../lib/api";

import { consultarOperacion } from "../lib/apiOperacion";
import { useCurso } from "../components/Layout";
import {
  Aviso,
  Cargando,
  ErrorCarga,
  Mensajes,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";

const ESTILO_MOTIVO = {
  fontSize: "0.85rem",
  color: "var(--color-text-secondary)",
} as const;

const CONSECUENCIAS = [
  "Cada repositorio pasa a sólo lectura en GitHub: los estudiantes lo siguen viendo, pero no pueden subir cambios.",
  "Las versiones ya capturadas no cambian: la evidencia es el commit registrado aquí.",
  "No se pueden crear etiquetas nuevas, y la actividad deja de leerse para esos repositorios.",
  "Es reversible: «Desarchivar» vuelve a abrir todos los repositorios archivados de la tarea.",
];

/** Bloque «Cierre de la tarea» (A-168, A-197): las cinco guardas a la vista
 * antes de habilitar el botón. Archivar y desarchivar son sólo del profesor. */
export function CierreTarea({
  cursoId,
  tareaId,
}: {
  cursoId: string;
  tareaId: string;
}) {
  const { contexto, puede } = useCurso();
  const autorizado = contexto.rol === "PROFESOR" && puede("tarea.administrar");
  const consulta = useConsulta(
    `archivado-${cursoId}-${tareaId}`,
    (signal) =>
      consultarOperacion<EstadoArchivado>(
        `/api/cursos/${cursoId}/tareas/${tareaId}/archivado`,
        { signal },
      ),
    10_000,
  );
  const estado = consulta.datos;
  const [sinCaptura, setSinCaptura] = useState("");
  const [sinAviso, setSinAviso] = useState("");
  const op = useOperacion();
  const confirmar = useConfirmar();
  if (!estado)
    return consulta.error ? (
      <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
    ) : (
      <Cargando texto="Comprobando condiciones de cierre…" />
    );

  // Una guarda que falla sólo por falta de confirmación se supera escribiéndola.
  const superable = estado.guardas.every(
    (g) =>
      g.cumple ||
      (g.confirmacion === "SIN_CAPTURA" && sinCaptura.trim().length >= 10) ||
      (g.confirmacion === "SIN_AVISO" && sinAviso.trim().length >= 10),
  );
  const habilitado =
    estado.archivables > 0 && estado.en_curso === 0 && superable;
  const pideCaptura = estado.guardas.some(
    (g) => !g.cumple && g.confirmacion === "SIN_CAPTURA",
  );
  const pideAviso = estado.guardas.some(
    (g) => !g.cumple && g.confirmacion === "SIN_AVISO",
  );
  const avisoPendiente =
    estado.aviso.destinatarios > 0 &&
    estado.aviso.encolados < estado.aviso.destinatarios;

  async function onAviso() {
    if (
      !autorizado ||
      !(await confirmar({
        titulo: "Enviar aviso previo",
        descripcion: `Se enviará el aviso de archivado a ${estado!.aviso.destinatarios} estudiantes de esta tarea por Canvas.`,
        accion: "Enviar aviso",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await enviarAvisoArchivado(cursoId, tareaId);
      if (!r.ok || !r.datos)
        throw new Error(r.error ?? "No se pudo encolar el aviso.");
      op.setMensaje(
        `Aviso previo encolado para ${r.datos.encolados} estudiantes.`,
      );
      consulta.recargar();
    });
  }
  async function onArchivar() {
    if (
      !autorizado ||
      !(await confirmar({
        titulo: "Archivar repositorios",
        descripcion: `Los ${estado!.archivables} repositorios de esta tarea pasarán a solo lectura en GitHub. Las versiones registradas se conservan.`,
        accion: "Archivar repositorios",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await archivarTarea(cursoId, tareaId, {
        confirmacion_sin_captura: pideCaptura ? sinCaptura : null,
        confirmacion_sin_aviso: pideAviso ? sinAviso : null,
      });
      if (!r.ok || !r.datos)
        throw new Error(r.error ?? "No se pudo solicitar el archivado.");
      op.setMensaje(
        `Archivado en curso para ${r.datos.repositorios} repositorios.`,
      );
      consulta.recargar();
    });
  }
  async function onDesarchivar() {
    if (
      !autorizado ||
      !(await confirmar({
        titulo: "Desarchivar repositorios",
        descripcion: `Se habilitarán nuevamente los cambios en ${estado!.archivados} repositorios archivados de esta tarea.`,
        accion: "Desarchivar",
      }))
    )
      return;
    await op.ejecutar(async () => {
      const r = await desarchivarTarea(cursoId, tareaId);
      if (!r.ok || !r.datos)
        throw new Error(r.error ?? "No se pudo solicitar el desarchivado.");
      op.setMensaje(
        `Desarchivado en curso para ${r.datos.repositorios} repositorios.`,
      );
      consulta.recargar();
    });
  }

  return (
    <section className="panel">
      <h2>Cierre de la tarea</h2>
      <p>
        {estado.tarea_estado === "ARCHIVADA" ? "La tarea está archivada. " : ""}
        {estado.archivables} repositorios por archivar · {estado.archivados}{" "}
        archivados
        {estado.fuera_de_alcance_o_inaccesibles > 0 &&
          ` · ${estado.fuera_de_alcance_o_inaccesibles} fuera de alcance o inaccesibles`}
        {estado.en_curso > 0 && ` · ${estado.en_curso} en curso`}
      </p>
      <Mensajes {...op} />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!autorizado && (
        <Aviso>
          Solo un profesor con permiso para administrar tareas puede archivar,
          desarchivar o enviar el aviso previo. Puedes revisar las condiciones
          de cierre.
        </Aviso>
      )}

      {estado.archivables > 0 && (
        <>
          <ol>
            {estado.guardas.map((g) => (
              <li key={g.numero}>
                <strong>{g.cumple ? "Cumple" : "Falta"}</strong> · {g.titulo}
                {g.motivo && <div style={ESTILO_MOTIVO}>{g.motivo}</div>}
                {g.detalle.length > 0 && (
                  <ul style={ESTILO_MOTIVO}>
                    {g.detalle.slice(0, 10).map((d) => (
                      <li key={d}>{d}</li>
                    ))}
                    {g.detalle.length > 10 && (
                      <li>y {g.detalle.length - 10} más</li>
                    )}
                  </ul>
                )}
                {g.numero === 4 && avisoPendiente && autorizado && (
                  <div>
                    <button
                      disabled={op.ocupado}
                      onClick={() => void onAviso()}
                    >
                      Enviar aviso previo por Canvas
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ol>
          {pideCaptura && autorizado && (
            <label style={{ display: "block" }}>
              Por qué archivas con entregas sin versión capturada
              <textarea
                value={sinCaptura}
                onChange={(e) => setSinCaptura(e.target.value)}
                rows={2}
                style={{ width: "100%" }}
              />
            </label>
          )}
          {pideAviso && autorizado && (
            <label style={{ display: "block" }}>
              Declara cuántos estudiantes no recibieron el aviso y cómo les
              avisaste
              <textarea
                value={sinAviso}
                onChange={(e) => setSinAviso(e.target.value)}
                rows={2}
                style={{ width: "100%" }}
              />
            </label>
          )}
          <p style={ESTILO_MOTIVO}>Qué implica archivar:</p>
          <ul style={ESTILO_MOTIVO}>
            {CONSECUENCIAS.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
          {autorizado && (
            <button
              disabled={!habilitado || op.ocupado}
              onClick={() => void onArchivar()}
            >
              Archivar repositorios de la tarea
            </button>
          )}{" "}
        </>
      )}
      {estado.puede_desarchivar && autorizado && (
        <button
          disabled={estado.en_curso > 0 || op.ocupado}
          onClick={onDesarchivar}
        >
          Desarchivar
        </button>
      )}
      <p style={ESTILO_MOTIVO}>
        Sólo un profesor del curso puede archivar o desarchivar.
      </p>
    </section>
  );
}
