import { useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, listarEquipo, type Perfil as PerfilTipo } from "../lib/api";
import { comprobar } from "../lib/errores";
import { useSesion } from "../components/Layout";
import {
  Apariencia,
  Aviso,
  Cabecera,
  Cargando,
  ErrorCarga,
  Mensajes,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { fechaLegible } from "../lib/textosTarea";
interface FilaSesion {
  id: number;
  agente: string | null;
  creada_en: string;
  es_la_actual: boolean;
}
export function PerfilPagina() {
  const sesion = useSesion();
  const [perfil, setPerfil] = useState(sesion.perfil);
  const [nombre, setNombre] = useState(perfil.nombre);
  const [login, setLogin] = useState(perfil.github_login_declarado ?? "");
  const [consiento, setConsiento] = useState(false);
  const [bloqueantes, setBloqueantes] = useState<
    { id: string; nombre: string }[]
  >([]);
  const op = useOperacion();
  const confirmar = useConfirmar();
  const sesiones = useConsulta("sesiones", async (signal) => {
    const r = await apiFetch("/api/perfil/sesiones", { signal });
    await comprobar(r);
    return r.json() as Promise<FilaSesion[]>;
  });
  async function guardar(path: string, method: string, body?: object) {
    const r = await apiFetch(path, {
      method,
      body: body ? JSON.stringify(body) : undefined,
    });
    await comprobar(r);
    const p = (await r.json()) as PerfilTipo;
    setPerfil(p);
    sesion.recargar();
  }
  async function cerrarCuenta() {
    await op.ejecutar(async () => {
      // El endpoint aún no protege al último profesor; esta comprobación evita ofrecer
      // el cierre en ese caso, pero no sustituye la protección transaccional pendiente.
      const equipos = await Promise.all(
        sesion.cursos
          .filter((c) => c.estado === "ACTIVO")
          .map(async (c) => ({ curso: c, miembros: await listarEquipo(c.id) })),
      );
      const cursos = equipos
        .filter(
          ({ miembros }) =>
            miembros.filter(
              (m) => m.rol === "PROFESOR" && m.estado === "ACTIVA",
            ).length === 1 &&
            miembros.some(
              (m) =>
                m.usuario_id === perfil.id &&
                m.rol === "PROFESOR" &&
                m.estado === "ACTIVA",
            ),
        )
        .map(({ curso }) => ({ id: curso.id, nombre: curso.nombre }));
      setBloqueantes(cursos);
      if (cursos.length) return;
      if (
        !(await confirmar({
          titulo: "Cerrar mi cuenta",
          descripcion: `Se cerrará la cuenta ${perfil.email} y todas sus sesiones. No podrás volver a iniciar sesión con ella.`,
          accion: "Cerrar mi cuenta",
          peligro: true,
          escribir: "CERRAR",
        }))
      )
        return;
      const r = await apiFetch("/api/perfil", { method: "DELETE" });
      await comprobar(r);
      window.location.assign("/acceso");
    });
  }
  return (
    <>
      <Cabecera
        titulo="Mi perfil"
        descripcion="Tu identidad, cuenta de GitHub y preferencias de este navegador."
      />
      <Mensajes {...op} />
      <div className="stack">
        <section className="panel">
          <h2>Identidad</h2>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void op.ejecutar(
                () => guardar("/api/perfil", "PATCH", { nombre }),
                "Nombre actualizado.",
              );
            }}
          >
            <label>
              Nombre
              <input
                required
                maxLength={200}
                value={nombre}
                onChange={(e) => setNombre(e.target.value)}
              />
            </label>
            <div>
              <span className="muted">Correo de Google</span>
              <p>{perfil.email}</p>
              <p className="help">
                El correo identifica tu cuenta y no se edita aquí.
              </p>
            </div>
            <div>
              <button className="primary" disabled={op.ocupado}>
                Guardar nombre
              </button>
            </div>
          </form>
        </section>
        <section className="panel">
          <h2>Mi cuenta de GitHub</h2>
          <p>
            Declara tu cuenta personal para el acceso del equipo docente a los
            repositorios. La aplicación comprobará que exista.
          </p>
          <p>
            Cuenta registrada:{" "}
            <strong>
              {perfil.github_login_declarado
                ? `@${perfil.github_login_declarado}`
                : "Sin cuenta declarada"}
            </strong>
          </p>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void op.ejecutar(async () => {
                await guardar("/api/perfil/cuenta-github", "PUT", {
                  login: login.trim(),
                  consiento,
                });
                setConsiento(false);
              }, "Cuenta de GitHub registrada.");
            }}
          >
            <label>
              Nombre de usuario de GitHub
              <input
                required
                value={login}
                onChange={(e) => setLogin(e.target.value)}
                autoComplete="off"
                placeholder="mi-usuario"
              />
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={consiento}
                onChange={(e) => setConsiento(e.target.checked)}
              />
              Declaro mi propia cuenta y doy consentimiento para el acceso
              docente de lectura al código de los repositorios del curso.
            </label>
            <div className="actions">
              <button
                className="primary"
                disabled={op.ocupado || !consiento || !login.trim()}
              >
                Guardar cuenta de GitHub
              </button>
              {perfil.github_login_declarado && (
                <button
                  type="button"
                  className="danger"
                  disabled={op.ocupado}
                  onClick={async () => {
                    if (
                      await confirmar({
                        titulo: "Desvincular mi cuenta de GitHub",
                        descripcion:
                          "Se retirará la cuenta declarada de tu perfil. Esto no elimina repositorios de GitHub.",
                        accion: "Desvincular",
                        peligro: true,
                      })
                    )
                      void op.ejecutar(async () => {
                        await guardar("/api/perfil/cuenta-github", "DELETE");
                        setLogin("");
                      }, "Cuenta desvinculada del perfil.");
                  }}
                >
                  Desvincular
                </button>
              )}
            </div>
          </form>
        </section>
        <section className="panel">
          <h2>Apariencia</h2>
          <Apariencia />
        </section>
        <section className="panel">
          <h2>Sesiones abiertas</h2>
          {sesiones.error && (
            <ErrorCarga error={sesiones.error} reintentar={sesiones.recargar} />
          )}
          {!sesiones.datos ? (
            !sesiones.error && <Cargando />
          ) : (
            <ul className="list-clean">
              {sesiones.datos.map((s) => (
                <li key={s.id}>
                  <strong>
                    {s.es_la_actual ? "Esta sesión" : "Otra sesión"}
                  </strong>
                  <p className="help">{s.agente ?? "Navegador no informado"}</p>
                  <p className="help">Desde {fechaLegible(s.creada_en)}</p>
                </li>
              ))}
            </ul>
          )}
          <button
            disabled={op.ocupado}
            onClick={() =>
              void op.ejecutar(async () => {
                await comprobar(
                  await apiFetch("/api/perfil/sesiones", { method: "DELETE" }),
                );
                sesiones.recargar();
              }, "Las otras sesiones se cerraron. Esta sesión sigue activa.")
            }
          >
            Cerrar las demás sesiones
          </button>
        </section>
        <section className="panel danger-zone">
          <h2>Cerrar mi cuenta</h2>
          <p>
            Esta acción cierra todas tus sesiones e impide volver a entrar con
            esta cuenta.
          </p>
          {bloqueantes.length > 0 && (
            <Aviso tipo="warning">
              Primero incorpora a otro profesor activo en estos cursos:
              <ul>
                {bloqueantes.map((c) => (
                  <li key={c.id}>
                    <Link to={`/cursos/${c.id}/equipo`}>{c.nombre}</Link>
                  </li>
                ))}
              </ul>
            </Aviso>
          )}
          <button
            className="danger"
            disabled={op.ocupado}
            onClick={cerrarCuenta}
          >
            Cerrar mi cuenta
          </button>
        </section>
      </div>
    </>
  );
}
