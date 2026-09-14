import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { enviarRecordatorio, obtenerPendientes, type Pendientes as PendientesDatos } from "../lib/api";
import { textoEstadoAcceso } from "../lib/textosTarea";

/** `/cursos/{id}/pendientes` (SPEC 07 S7.8): la pantalla unica de
 * informacion faltante, los cuatro bloques literales de S7.8.1. */
export function Pendientes() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [datos, setDatos] = useState<PendientesDatos | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [enviando, setEnviando] = useState<string | null>(null);

  async function cargar() {
    if (!cursoId) return;
    setDatos(await obtenerPendientes(cursoId));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId]);

  async function onRecordatorio(estudianteId: string) {
    if (!cursoId) return;
    setEnviando(estudianteId);
    setMensaje(null);
    const respuesta = await enviarRecordatorio(cursoId, estudianteId);
    if (respuesta.ok) {
      setMensaje("Recordatorio enviado.");
    } else if (respuesta.status === 429) {
      setMensaje("Ya se envió un recordatorio a este estudiante hoy.");
    } else {
      setMensaje(`No se pudo enviar (${respuesta.status}).`);
    }
    setEnviando(null);
  }

  if (!datos) {
    return (
      <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <p>Cargando…</p>
      </main>
    );
  }

  return (
    <main style={{ maxWidth: 900, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Pendientes</h1>
      {mensaje && <p role="status">{mensaje}</p>}

      <section>
        <h2>1. Sin cuenta de GitHub ({datos.bloque_1_sin_cuenta.length})</h2>
        {datos.bloque_1_sin_cuenta.length === 0 ? (
          <p>Nada pendiente en este bloque.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Estado del estudiante</th>
                <th>Estado del mapeo</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {datos.bloque_1_sin_cuenta.map((f) => (
                <tr key={f.estudiante_id}>
                  <td>{f.nombre}</td>
                  <td>{f.estado_estudiante}</td>
                  <td>{f.estado_mapeo}</td>
                  <td>
                    <button
                      onClick={() => onRecordatorio(f.estudiante_id)}
                      disabled={enviando === f.estudiante_id}
                    >
                      {enviando === f.estudiante_id ? "…" : "Enviar recordatorio"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>2. Cuentas en conflicto ({datos.bloque_2_en_conflicto.length})</h2>
        {datos.bloque_2_en_conflicto.length === 0 ? (
          <p>Nada pendiente en este bloque.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Estado</th>
                <th>Motivo</th>
                <th>Cuenta</th>
              </tr>
            </thead>
            <tbody>
              {datos.bloque_2_en_conflicto.map((f) => (
                <tr key={f.estudiante_id}>
                  <td>{f.nombre}</td>
                  <td>{f.estado_mapeo}</td>
                  <td>{f.motivo_invalidacion ?? "—"}</td>
                  <td>{f.cuenta_login ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>3. Grupos incompletos ({datos.bloque_3_grupos_incompletos.length})</h2>
        {datos.bloque_3_grupos_incompletos.length === 0 ? (
          <p>Nada pendiente en este bloque.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Severidad</th>
                <th>Nombre</th>
              </tr>
            </thead>
            <tbody>
              {datos.bloque_3_grupos_incompletos.map((f, i) => (
                <tr key={`${f.estudiante_id ?? "curso"}-${i}`}>
                  <td>{f.tipo}</td>
                  <td>{f.severidad}</td>
                  <td>{f.nombre ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>4. Invitaciones sin aceptar ({datos.bloque_4_invitaciones_sin_aceptar.length})</h2>
        {datos.bloque_4_invitaciones_sin_aceptar.length === 0 ? (
          <p>Nada pendiente en este bloque.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nombre</th>
                <th>Invitación</th>
              </tr>
            </thead>
            <tbody>
              {datos.bloque_4_invitaciones_sin_aceptar.map((f, i) => (
                <tr key={`${f.estudiante_id}-${i}`}>
                  <td>{f.nombre}</td>
                  <td>{textoEstadoAcceso(f.estado_acceso)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p>{cursoId && <Link to={`/cursos/${cursoId}/personas`}>Volver a Personas</Link>}</p>
    </main>
  );
}
