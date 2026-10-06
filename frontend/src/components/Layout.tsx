import {
  Suspense,
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  Link,
  NavLink,
  Outlet,
  useLocation,
  useParams,
  useNavigate,
} from "react-router-dom";
import { BookOpen, UserRound, Menu, ChevronDown, LogOut } from "lucide-react";
import {
  apiFetch,
  listarCursos,
  obtenerCapacidades,
  obtenerContexto,
  obtenerPerfil,
  type Capacidades,
  type Contexto,
  type Curso,
  type Perfil,
} from "../lib/api";
import { useConsulta } from "../hooks/useConsulta";
import { Aviso, Cargando, ErrorCarga, Estado } from "./ui";

type Sesion = {
  perfil: Perfil;
  cursos: Curso[];
  capacidades: Capacidades | null;
  recargar: () => void;
  agregarCurso: (curso: Curso) => void;
  errorActualizacion: string | null;
};
const SesionContext = createContext<Sesion | null>(null);
export function useSesion() {
  const s = useContext(SesionContext);
  if (!s) throw new Error("La sesión no está disponible");
  return s;
}
type CursoContexto = {
  curso: Curso;
  contexto: Contexto;
  puede: (permiso: string) => boolean;
  recargar: () => void;
};
const CursoContext = createContext<CursoContexto | null>(null);
export function useCurso() {
  const c = useContext(CursoContext);
  if (!c) throw new Error("El curso no está disponible");
  return c;
}

function Icono({ tipo }: { tipo: "cursos" | "cuenta" | "menu" | "salir" }) {
  const Icon =
    tipo === "cursos"
      ? BookOpen
      : tipo === "cuenta"
        ? UserRound
        : tipo === "salir"
          ? LogOut
          : Menu;
  return <Icon size={24} strokeWidth={1.6} aria-hidden="true" />;
}
/** Cierra solo la sesión de este navegador (las demás siguen activas) y
 * vuelve al acceso. Si algo falla, igual se sale: la sesión vencida también
 * termina en /acceso. */
async function cerrarSesionActual() {
  try {
    const r = await apiFetch("/api/perfil/sesiones");
    if (r.ok) {
      const sesiones = (await r.json()) as {
        id: string;
        es_la_actual: boolean;
      }[];
      const actual = sesiones.find((s) => s.es_la_actual);
      if (actual)
        await apiFetch(`/api/perfil/sesiones/${actual.id}`, {
          method: "DELETE",
        });
    }
  } finally {
    window.location.assign("/acceso");
  }
}
function BotonCerrarSesion({ className }: { className?: string }) {
  const [saliendo, setSaliendo] = useState(false);
  return (
    <button
      type="button"
      className={className}
      disabled={saliendo}
      onClick={() => {
        setSaliendo(true);
        void cerrarSesionActual();
      }}
    >
      {className === "nav-salir" && <Icono tipo="salir" />}
      {saliendo ? "Saliendo…" : "Cerrar sesión"}
    </button>
  );
}
export function Publico({ children }: { children?: ReactNode }) {
  return (
    <div className="public-layout">
      <header className="public-header">
        <span className="public-mark">P2</span>
        <strong>Proyecto 2</strong>
        <span className="muted">Gestión docente</span>
      </header>
      <main className="public-main" id="contenido">
        {children ?? <Outlet />}
      </main>
      <footer className="public-footer">
        Canvas y GitHub · Un espacio para el equipo docente
      </footer>
    </div>
  );
}
export function LayoutAutenticado() {
  const ubicacion = useLocation();
  const [vencida, setVencida] = useState(false);
  const consulta = useConsulta("sesion", async (signal) => {
    const perfil = await obtenerPerfil(signal);
    if (!perfil) return null;
    const [cursos, capacidades] = await Promise.all([
      listarCursos(signal),
      obtenerCapacidades(signal).catch(() => null),
    ]);
    return { perfil, cursos, capacidades };
  });
  useEffect(() => {
    function acceso(event: Event) {
      if ((event as CustomEvent<{ status: number }>).detail.status === 401)
        setVencida(true);
    }
    window.addEventListener("pds2:acceso", acceso);
    return () => window.removeEventListener("pds2:acceso", acceso);
  }, []);
  if (vencida || (!consulta.cargando && !consulta.error && !consulta.datos))
    return (
      <Publico>
        <section className="panel">
          <h1>Vuelve a entrar</h1>
          <p>
            Necesitas una sesión activa para consultar tus cursos. Puedes entrar
            nuevamente con tu cuenta de Google autorizada.
          </p>
          <Link
            className="button primary"
            to={`/acceso?destino=${encodeURIComponent(ubicacion.pathname + ubicacion.search)}`}
          >
            Entrar con Google
          </Link>
        </section>
      </Publico>
    );
  if (!consulta.datos)
    return (
      <Publico>
        {consulta.error ? (
          <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
        ) : (
          <Cargando texto="Consultando tu sesión…" />
        )}
      </Publico>
    );
  return (
    <SesionContext.Provider
      value={{
        ...consulta.datos,
        recargar: consulta.recargar,
        errorActualizacion: consulta.error,
        agregarCurso: (nuevo) =>
          consulta.actualizar({
            ...consulta.datos!,
            cursos: [
              ...consulta.datos!.cursos.filter((item) => item.id !== nuevo.id),
              nuevo,
            ],
          }),
      }}
    >
      <Outlet />
    </SesionContext.Provider>
  );
}
const SECCIONES = [
  ["", "Inicio del curso"],
  ["vinculacion", "Configuración"],
  ["personas", "Personas"],
  ["pendientes", "Pendientes"],
  ["tareas", "Tareas"],
  ["seguimiento", "Seguimiento"],
  ["correccion", "Corrección"],
  ["comunicaciones", "Comunicaciones"],
  ["informes", "Informe diario"],
  ["mis-notificaciones", "Mis notificaciones"],
  ["equipo", "Equipo docente"],
  ["ajustes", "Ajustes"],
] as const;
const CAPACIDAD_SECCION: Record<string, string> = {
  seguimiento: "tablero_actividad",
  correccion: "correccion",
  informes: "informe_diario",
  "mis-notificaciones": "mis_notificaciones",
  comunicaciones: "comunicaciones_automaticas",
};
function EnlacesCurso({
  curso,
  cerrar,
}: {
  curso: Curso;
  cerrar?: () => void;
}) {
  const { pathname } = useLocation();
  const { capacidades } = useSesion();
  const contexto = useContext(CursoContext);
  return (
    <nav className="course-links" aria-label="Secciones del curso">
      {SECCIONES.filter(
        ([ruta]) =>
          (!CAPACIDAD_SECCION[ruta] ||
            capacidades?.banderas.includes(CAPACIDAD_SECCION[ruta])) &&
          (!["vinculacion", "ajustes"].includes(ruta) ||
            contexto?.puede("curso.administrar")),
      ).map(([ruta, nombre]) => (
        <NavLink
          key={ruta}
          onClick={cerrar}
          end={!ruta}
          to={`/cursos/${curso.id}${ruta ? `/${ruta}` : ""}`}
          aria-current={
            ruta === "vinculacion" && pathname.endsWith("/verificacion")
              ? "page"
              : undefined
          }
        >
          {nombre}
        </NavLink>
      ))}
    </nav>
  );
}
export function Estructura({
  curso,
  children,
}: {
  curso?: Curso;
  children?: ReactNode;
}) {
  const { perfil, cursos, errorActualizacion, recargar } = useSesion();
  const contextoCurso = useContext(CursoContext);
  const navegar = useNavigate();
  const { pathname } = useLocation();
  const menu = useRef<HTMLDialogElement>(null);
  const nombreSeccion = pathname.endsWith("/verificacion")
    ? "Verificación"
    : curso
      ? (SECCIONES.find(
          ([ruta]) => ruta && pathname.includes(`/${ruta}`),
        )?.[1] ?? "Inicio del curso")
      : pathname === "/perfil"
        ? "Mi perfil"
        : "Mis cursos";
  function cerrarMenu() {
    menu.current?.close();
  }
  useEffect(() => {
    cerrarMenu();
    window.scrollTo(0, 0);
    document.getElementById("contenido")?.focus({ preventScroll: true });
  }, [pathname]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <nav className="global-nav" aria-label="Navegación global">
        <Link className="brand" to="/cursos">
          <strong>P2</strong>Proyecto 2
        </Link>
        <NavLink to="/cursos">
          <Icono tipo="cursos" />
          Cursos
        </NavLink>
        <NavLink className="nav-bottom" to="/perfil">
          <Icono tipo="cuenta" />
          Cuenta
        </NavLink>
        <BotonCerrarSesion className="nav-salir" />
      </nav>
      <header className="shell-header">
        <button
          className="mobile-toggle"
          aria-label="Abrir navegación"
          onClick={() => menu.current?.showModal()}
        >
          <Icono tipo="menu" />
        </button>
        <nav className="breadcrumbs" aria-label="Ubicación">
          <ol>
            <li>
              <Link to="/cursos">Cursos</Link>
            </li>
            {curso && (
              <li>
                <Link to={`/cursos/${curso.id}`}>
                  {curso.codigo} · {curso.periodo}
                </Link>
              </li>
            )}
            {(curso || pathname !== "/cursos") && (
              <li aria-current="page">{nombreSeccion}</li>
            )}
          </ol>
        </nav>
        <Link className="identity" to="/perfil">
          <span className="avatar" aria-hidden="true">
            {perfil.nombre.trim().slice(0, 1).toUpperCase()}
          </span>
          <span className="identity-name">
            {perfil.nombre}
            {contextoCurso?.contexto.es_via_compartida && (
              <span className="help"> · Vía de acceso compartida</span>
            )}
          </span>
          <ChevronDown size={14} aria-hidden="true" />
          <span className="sr-only"> · Mi perfil</span>
        </Link>
      </header>
      <div className={`workspace ${curso ? "" : "no-course"}`}>
        {curso && (
          <aside className="course-nav">
            <div className="course-nav-title">
              <strong>{curso.nombre}</strong>
              <span className="muted">{curso.periodo}</span>
              <label className="course-switcher">
                <span className="sr-only">Cambiar de curso</span>
                <select
                  value={curso.id}
                  onChange={(event) => navegar(`/cursos/${event.target.value}`)}
                >
                  {cursos.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.codigo} · {item.periodo}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <EnlacesCurso curso={curso} />
            <p className="course-nav-note">
              Fechas del curso
              <br />
              {curso.zona_horaria}
            </p>
          </aside>
        )}
        <main className="main-content" id="contenido" tabIndex={-1}>
          {errorActualizacion && (
            <Aviso tipo="warning">
              <strong>No pudimos actualizar tus cursos.</strong>
              <p>
                Se conserva la última información disponible.{" "}
                {errorActualizacion}
              </p>
              <button onClick={recargar}>Actualizar mis cursos</button>
            </Aviso>
          )}
          <Suspense fallback={<Cargando texto="Cargando pantalla…" />}>
            {children ?? <Outlet />}
          </Suspense>
        </main>
      </div>
      <dialog className="mobile-dialog" ref={menu} aria-label="Navegación">
        <div className="panel-header">
          <h2>Proyecto 2</h2>
          <button autoFocus onClick={cerrarMenu}>
            Cerrar
          </button>
        </div>
        <div className="actions">
          <Link to="/cursos" onClick={cerrarMenu}>
            Mis cursos
          </Link>
          <Link to="/perfil" onClick={cerrarMenu}>
            Mi perfil
          </Link>
          <BotonCerrarSesion />
        </div>
        {curso && (
          <>
            <hr />
            <h3>{curso.nombre}</h3>
            <label>
              Cambiar de curso
              <select
                value={curso.id}
                onChange={(event) => {
                  cerrarMenu();
                  navegar(`/cursos/${event.target.value}`);
                }}
              >
                {cursos.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.codigo} · {item.periodo}
                  </option>
                ))}
              </select>
            </label>
            <EnlacesCurso curso={curso} cerrar={cerrarMenu} />
          </>
        )}
      </dialog>
    </div>
  );
}
export function LayoutCurso() {
  const { cursoId = "" } = useParams();
  const sesion = useSesion();
  const curso = sesion.cursos.find((c) => c.id === cursoId);
  const consulta = useConsulta(
    `contexto-${cursoId}`,
    (signal) => obtenerContexto(cursoId, signal),
    60_000,
  );
  const [revalidando, setRevalidando] = useState(false);
  useEffect(() => {
    function refrescar() {
      consulta.recargar();
    }
    function acceso(event: Event) {
      const { status, path } = (
        event as CustomEvent<{ status: number; path: string }>
      ).detail;
      if (
        status === 403 &&
        path.includes(`/cursos/${cursoId}/`) &&
        !path.endsWith("/contexto")
      ) {
        setRevalidando(true);
        consulta.recargar();
      }
    }
    window.addEventListener("focus", refrescar);
    window.addEventListener("pds2:acceso", acceso);
    return () => {
      window.removeEventListener("focus", refrescar);
      window.removeEventListener("pds2:acceso", acceso);
    };
  }, [cursoId, consulta.recargar]);
  useEffect(() => {
    if (!consulta.cargando) setRevalidando(false);
  }, [consulta.cargando]);
  if (!curso)
    return (
      <Estructura>
        <h1>Curso no disponible</h1>
        <Aviso tipo="warning">
          Este curso no aparece entre tus cursos. Puede que tu acceso haya
          cambiado.
        </Aviso>
        <Link className="button" to="/cursos">
          Volver a mis cursos
        </Link>
      </Estructura>
    );
  if (consulta.error || !consulta.datos)
    return (
      <Estructura curso={curso}>
        {curso.estado === "ARCHIVADO" && (
          <Aviso tipo="warning">
            Curso archivado: sólo lectura. Los procesos y comunicaciones están
            pausados.
          </Aviso>
        )}
        {consulta.error ? (
          <ErrorCarga error={consulta.error} reintentar={consulta.recargar} />
        ) : (
          <Cargando texto="Consultando tus permisos en este curso…" />
        )}
      </Estructura>
    );
  return (
    <CursoContext.Provider
      value={{
        curso,
        contexto: consulta.datos,
        puede: (permiso) =>
          !revalidando && consulta.datos!.permisos_efectivos.includes(permiso),
        recargar: () => {
          consulta.recargar();
          sesion.recargar();
        },
      }}
    >
      <Estructura curso={curso}>
        {revalidando && <Aviso>Actualizando tus permisos…</Aviso>}
        {curso.estado === "ARCHIVADO" && (
          <Aviso tipo="warning">
            Curso archivado: sólo lectura. Los procesos y comunicaciones están
            pausados.
          </Aviso>
        )}
        <Outlet key={cursoId} />
      </Estructura>
    </CursoContext.Provider>
  );
}
export function SinPermiso({
  children = "Solo un profesor puede realizar esta acción.",
}: {
  children?: ReactNode;
}) {
  return <p className="help">{children}</p>;
}
export function EstadoCurso({ curso }: { curso: Curso }) {
  return <Estado valor={curso.estado} />;
}

/** La API es la fuente de alcance; una URL directa conserva las mismas guardas. */
export function AccesoArea({
  capacidad,
  permiso,
  children,
}: {
  capacidad?: string;
  permiso?: string;
  children: ReactNode;
}) {
  const { capacidades, recargar } = useSesion();
  const { puede, curso } = useCurso();
  if (permiso && !puede(permiso))
    return (
      <section className="panel">
        <h1>Permiso insuficiente</h1>
        <Aviso tipo="warning">
          Esta configuración está reservada a los profesores del curso. Puedes
          seguir consultando las tareas y personas disponibles.
        </Aviso>
        <Link to={`/cursos/${curso.id}`}>Volver al curso</Link>
      </section>
    );
  if (capacidad && !capacidades)
    return (
      <section className="panel">
        <h1>No pudimos comprobar la disponibilidad</h1>
        <Aviso tipo="warning">
          No se pudo consultar qué funciones están disponibles. Tus datos del
          curso siguen conservados.
        </Aviso>
        <button onClick={recargar}>Intentar nuevamente</button>
      </section>
    );
  if (capacidad && !capacidades?.banderas.includes(capacidad))
    return (
      <section className="panel">
        <h1>Área no disponible</h1>
        <p>Esta función todavía no está habilitada en esta instalación.</p>
        <Link to={`/cursos/${curso.id}`}>Volver al curso</Link>
      </section>
    );
  return <>{children}</>;
}
