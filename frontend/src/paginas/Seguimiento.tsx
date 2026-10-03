import { Link } from "react-router-dom";
import type { FilaSeguimiento } from "../lib/api";
import { consultarOperacion } from "../lib/apiOperacion";
import { useCurso } from "../components/Layout";
import { Cabecera, Cargando, ErrorCarga, Tabla, Vacio } from "../components/ui";
import { useConsulta } from "../hooks/useConsulta";
import { textoModalidad } from "../lib/textosTarea";

export function Seguimiento() {
  const { curso } = useCurso();
  const consulta = useConsulta(`seguimiento-${curso.id}`, (signal) =>
    consultarOperacion<FilaSeguimiento[]>(
      `/api/cursos/${curso.id}/seguimiento`,
      { signal },
    ),
  );
  return (
    <>
      <Cabecera
        titulo="Seguimiento del curso"
        descripcion="Actividad y situaciones que requieren atención en las tareas activas."
        acciones={
          <button disabled={consulta.cargando} onClick={consulta.recargar}>
            Actualizar vista
          </button>
        }
      />
      {consulta.error && (
        <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
      )}
      {!consulta.datos ? (
        !consulta.error && <Cargando />
      ) : consulta.datos.length === 0 ? (
        <Vacio>
          <h2>No hay tareas activas</h2>
          <p>El seguimiento comienza cuando activas una tarea.</p>
          <Link className="button primary" to={`/cursos/${curso.id}/tareas`}>
            Ir a tareas
          </Link>
        </Vacio>
      ) : (
        <section className="panel">
          <Tabla etiqueta="Seguimiento de tareas activas">
            <table>
              <thead>
                <tr>
                  <th scope="col">Tarea</th>
                  <th scope="col">Repositorios</th>
                  <th scope="col">Sin actividad reciente</th>
                  <th scope="col">Participación por revisar</th>
                  <th scope="col">Invitaciones sin aceptar</th>
                </tr>
              </thead>
              <tbody>
                {consulta.datos.map((f) => (
                  <tr key={f.tarea_id}>
                    <td>
                      <Link
                        to={`/cursos/${curso.id}/tareas/${f.tarea_id}?vista=actividad`}
                      >
                        {f.nombre}
                      </Link>
                      <p className="help">{textoModalidad(f.modalidad)}</p>
                    </td>
                    <td>
                      {f.repositorios.operativos} listos ·{" "}
                      {f.repositorios.degradados} con accesos pendientes
                      <p className="help">
                        {f.repositorios.esperando_informacion} esperando
                        información
                      </p>
                    </td>
                    <td>{f.sin_actividad}</td>
                    <td>{f.sin_participacion}</td>
                    <td>{f.invitaciones_sin_aceptar}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Tabla>
        </section>
      )}
    </>
  );
}
