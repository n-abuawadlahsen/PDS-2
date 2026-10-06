import { useState } from "react";
import { useCurso } from "./Layout";
import { Aviso, Cargando, ErrorCarga, Mensajes, useConfirmar } from "./ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { consultarFinal, fechaFinal } from "../lib/apiFinal";

type Candidato = {
  estudiante_id: string;
  nombre: string;
  canvas_user_id: number;
  coincidencias: string[];
  motivo_bloqueo: string | null;
  repositorios_conservados: number;
  versiones_conservadas: number;
};
type Fusion = {
  incidencia_id: string;
  nombre: string;
  canvas_user_id: number;
  candidatos: Candidato[];
};
type Historia = {
  fecha: string;
  antes: { canvas_user_id_anterior: number; canvas_user_id_nuevo: number };
};
type Vista = { pendientes: Fusion[]; historial: Historia[] };
export function FusionesCanvas({ alCambiar }: { alCambiar: () => void }) {
  const { curso, puede, contexto } = useCurso();
  const [abierto, setAbierto] = useState(false);
  const op = useOperacion();
  const confirmar = useConfirmar();
  const ruta = `/api/cursos/${curso.id}/personas/fusiones-canvas`;
  const autorizado = puede("mapeo.editar") && contexto.rol === "PROFESOR";
  const consulta = useConsulta(`${ruta}:${abierto}:${autorizado}`, (signal) =>
    abierto && autorizado
      ? consultarFinal<Vista>(ruta, { signal })
      : Promise.resolve({ pendientes: [], historial: [] }),
  );
  if (!autorizado) return null;
  return (
    <details
      className="panel"
      onToggle={(e) => setAbierto(e.currentTarget.open)}
    >
      <summary>Revisar posibles fusiones de identidades Canvas</summary>
      <p>
        Una coincidencia de login o identificador institucional requiere
        revisión. Ninguna identidad se fusiona automáticamente ni por similitud
        de nombres.
      </p>
      <Mensajes {...op} />
      {consulta.cargando && <Cargando />}
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {abierto &&
        !consulta.cargando &&
        !consulta.error &&
        !consulta.datos?.pendientes.length && (
          <p>No hay propuestas de fusión pendientes.</p>
        )}
      {consulta.datos?.pendientes.map((f) => (
        <section key={f.incidencia_id}>
          <h3>
            {f.nombre} · Canvas {f.canvas_user_id}
          </h3>
          {f.candidatos.map((c) => (
            <div key={c.estudiante_id}>
              <p>
                Identidad retirada: {c.nombre} · Canvas {c.canvas_user_id}.
                Coincide:{" "}
                {c.coincidencias
                  .map((campo) =>
                    campo === "login_id"
                      ? "identificador de acceso"
                      : "identificador institucional",
                  )
                  .join(", ")}
                .
              </p>
              <p>
                Se conservarán los repositorios ({c.repositorios_conservados}) y
                las versiones ({c.versiones_conservadas}) de la identidad
                anterior.
              </p>
              {c.motivo_bloqueo && (
                <Aviso tipo="warning">{c.motivo_bloqueo}</Aviso>
              )}
              <button
                disabled={op.ocupado || Boolean(c.motivo_bloqueo)}
                onClick={() => {
                  void op.ejecutar(async () => {
                    if (
                      !(await confirmar({
                        titulo: "Confirmar fusión de identidades Canvas",
                        descripcion: `Confirma que ${c.nombre} (Canvas ${c.canvas_user_id}) y ${f.nombre} (Canvas ${f.canvas_user_id}) son la misma persona. Se conservarán los repositorios, versiones, borradores y mapeos de la identidad anterior. El padrón usará el nuevo ID de Canvas; la fila nueva quedará como alias histórico.`,
                        accion: "Confirmar fusión",
                        peligro: true,
                      }))
                    )
                      return;
                    await consultarFinal(
                      `${ruta}/${f.incidencia_id}/confirmar`,
                      {
                        method: "POST",
                        body: JSON.stringify({
                          anterior_id: c.estudiante_id,
                          confirmar: true,
                        }),
                      },
                    );
                    consulta.recargar();
                    alCambiar();
                  }, "Identidades fusionadas. Se solicitó actualizar grupos, tareas y la validez del mapeo GitHub.");
                }}
              >
                Confirmar que es la misma persona
              </button>
            </div>
          ))}
        </section>
      ))}
      {Boolean(consulta.datos?.historial.length) && (
        <>
          <h3>Fusiones confirmadas</h3>
          <ul>
            {consulta.datos?.historial.map((h, i) => (
              <li key={`${h.fecha}:${i}`}>
                Canvas {h.antes.canvas_user_id_anterior} →{" "}
                {h.antes.canvas_user_id_nuevo} ·{" "}
                {fechaFinal(h.fecha, curso.zona_horaria)}
              </li>
            ))}
          </ul>
        </>
      )}
    </details>
  );
}
