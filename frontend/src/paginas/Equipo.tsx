import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { invitarMiembro, listarEquipo, obtenerContexto, retirarMiembro, type Contexto, type Miembro } from "../lib/api";
import {
  PERMISOS_AYUDANTE_POR_DEFECTO,
  PERMISOS_CONCEDIBLES,
  PERMISOS_IMPLICITOS,
  PERMISOS_NO_CONCEDIBLES,
} from "../lib/permisos";

/** `/cursos/{id}/equipo` (SPEC 02 S2.4, S2.5, S2.9). */
export function Equipo() {
  const { cursoId } = useParams<{ cursoId: string }>();
  const [contexto, setContexto] = useState<Contexto | null>(null);
  const [equipo, setEquipo] = useState<Miembro[]>([]);
  const [invitando, setInvitando] = useState(false);
  const [email, setEmail] = useState("");
  const [rol, setRol] = useState<"PROFESOR" | "AYUDANTE">("AYUDANTE");
  const [permisos, setPermisos] = useState<string[]>(PERMISOS_AYUDANTE_POR_DEFECTO);
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function cargar() {
    if (!cursoId) return;
    setContexto(await obtenerContexto(cursoId));
    setEquipo(await listarEquipo(cursoId));
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cursoId]);

  const puedeAdministrar = contexto?.permisos_efectivos.includes("equipo.administrar") ?? false;

  function alternarPermiso(clave: string) {
    setPermisos((actual) => (actual.includes(clave) ? actual.filter((p) => p !== clave) : [...actual, clave]));
  }

  async function onInvitar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!cursoId) return;
    setMensaje(null);
    const respuesta = await invitarMiembro(cursoId, {
      email,
      rol,
      permisos: rol === "PROFESOR" ? [] : permisos,
    });
    if (respuesta.ok) {
      setMensaje("Invitación enviada.");
      setInvitando(false);
      setEmail("");
      await cargar();
    } else {
      const cuerpo = await respuesta.json().catch(() => ({}));
      setMensaje(`No se pudo invitar: ${JSON.stringify(cuerpo.detail ?? respuesta.status)}`);
    }
  }

  async function onRetirar(membresiaId: string, nombre: string) {
    if (!cursoId) return;
    if (!window.confirm(`Retirar a ${nombre} del curso`)) return;
    const respuesta = await retirarMiembro(cursoId, membresiaId);
    if (respuesta.ok) {
      await cargar();
    } else {
      const cuerpo = await respuesta.json().catch(() => ({}));
      setMensaje(`No se pudo retirar: ${cuerpo.detail ?? respuesta.status}`);
    }
  }

  return (
    <main style={{ maxWidth: 720, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Equipo docente</h1>
      {mensaje && <p role="status">{mensaje}</p>}
      <p style={{ fontSize: "0.85rem", color: "#666" }}>
        los permisos son del curso completo; el reparto de correcciones es lo que acota qué entrega abre cada
        persona
      </p>

      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Correo</th>
            <th>Rol</th>
            <th>Estado</th>
            {puedeAdministrar && <th></th>}
          </tr>
        </thead>
        <tbody>
          {equipo.map((m) => (
            <tr key={m.membresia_id}>
              <td>{m.nombre}</td>
              <td>{m.email}</td>
              <td>{m.rol}</td>
              <td>{m.estado === "RETIRADA" ? `Retirado el ${m.retirada_en}` : "Activa"}</td>
              {puedeAdministrar && m.estado === "ACTIVA" && (
                <td>
                  <button onClick={() => onRetirar(m.membresia_id, m.nombre)}>Retirar</button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {puedeAdministrar && !invitando && <button onClick={() => setInvitando(true)}>Incorporar</button>}

      {puedeAdministrar && invitando && (
        <form onSubmit={onInvitar} style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxWidth: 420 }}>
          <label>
            Correo (gmail.com)
            <input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label>
            Rol
            <select value={rol} onChange={(e) => setRol(e.target.value as "PROFESOR" | "AYUDANTE")}>
              <option value="AYUDANTE">Ayudante</option>
              <option value="PROFESOR">Profesor</option>
            </select>
          </label>

          {rol === "AYUDANTE" && (
            <fieldset>
              <legend>Permisos</legend>
              {PERMISOS_IMPLICITOS.map((p) => (
                <div key={p.clave}>
                  <label>
                    <input type="checkbox" checked disabled /> {p.etiqueta} ({p.descripcion})
                  </label>
                </div>
              ))}
              {PERMISOS_CONCEDIBLES.map((p) => (
                <div key={p.clave}>
                  <label>
                    <input
                      type="checkbox"
                      checked={permisos.includes(p.clave)}
                      onChange={() => alternarPermiso(p.clave)}
                    />{" "}
                    {p.etiqueta} — {p.descripcion}
                  </label>
                </div>
              ))}
              {PERMISOS_NO_CONCEDIBLES.map((p) => (
                <div key={p.clave}>
                  <label>
                    <input type="checkbox" disabled /> {p.etiqueta} ({p.motivo})
                  </label>
                </div>
              ))}
            </fieldset>
          )}

          <div>
            <button type="submit">Enviar invitación</button>{" "}
            <button type="button" onClick={() => setInvitando(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}
    </main>
  );
}
