import { useState } from "react";
import { Link } from "react-router-dom";
import { enviarRecordatorio, obtenerPendientes } from "../lib/api";
import { comprobar } from "../lib/errores";
import { textoEstadoAcceso } from "../lib/textosTarea";
import { useCurso } from "../components/Layout";
import {
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Vacio,
  etiqueta,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
function Recordatorio({ id }: { id: string }) {
  const { curso } = useCurso();
  const op = useOperacion();
  const [solicitado, setSolicitado] = useState(false);
  return (
    <div>
      <button
        disabled={op.ocupado || solicitado}
        onClick={() =>
          void op.ejecutar(async () => {
            const r = await enviarRecordatorio(curso.id, id);
            if (r.status === 429) {
              setSolicitado(true);
              throw new Error(
                "Ya se solicitó un recordatorio para este estudiante hoy.",
              );
            }
            await comprobar(r);
            setSolicitado(true);
          }, "Recordatorio solicitado por Canvas. La recepción depende del procesamiento del envío.")
        }
      >
        {op.ocupado
          ? "Solicitando…"
          : solicitado
            ? "Recordatorio solicitado"
            : "Enviar recordatorio"}
      </button>
      <Mensajes {...op} />
    </div>
  );
}
export function Pendientes() {
  const { curso, puede } = useCurso();
  const c = useConsulta(`pendientes-${curso.id}`, () =>
    obtenerPendientes(curso.id),
  );
  const d = c.datos;
  return (
    <>
      <Cabecera
        titulo="Pendientes"
        descripcion="Información o accesos que requieren atención. Los repositorios que ya tienen sus datos continúan automáticamente."
        acciones={
          <button disabled={c.cargando} onClick={c.recargar}>
            Actualizar pendientes
          </button>
        }
      />
      {c.error && <ErrorCarga error={c.error} reintentar={c.recargar} />}
      {!d ? (
        !c.error && <Cargando />
      ) : (
        <div className="stack pending-list">
          <section className="panel">
            <h2>Sin cuenta de GitHub · {d.bloque_1_sin_cuenta.length}</h2>
            <p>
              Estos estudiantes deben declarar su cuenta en Canvas o recibir
              ayuda del equipo docente. Máximo un recordatorio por estudiante al
              día.
            </p>
            {!d.bloque_1_sin_cuenta.length ? (
              <Vacio>No hay pendientes de este tipo.</Vacio>
            ) : (
              <ul className="list-clean">
                {d.bloque_1_sin_cuenta.map((f) => (
                  <li key={f.estudiante_id}>
                    <div className="panel-header">
                      <div>
                        <strong>{f.nombre}</strong>
                        <p className="help">
                          Inscripción: {etiqueta(f.estado_estudiante)}
                        </p>
                        <Estado valor={f.estado_mapeo} />
                      </div>
                      {puede("comunicacion.enviar") && (
                        <Recordatorio id={f.estudiante_id} />
                      )}
                    </div>
                    {puede("mapeo.editar") && (
                      <Link to={`/cursos/${curso.id}/personas`}>
                        Revisar y asociar cuenta en Personas
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            )}
            {!puede("comunicacion.enviar") && (
              <p className="help">
                El envío de recordatorios requiere permiso de comunicaciones.
              </p>
            )}
          </section>
          <section className="panel">
            <h2>Cuentas en conflicto · {d.bloque_2_en_conflicto.length}</h2>
            <p>
              Revisa la cuenta declarada y el motivo antes de corregir una
              asociación.
            </p>
            {!d.bloque_2_en_conflicto.length ? (
              <Vacio>No hay pendientes de este tipo.</Vacio>
            ) : (
              <ul className="list-clean">
                {d.bloque_2_en_conflicto.map((f) => (
                  <li key={f.estudiante_id}>
                    <div className="panel-header">
                      <strong>{f.nombre}</strong>
                      <Estado valor={f.estado_mapeo} />
                    </div>
                    <p>
                      {f.cuenta_login
                        ? `@${f.cuenta_login}`
                        : "Sin cuenta identificada"}
                    </p>
                    {f.motivo_invalidacion && (
                      <p className="help">{etiqueta(f.motivo_invalidacion)}</p>
                    )}
                    <Link to={`/cursos/${curso.id}/personas`}>
                      Revisar en Personas
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="panel">
            <h2>Grupos incompletos · {d.bloque_3_grupos_incompletos.length}</h2>
            <p>
              Información sincronizada desde Canvas. En esta versión las tareas
              son individuales.
            </p>
            {!d.bloque_3_grupos_incompletos.length ? (
              <Vacio>No hay pendientes de este tipo.</Vacio>
            ) : (
              <ul className="list-clean">
                {d.bloque_3_grupos_incompletos.map((f, i) => (
                  <li key={`${f.estudiante_id}-${i}`}>
                    <strong>{f.nombre ?? "Información del curso"}</strong>
                    <p>
                      {etiqueta(f.tipo)} · {etiqueta(f.severidad)}
                    </p>
                    {Object.keys(f.detalle).length > 0 && (
                      <details>
                        <summary>Ver detalle</summary>
                        <pre>{JSON.stringify(f.detalle, null, 2)}</pre>
                      </details>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="panel">
            <h2>
              Invitaciones sin aceptar ·{" "}
              {d.bloque_4_invitaciones_sin_aceptar.length}
            </h2>
            <p>
              El repositorio puede estar creado mientras el estudiante aún debe
              aceptar su invitación en GitHub.
            </p>
            {!d.bloque_4_invitaciones_sin_aceptar.length ? (
              <Vacio>No hay pendientes de este tipo.</Vacio>
            ) : (
              <ul className="list-clean">
                {d.bloque_4_invitaciones_sin_aceptar.map((f, i) => (
                  <li key={`${f.estudiante_id}-${i}`}>
                    <strong>{f.nombre}</strong>
                    <p className="help">{textoEstadoAcceso(f.estado_acceso)}</p>
                  </li>
                ))}
              </ul>
            )}
            <Link to={`/cursos/${curso.id}/tareas`}>
              Consultar repositorios por tarea
            </Link>
          </section>
        </div>
      )}
    </>
  );
}
