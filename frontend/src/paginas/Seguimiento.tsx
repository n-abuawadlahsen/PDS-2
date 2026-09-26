import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { obtenerSeguimiento, type FilaSeguimiento } from "../lib/api";

const ESTILO_MOTIVO = { fontSize: "0.85rem", color: "#666" } as const;

/** `/cursos/{id}/seguimiento` (SPEC 10 S10.10.6): una fila por tarea activa,
 * en vivo sobre el espejo, con las mismas cifras que cada tablero. */
export function Seguimiento() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [filas, setFilas] = useState<FilaSeguimiento[] | null>(null);

  useEffect(() => {
    if (cursoId) obtenerSeguimiento(cursoId).then(setFilas);
  }, [cursoId]);

  if (!cursoId || !filas) return <p>Cargando…</p>;
  return (
    <main>
      <p>
        <Link to={`/cursos/${cursoId}/tareas`}>← Tareas</Link>
      </p>
      <h1>Seguimiento del curso</h1>
      {filas.length === 0 ? (
        <p>No hay tareas activas.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Tarea</th>
              <th>Repositorios</th>
              <th>Sin actividad reciente</th>
              <th>Sin participación</th>
              <th>Invitaciones sin aceptar</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.tarea_id}>
                <td>
                  <Link to={`/cursos/${cursoId}/tareas/${f.tarea_id}`}>{f.nombre}</Link>
                  <div style={ESTILO_MOTIVO}>{f.modalidad === "GRUPAL" ? "grupal" : "individual"}</div>
                </td>
                <td>
                  {f.repositorios.operativos} listos · {f.repositorios.degradados} incompletos ·{" "}
                  {f.repositorios.esperando_informacion} con información pendiente
                </td>
                <td>{f.sin_actividad}</td>
                <td>{f.sin_participacion}</td>
                <td>{f.invitaciones_sin_aceptar}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
