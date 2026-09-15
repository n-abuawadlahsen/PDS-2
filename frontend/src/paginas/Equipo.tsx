import { useState } from "react";
import {
  apiFetch,
  invitarMiembro,
  listarEquipo,
  reincorporarMiembro,
  retirarMiembro,
  type Miembro,
} from "../lib/api";
import {
  PERMISOS_AYUDANTE_POR_DEFECTO,
  PERMISOS_CONCEDIBLES,
} from "../lib/permisos";
import { comprobar } from "../lib/errores";
import { useCurso } from "../components/Layout";
import {
  Cabecera,
  Cargando,
  ErrorCarga,
  Estado,
  Mensajes,
  Tabla,
  etiqueta,
  useConfirmar,
} from "../components/ui";
import { useConsulta, useOperacion } from "../hooks/useConsulta";
import { fechaLegible } from "../lib/textosTarea";
interface Invitacion {
  id: string;
  email: string;
  rol: string;
  estado: string;
  expira_en: string;
  enlace: string | null;
  correo_estado: string | null;
  correo_motivo: string | null;
  reenvios_restantes: number;
}
const PERMISOS_PARCIAL = [
  "tarea.administrar",
  "mapeo.editar",
  "comunicacion.enviar",
];
function Permisos({
  valores,
  cambiar,
}: {
  valores: string[];
  cambiar: (v: string[]) => void;
}) {
  return (
    <fieldset>
      <legend>Permisos del ayudante</legend>
      <p className="help">
        Siempre puede consultar el curso. Administrar el curso y el equipo
        corresponde a profesores.
      </p>
      {PERMISOS_CONCEDIBLES.filter((p) =>
        PERMISOS_PARCIAL.includes(p.clave),
      ).map((p) => (
        <label className="check" key={p.clave}>
          <input
            type="checkbox"
            checked={valores.includes(p.clave)}
            onChange={(e) =>
              cambiar(
                e.target.checked
                  ? [...valores, p.clave]
                  : valores.filter((v) => v !== p.clave),
              )
            }
          />
          <span>
            {p.etiqueta}
            <span className="help"> · {p.descripcion}</span>
          </span>
        </label>
      ))}
      <p className="help">
        Otros permisos ya asignados se conservan al editar estos controles.
      </p>
    </fieldset>
  );
}
export function Equipo() {
  const { curso, puede, recargar } = useCurso();
  const administra = puede("equipo.administrar");
  const c = useConsulta(
    `equipo-${curso.id}`,
    (signal) => listarEquipo(curso.id, signal),
    10000,
  );
  const op = useOperacion();
  const confirmar = useConfirmar();
  const [invitando, setInvitando] = useState(false);
  const [email, setEmail] = useState("");
  const [rol, setRol] = useState<"PROFESOR" | "AYUDANTE">("AYUDANTE");
  const [permisos, setPermisos] = useState<string[]>(
    PERMISOS_AYUDANTE_POR_DEFECTO,
  );
  const [editando, setEditando] = useState<Miembro | null>(null);
  const invitaciones = useConsulta(
    `invitaciones-${curso.id}-${administra}`,
    async (signal) => {
      if (!administra) return [] as Invitacion[];
      const r = await apiFetch(`/api/cursos/${curso.id}/equipo/invitaciones`, {
        signal,
        cache: "no-store",
      });
      await comprobar(r);
      return r.json() as Promise<Invitacion[]>;
    },
    10000,
  );
  async function mutar(path: string, method: string, body?: object) {
    const r = await apiFetch(path, {
      method,
      body: body ? JSON.stringify(body) : undefined,
    });
    await comprobar(r);
    c.recargar();
    invitaciones.recargar();
    recargar();
  }
  return (
    <>
      <Cabecera
        titulo="Equipo docente"
        descripcion="Profesores y ayudantes del curso, con permisos específicos para sus tareas."
        acciones={
          administra &&
          !invitando && (
            <button className="primary" onClick={() => setInvitando(true)}>
              Incorporar integrante
            </button>
          )
        }
      />
      <Mensajes {...op} />
      <p className="help">
        Todos los profesores tienen los mismos permisos. Un curso activo siempre
        debe conservar al menos un profesor activo.
      </p>
      {c.error && <ErrorCarga error={c.error} reintentar={c.recargar} />}
      {!c.datos ? (
        !c.error && <Cargando />
      ) : (
        <section className="panel">
          <h2>Integrantes</h2>
          <Tabla etiqueta="Equipo docente del curso">
            <table>
              <thead>
                <tr>
                  <th scope="col">Persona</th>
                  <th scope="col">Rol</th>
                  <th scope="col">Estado</th>
                  <th scope="col">GitHub</th>
                  <th scope="col">Permisos</th>
                  <th scope="col">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {c.datos.map((m) => (
                  <tr key={m.membresia_id}>
                    <td>
                      <strong>{m.nombre}</strong>
                      <p className="help">{m.email}</p>
                    </td>
                    <td>{etiqueta(m.rol)}</td>
                    <td>
                      <Estado valor={m.estado} />
                      {m.retirada_en && (
                        <p className="help">
                          Retiro:{" "}
                          {fechaLegible(m.retirada_en, curso.zona_horaria)}
                        </p>
                      )}
                    </td>
                    <td>
                      <p>{m.github_login ?? "Sin cuenta declarada"}</p>
                      {m.github_estado && <Estado valor={m.github_estado} />}
                      {m.github_error && (
                        <p className="help">{m.github_error}</p>
                      )}
                      {administra &&
                        m.github_login &&
                        m.estado === "ACTIVA" && (
                          <button
                            disabled={op.ocupado}
                            onClick={() =>
                              void op.ejecutar(
                                () =>
                                  mutar(
                                    `/api/cursos/${curso.id}/equipo/${m.membresia_id}/github/reintentar`,
                                    "POST",
                                  ),
                                "Actualización de acceso solicitada. Revisa el estado en unos momentos.",
                              )
                            }
                          >
                            Actualizar acceso GitHub
                          </button>
                        )}
                    </td>
                    <td>
                      {m.rol === "PROFESOR" ? (
                        "Administración completa"
                      ) : (
                        <>
                          {PERMISOS_CONCEDIBLES.filter(
                            (p) =>
                              m.permisos.includes(p.clave) &&
                              PERMISOS_PARCIAL.includes(p.clave),
                          )
                            .map((p) => p.etiqueta)
                            .join(", ") || "Consulta del curso"}
                          {m.permisos.some(
                            (p) => !PERMISOS_PARCIAL.includes(p),
                          ) && (
                            <p className="help">
                              Otros permisos asignados se conservan.
                            </p>
                          )}
                        </>
                      )}
                    </td>
                    <td>
                      {administra && (
                        <div className="actions">
                          {m.estado === "ACTIVA" ? (
                            <>
                              <button
                                disabled={op.ocupado}
                                onClick={() =>
                                  setEditando({
                                    ...m,
                                    permisos: [...m.permisos],
                                  })
                                }
                              >
                                Editar acceso
                              </button>
                              <button
                                className="danger"
                                disabled={op.ocupado}
                                onClick={async () => {
                                  if (
                                    await confirmar({
                                      titulo: `Retirar a ${m.nombre}`,
                                      descripcion: `Perderá el acceso al curso ${curso.nombre}. Se solicitará retirar su acceso docente a GitHub.`,
                                      accion: "Retirar del curso",
                                      peligro: true,
                                    })
                                  )
                                    void op.ejecutar(async () => {
                                      await comprobar(
                                        await retirarMiembro(
                                          curso.id,
                                          m.membresia_id,
                                        ),
                                      );
                                      c.recargar();
                                      recargar();
                                    }, "Integrante retirado del curso. La revocación de GitHub se procesará en segundo plano.");
                                }}
                              >
                                Retirar
                              </button>
                            </>
                          ) : (
                            <button
                              disabled={op.ocupado}
                              onClick={async () => {
                                if (
                                  await confirmar({
                                    titulo: `Reincorporar a ${m.nombre}`,
                                    descripcion:
                                      "Recuperará su pertenencia al curso con los permisos registrados.",
                                    accion: "Reincorporar",
                                  })
                                )
                                  void op.ejecutar(async () => {
                                    await comprobar(
                                      await reincorporarMiembro(
                                        curso.id,
                                        m.membresia_id,
                                        m.rol === "PROFESOR" ? [] : m.permisos,
                                      ),
                                    );
                                    c.recargar();
                                    recargar();
                                  }, "Integrante reincorporado.");
                              }}
                            >
                              Reincorporar
                            </button>
                          )}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Tabla>
        </section>
      )}
      {editando && administra && (
        <section className="panel">
          <h2>Acceso de {editando.nombre}</h2>
          <form
            className="form-stack"
            onSubmit={async (e) => {
              e.preventDefault();
              const original = c.datos?.find(
                (m) => m.membresia_id === editando.membresia_id,
              );
              if (!original) return;
              if (
                !(await confirmar({
                  titulo: `Cambiar acceso de ${editando.nombre}`,
                  descripcion: `Se aplicará el rol ${etiqueta(editando.rol)} y sus permisos en el curso. El cambio tendrá efecto en las siguientes solicitudes.`,
                  accion: "Guardar acceso",
                }))
              )
                return;
              void op.ejecutar(async () => {
                const base = `/api/cursos/${curso.id}/miembros/${editando.membresia_id}`;
                if (original.rol !== editando.rol)
                  await mutar(`${base}/rol`, "PATCH", {
                    rol: editando.rol,
                    permisos:
                      editando.rol === "PROFESOR" ? [] : editando.permisos,
                  });
                else if (editando.rol === "AYUDANTE")
                  await mutar(`${base}/permisos`, "PATCH", {
                    permisos: editando.permisos,
                  });
                setEditando(null);
              }, "Acceso actualizado.");
            }}
          >
            <label>
              Rol
              <select
                value={editando.rol}
                onChange={(e) =>
                  setEditando({
                    ...editando,
                    rol: e.target.value as Miembro["rol"],
                    permisos:
                      editando.rol === "PROFESOR"
                        ? [...PERMISOS_AYUDANTE_POR_DEFECTO]
                        : editando.permisos,
                  })
                }
              >
                <option value="AYUDANTE">Ayudante</option>
                <option value="PROFESOR">Profesor</option>
              </select>
            </label>
            {editando.rol === "AYUDANTE" && (
              <Permisos
                valores={editando.permisos}
                cambiar={(p) => setEditando({ ...editando, permisos: p })}
              />
            )}
            <div className="actions">
              <button className="primary" disabled={op.ocupado}>
                Guardar acceso
              </button>
              <button
                type="button"
                disabled={op.ocupado}
                onClick={() => setEditando(null)}
              >
                Cancelar
              </button>
            </div>
          </form>
        </section>
      )}
      {invitando && administra && (
        <section className="panel">
          <h2>Incorporar integrante</h2>
          <p className="help">
            La invitación quedará disponible para compartir. El correo se
            procesa en segundo plano y su estado aparece en la lista.
          </p>
          <form
            className="form-stack"
            onSubmit={(e) => {
              e.preventDefault();
              void op.ejecutar(async () => {
                const r = await invitarMiembro(curso.id, {
                  email,
                  rol,
                  permisos: rol === "PROFESOR" ? [] : permisos,
                });
                await comprobar(r);
                invitaciones.recargar();
                setInvitando(false);
                setEmail("");
              }, "Invitación creada. Puedes copiar el enlace y consultar el estado del correo.");
            }}
          >
            <label>
              Correo personal Gmail
              <input
                required
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
              />
            </label>
            <label>
              Rol
              <select
                value={rol}
                onChange={(e) => setRol(e.target.value as typeof rol)}
              >
                <option value="AYUDANTE">Ayudante</option>
                <option value="PROFESOR">Profesor</option>
              </select>
            </label>
            {rol === "AYUDANTE" ? (
              <Permisos valores={permisos} cambiar={setPermisos} />
            ) : (
              <p>
                El profesor podrá administrar el curso y el equipo, con los
                mismos permisos que los demás profesores.
              </p>
            )}
            <div className="actions">
              <button className="primary" disabled={op.ocupado}>
                {op.ocupado ? "Registrando…" : "Registrar invitación"}
              </button>
              <button
                type="button"
                disabled={op.ocupado}
                onClick={() => setInvitando(false)}
              >
                Cancelar
              </button>
            </div>
          </form>
        </section>
      )}
      {administra && (
        <section className="panel">
          <h2>Invitaciones</h2>
          {invitaciones.error && (
            <ErrorCarga
              error={invitaciones.error}
              reintentar={invitaciones.recargar}
            />
          )}
          {!invitaciones.datos ? (
            <Cargando />
          ) : invitaciones.datos.length === 0 ? (
            <p>No hay invitaciones registradas.</p>
          ) : (
            <ul className="list-clean">
              {invitaciones.datos.map((i) => (
                <li key={i.id}>
                  <strong>{i.email}</strong> · {etiqueta(i.rol)} ·{" "}
                  <Estado valor={i.estado} />
                  <p className="help">
                    Vence: {fechaLegible(i.expira_en, curso.zona_horaria)}
                  </p>
                  <p>{textoCorreo(i)}</p>
                  {i.enlace && (
                    <label>
                      Enlace de invitación para {i.email}
                      <input
                        readOnly
                        value={i.enlace}
                        onFocus={(e) => e.target.select()}
                      />
                    </label>
                  )}
                  <div className="actions">
                    {i.enlace && (
                      <button
                        onClick={() =>
                          void op.ejecutar(async () => {
                            if (!navigator.clipboard)
                              throw new Error(
                                "Selecciona el enlace y cópialo desde el campo.",
                              );
                            await navigator.clipboard.writeText(i.enlace!);
                          }, "Enlace copiado.")
                        }
                      >
                        Copiar enlace
                      </button>
                    )}
                    {(i.estado === "PENDIENTE" || i.estado === "EXPIRADA") && (
                      <>
                        <button
                          disabled={op.ocupado || i.reenvios_restantes <= 0}
                          onClick={async () => {
                            if (
                              await confirmar({
                                titulo: "Reenviar invitación",
                                descripcion: `Se invalidará el enlace anterior de ${i.email} y se generará uno nuevo.`,
                                accion: "Reenviar",
                              })
                            )
                              void op.ejecutar(
                                () =>
                                  mutar(
                                    `/api/cursos/${curso.id}/equipo/invitaciones/${i.id}/reenviar`,
                                    "POST",
                                  ),
                                "Se generó una nueva invitación. El enlace anterior dejó de ser válido.",
                              );
                          }}
                        >
                          Reenviar invitación
                        </button>
                        <button
                          className="danger"
                          disabled={op.ocupado}
                          onClick={async () => {
                            if (
                              await confirmar({
                                titulo: "Revocar invitación",
                                descripcion: `La invitación para ${i.email} dejará de ser válida.`,
                                accion: "Revocar",
                                peligro: true,
                              })
                            )
                              void op.ejecutar(
                                () =>
                                  mutar(
                                    `/api/cursos/${curso.id}/equipo/invitaciones/${i.id}`,
                                    "DELETE",
                                  ),
                                "Invitación revocada.",
                              );
                          }}
                        >
                          Revocar invitación
                        </button>
                      </>
                    )}
                  </div>
                  {(i.estado === "PENDIENTE" || i.estado === "EXPIRADA") && (
                    <p className="help">
                      Reenvíos disponibles: {i.reenvios_restantes} de 3.
                    </p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </>
  );
}

function textoCorreo(i: Invitacion): string {
  const motivos: Record<string, string> = {
    COMUNICACIONES_PAUSADAS:
      "El correo está pausado. Puedes compartir el enlace directamente.",
    CORREO_SIN_CONFIGURAR:
      "Falta configurar el correo del servicio. Puedes compartir el enlace.",
    DESTINATARIO_NO_PERMITIDO:
      "El envío a esta dirección está restringido por la configuración del servicio.",
    CUOTA_AGOTADA:
      "El correo quedó pendiente para el próximo día por el límite de envíos.",
    SIMULADO_LOCAL: "Prueba local: no se envió correo real.",
    ENLACE_ANTIGUO:
      "Invitación anterior a esta actualización. Usa Reenviar para obtener un enlace nuevo.",
    ENLACE_NO_RECUPERABLE:
      "No se pudo recuperar el enlace. Reenvía la invitación para generar otro.",
    ENVIO_INCIERTO:
      "No pudimos confirmar el envío. Comparte el enlace o reenvía la invitación.",
    INVITACION_NO_VIGENTE: "El envío pendiente fue cancelado.",
  };
  if (i.correo_motivo) return motivos[i.correo_motivo] ?? i.correo_motivo;
  if (i.correo_estado === "ENVIADO")
    return "Correo aceptado por el proveedor. Revisa también la carpeta de spam.";
  if (i.correo_estado === "REQUIERE_ATENCION" || i.correo_estado === "FALLIDO")
    return "No se pudo enviar el correo. Puedes compartir el enlace.";
  if (i.correo_estado === "CADUCADO")
    return "El envío caducó junto con la invitación.";
  return "Correo pendiente de envío.";
}
