import {
  createContext,
  useContext,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { mensajeError } from "../lib/errores";
import {
  DEFAULT_THEME,
  THEME_LABELS,
  THEMES,
  aplicarTema,
  restablecerTema,
  validarTema,
} from "../config/theme";

export function Cabecera({
  titulo,
  descripcion,
  acciones,
}: {
  titulo: string;
  descripcion?: string;
  acciones?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        <h1>{titulo}</h1>
        {descripcion && <p>{descripcion}</p>}
      </div>
      {acciones && <div className="actions">{acciones}</div>}
    </header>
  );
}
export function Aviso({
  children,
  tipo = "info",
}: {
  children: ReactNode;
  tipo?: "info" | "success" | "warning" | "error";
}) {
  return (
    <div
      className={`notice ${tipo}`}
      role={tipo === "error" ? "alert" : "status"}
    >
      {children}
    </div>
  );
}
export function Cargando({
  texto = "Cargando información…",
}: {
  texto?: string;
}) {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      {texto}
    </div>
  );
}
export function ErrorCarga({
  error,
  reintentar,
}: {
  error: unknown;
  reintentar?: () => void;
}) {
  return (
    <Aviso tipo="error">
      <div>{mensajeError(error)}</div>
      {reintentar && (
        <button className="quiet" onClick={reintentar}>
          Intentar nuevamente
        </button>
      )}
    </Aviso>
  );
}
export function Mensajes({
  error,
  mensaje,
}: {
  error: string | null;
  mensaje: string | null;
}) {
  return (
    <>
      {error && <ErrorCarga error={error} />}
      {mensaje && <Aviso tipo="success">{mensaje}</Aviso>}
    </>
  );
}
export function Vacio({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}
export function Tabla({
  children,
  etiqueta,
  fija = true,
}: {
  children: ReactNode;
  etiqueta: string;
  fija?: boolean;
}) {
  return (
    <>
      <div
        className={`table-wrap ${fija ? "sticky" : ""}`}
        role="region"
        aria-label={etiqueta}
        tabIndex={0}
      >
        {children}
      </div>
      <p className="table-hint">
        Si hay más columnas, desplaza la tabla horizontalmente.
      </p>
    </>
  );
}
const ETIQUETAS: Record<string, string> = {
  ACTIVO: "Activo",
  ACTIVA: "Activa",
  BORRADOR: "Borrador",
  VINCULANDO: "En configuración",
  ARCHIVADO: "Archivado",
  RETIRADA: "Retirada",
  RETIRADO: "Retirado",
  INACTIVO: "Inactivo",
  INACTIVA: "Inactiva",
  PROFESOR: "Profesor",
  AYUDANTE: "Ayudante",
  CANVAS_DESVINCULADO: "Canvas requiere atención",
  GITHUB_DESVINCULADO: "GitHub requiere atención",
  CORRECTO: "Correcto",
  ADVERTENCIA: "Advertencia",
  BLOQUEANTE: "Bloqueante",
  NO_VERIFICADO: "Sin verificar",
  VERIFICADO_A_MANO: "Verificado manualmente",
  VALIDA: "Válida",
  INVALIDA: "Inválida",
  PENDIENTE: "Pendiente",
  VIGENTE: "Cuenta verificada",
  SIN_DATO: "Sin cuenta de GitHub",
  RECIBIDO: "Por validar",
  NO_RESUELTO: "No se pudo validar",
  NO_EXISTE: "Cuenta no encontrada",
  ES_ORGANIZACION: "Es una organización",
  EN_CONFLICTO: "Cuenta en conflicto",
  INVALIDADO: "Requiere revisión",
  SUPERSEDIDO: "Asociación anterior",
  NO_CREADA: "Sin tarea de registro",
  ABIERTA: "Registro abierto",
  CREADA: "Registro creado",
  ALTERADA: "Registro modificado en Canvas",
  DESAPARECIDA: "Registro no disponible",
  RESTAURADA: "Registro restaurado",
  PUBLICADA: "Publicada",
  CERRADA: "Cerrada",
  SE_APLICARIA: "Lista para aplicar",
  APLICADA: "Aplicada",
  FALLIDA: "No aplicada",
  RENOMBRADO: "Cuenta renombrada",
  CUENTA_ELIMINADA: "Cuenta eliminada",
  LOGIN_REASIGNADO: "Nombre de cuenta reasignado",
  ESTUDIANTE_RETIRADO: "Estudiante retirado",
  CUENTA_NO_ELEGIBLE: "Cuenta no elegible",
  EXPIRADA: "Vencida",
  ACEPTADA: "Aceptada",
  REVOCADA: "Revocada",
  ERROR: "Requiere atención",
  SINCRONIZADA: "Sincronizada",
  PARCIAL: "Sincronización parcial",
  TRUNCADA: "Sincronización incompleta",
};
export function etiqueta(valor: string | null | undefined) {
  if (!valor) return "Sin información";
  return (
    ETIQUETAS[valor] ??
    valor.charAt(0).toUpperCase() +
      valor.slice(1).toLowerCase().replaceAll("_", " ")
  );
}
export function Estado({ valor, texto }: { valor: string; texto?: string }) {
  const tipo = [
    "CORRECTO",
    "ACTIVO",
    "ACTIVA",
    "VALIDA",
    "VIGENTE",
    "OPERATIVO",
    "APLICADA",
    "COMPLETADO",
  ].includes(valor)
    ? "success"
    : [
          "BLOQUEANTE",
          "ERROR_PERMANENTE",
          "BLOQUEADO",
          "INACCESIBLE",
          "ERROR",
          "INVALIDA",
          "EN_CONFLICTO",
        ].includes(valor)
      ? "error"
      : [
            "DEGRADADO",
            "ADVERTENCIA",
            "ESPERANDO_INFORMACION",
            "ESPERANDO_LIMITE",
            "SIN_DATO",
            "INVALIDADO",
            "ERROR_TRANSITORIO",
            "ATENCION",
          ].includes(valor)
        ? "warning"
        : ["VERIFICADO_A_MANO", "CREANDO", "VINCULANDO", "RECIBIDO"].includes(
              valor,
            )
          ? "info"
          : "neutral";
  return <span className={`status ${tipo}`}>{texto ?? etiqueta(valor)}</span>;
}
export function Paginacion({
  total,
  pagina,
  cambiar,
  tamano = 20,
}: {
  total: number;
  pagina: number;
  cambiar: (pagina: number) => void;
  tamano?: number;
}) {
  const paginas = Math.max(1, Math.ceil(total / tamano));
  return (
    <div className="pagination">
      <span>
        {total} resultados · Página {pagina} de {paginas}
      </span>
      <button disabled={pagina <= 1} onClick={() => cambiar(pagina - 1)}>
        Anterior
      </button>
      <button disabled={pagina >= paginas} onClick={() => cambiar(pagina + 1)}>
        Siguiente
      </button>
    </div>
  );
}
export function Apariencia() {
  const [tema, setTema] = useState(() =>
    validarTema(document.documentElement.dataset.theme),
  );
  return (
    <div className="form-stack">
      <label>
        Apariencia
        <select
          value={tema}
          onChange={(e) => setTema(aplicarTema(e.target.value, true))}
        >
          {THEMES.map((t) => (
            <option key={t} value={t}>
              {THEME_LABELS[t]}
            </option>
          ))}
        </select>
      </label>
      <p className="help">
        Solo cambia los colores en este navegador. Tu trabajo se conserva.
        Predeterminado: {THEME_LABELS[DEFAULT_THEME]}.
      </p>
      <div>
        <button onClick={() => setTema(restablecerTema())}>
          Restablecer apariencia
        </button>
      </div>
    </div>
  );
}
export interface Confirmacion {
  titulo: string;
  descripcion: string;
  accion?: string;
  escribir?: string;
  peligro?: boolean;
}
const ContextoConfirmar = createContext<
  (datos: Confirmacion) => Promise<boolean>
>(() => Promise.resolve(false));
export function useConfirmar() {
  return useContext(ContextoConfirmar);
}
export function Confirmaciones({ children }: { children: ReactNode }) {
  const [datos, setDatos] = useState<Confirmacion | null>(null);
  const [texto, setTexto] = useState("");
  const resolver = useRef<(valor: boolean) => void>();
  const dialogo = useRef<HTMLDialogElement>(null);
  const id = useId();
  useEffect(() => {
    if (datos) {
      dialogo.current?.showModal();
    }
  }, [datos]);
  function cerrar(valor: boolean) {
    dialogo.current?.close();
    resolver.current?.(valor);
    resolver.current = undefined;
    setDatos(null);
  }
  return (
    <ContextoConfirmar.Provider
      value={(config) =>
        new Promise((resolve) => {
          resolver.current?.(false);
          resolver.current = resolve;
          setTexto("");
          setDatos(config);
        })
      }
    >
      {children}
      <dialog
        ref={dialogo}
        aria-labelledby={`${id}-titulo`}
        aria-describedby={`${id}-descripcion`}
        onCancel={(e) => {
          e.preventDefault();
          cerrar(false);
        }}
      >
        <h2 id={`${id}-titulo`}>{datos?.titulo}</h2>
        <p id={`${id}-descripcion`}>{datos?.descripcion}</p>
        {datos?.escribir && (
          <label>
            Escribe «{datos.escribir}» para confirmar
            <input
              autoComplete="off"
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
            />
          </label>
        )}
        <div className="actions end">
          <button autoFocus onClick={() => cerrar(false)}>
            Cancelar
          </button>
          <button
            className={datos?.peligro ? "danger" : "primary"}
            disabled={Boolean(datos?.escribir && texto !== datos.escribir)}
            onClick={() => cerrar(true)}
          >
            {datos?.accion ?? "Confirmar"}
          </button>
        </div>
      </dialog>
    </ContextoConfirmar.Provider>
  );
}
