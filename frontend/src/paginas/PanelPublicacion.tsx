import { useEffect, useRef, useState } from "react";
import {
  accionPublicacion,
  publicarCorreccion,
  type PantallaCorreccion,
  type ResultadoPublicacion,
} from "../lib/api";
import { fechaFinal } from "../lib/apiFinal";
import { useCurso } from "../components/Layout";
import { Aviso, Mensajes } from "../components/ui";
import { useOperacion } from "../hooks/useConsulta";

export function PanelPublicacion({
  cursoId,
  entregaId,
  sujetoId,
  datos,
  onCambio,
  cambiosPendientes = false,
}: {
  cursoId: string;
  entregaId: string;
  sujetoId: string;
  datos: PantallaCorreccion;
  onCambio: () => void;
  cambiosPendientes?: boolean;
}) {
  const { curso } = useCurso();
  const [abierto, setAbierto] = useState(false);
  const [versionRevisada, setVersionRevisada] = useState(false);
  const [confirmacionReclamo, setConfirmacionReclamo] = useState("");
  const [sinCodigo, setSinCodigo] = useState(false);
  const [conflicto, setConflicto] =
    useState<ResultadoPublicacion["detalle"]>(null);
  const [aceptoReemplazar, setAceptoReemplazar] = useState(false);
  const [reabrir, setReabrir] = useState(false);
  const [motivo, setMotivo] = useState("");
  const op = useOperacion();
  const dialogo = useRef<HTMLDialogElement>(null);
  const puedeAbrir =
    datos.puede_publicar &&
    datos.estado === "LISTA_PARA_PUBLICAR" &&
    datos.publicable &&
    !cambiosPendientes;
  useEffect(() => {
    if (abierto) dialogo.current?.showModal();
    else dialogo.current?.close();
  }, [abierto]);
  useEffect(() => {
    function tecla(evento: KeyboardEvent) {
      const elemento = evento.target as HTMLElement;
      if (
        evento.key.toLowerCase() !== "p" ||
        evento.ctrlKey ||
        evento.metaKey ||
        evento.altKey ||
        elemento.isContentEditable ||
        ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(elemento.tagName) ||
        document.querySelector("dialog[open]")
      )
        return;
      if (puedeAbrir) {
        evento.preventDefault();
        setAbierto(true);
      }
    }
    window.addEventListener("keydown", tecla);
    return () => window.removeEventListener("keydown", tecla);
  }, [puedeAbrir]);
  function cerrar() {
    if (op.ocupado) return;
    setAbierto(false);
    setConflicto(null);
    setAceptoReemplazar(false);
  }
  async function publicar(resolucion?: "PUBLICAR_MIA") {
    await op.ejecutar(async () => {
      const r = await publicarCorreccion(cursoId, entregaId, sujetoId, {
        resolucion,
        version_revisada: versionRevisada,
        confirmacion_reclamo: confirmacionReclamo.trim() || undefined,
        reconocimiento_sin_codigo: sinCodigo,
      });
      if (!r.ok) {
        if (r.detalle?.codigo === "CONFLICTO") {
          setConflicto(r.detalle);
          return;
        }
        throw new Error(
          r.detalle?.motivo ||
            "No se pudo publicar. Revisa la corrección e intenta nuevamente.",
        );
      }
      setAbierto(false);
      setConflicto(null);
      setAceptoReemplazar(false);
      if (r.datos?.estado === "PUBLICADA")
        op.setMensaje("Nota publicada y verificada en Canvas.");
      else if (r.datos?.estado === "PUBLICADA_CON_ADVERTENCIA")
        op.setMensaje(
          "La nota se publicó con advertencia. Revisa la nota de Canvas antes de cerrar la corrección.",
        );
      else
        op.setError(
          r.datos?.error ||
            "Canvas no confirmó la publicación. Revisa el estado antes de reintentar.",
        );
      onCambio();
    });
  }
  async function accion(
    tipo: "reintentar" | "reabrir" | "adoptar-canvas" | "rubrica-revisada",
  ) {
    await op.ejecutar(async () => {
      const r = await accionPublicacion(
        cursoId,
        entregaId,
        sujetoId,
        tipo,
        motivo.trim(),
      );
      if (!r.ok) throw new Error(r.error || "No se pudo completar la acción.");
      if (tipo === "adoptar-canvas") {
        setAbierto(false);
        setConflicto(null);
        op.setMensaje(
          `Se adoptó la nota de Canvas${r.datos?.nota ? ` (${r.datos.nota})` : ""}. No se escribió en Canvas.`,
        );
      }
      if (tipo === "reintentar")
        op.setMensaje(
          "La corrección volvió a lista. Revisa el resumen y confirma una nueva publicación.",
        );
      if (tipo === "reabrir") {
        setReabrir(false);
        setMotivo("");
        op.setMensaje(
          "Corrección reabierta. La nota de Canvas se conserva hasta una nueva publicación explícita.",
        );
      }
      if (tipo === "rubrica-revisada")
        op.setMensaje("Revisión de la rúbrica registrada.");
      onCambio();
    });
  }
  const confirmacionesPendientes =
    (datos.banderas.version_desactualizada && !versionRevisada) ||
    (datos.banderas.reclamo_abierto && !confirmacionReclamo.trim()) ||
    (datos.repositorio_estado === "INACCESIBLE" &&
      !datos.banderas.reconocimiento_sin_codigo &&
      !sinCodigo);
  return (
    <section className="panel">
      <h2>Publicación en Canvas</h2>
      <Mensajes error={!abierto ? op.error : null} mensaje={op.mensaje} />
      {datos.rubrica.cambio_sin_revisar && datos.es_propietario && (
        <div>
          <Aviso tipo="warning">
            La rúbrica cambió. Revisa sus criterios antes de continuar.
          </Aviso>
          <button
            disabled={op.ocupado || cambiosPendientes}
            onClick={() => accion("rubrica-revisada")}
          >
            He revisado los cambios de la rúbrica
          </button>
        </div>
      )}
      {!datos.puede_publicar ? (
        <p className="help">
          Puedes preparar el borrador y marcarlo listo. Publica quien tenga el
          permiso correspondiente en este curso.
        </p>
      ) : (
        <>
          {!datos.publicable && (
            <Aviso tipo="warning">
              No publicable:{" "}
              {datos.motivo_no_publicable ??
                "Revisa los requisitos de esta entrega."}
            </Aviso>
          )}
          {cambiosPendientes && (
            <Aviso>
              Guarda los cambios y marca la corrección lista antes de publicar.
            </Aviso>
          )}
          {datos.estado === "LISTA_PARA_PUBLICAR" && (
            <button
              className="primary"
              disabled={!puedeAbrir || op.ocupado}
              onClick={() => setAbierto(true)}
            >
              Publicar en Canvas
            </button>
          )}
          {datos.estado === "PUBLICANDO" && (
            <Aviso>
              La publicación está en curso. Actualiza el estado antes de
              intentar otra operación.
            </Aviso>
          )}
          {datos.estado === "ERROR_PUBLICACION" && (
            <button disabled={op.ocupado} onClick={() => accion("reintentar")}>
              Preparar reintento de publicación
            </button>
          )}
          {["PUBLICADA", "PUBLICADA_CON_ADVERTENCIA"].includes(
            datos.estado,
          ) && (
            <>
              <Aviso
                tipo={datos.estado === "PUBLICADA" ? "success" : "warning"}
              >
                {datos.estado === "PUBLICADA"
                  ? "Publicada y verificada en Canvas."
                  : "Publicada con advertencia. Revisa las notas del panel Canvas; si debes cambiarlas, reabre la corrección."}
              </Aviso>
              <button
                disabled={op.ocupado}
                onClick={() => setReabrir(!reabrir)}
              >
                Reabrir corrección
              </button>
              {reabrir && (
                <form
                  className="form-stack"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void accion("reabrir");
                  }}
                >
                  <label>
                    Motivo de reapertura
                    <textarea
                      required
                      minLength={5}
                      maxLength={2000}
                      value={motivo}
                      onChange={(e) => setMotivo(e.target.value)}
                    />
                  </label>
                  <p className="help">
                    Reabrir permite editar el borrador. La nota publicada no
                    cambia automáticamente.
                  </p>
                  <button
                    className="primary"
                    disabled={op.ocupado || motivo.trim().length < 5}
                  >
                    Confirmar reapertura
                  </button>
                </form>
              )}
            </>
          )}
          {![
            "LISTA_PARA_PUBLICAR",
            "PUBLICANDO",
            "PUBLICADA",
            "PUBLICADA_CON_ADVERTENCIA",
            "ERROR_PUBLICACION",
          ].includes(datos.estado) && (
            <p className="help">
              Primero guarda el borrador y marca esta corrección como lista.
            </p>
          )}
        </>
      )}
      <dialog
        ref={dialogo}
        aria-labelledby="publicacion-titulo"
        onCancel={(e) => {
          e.preventDefault();
          cerrar();
        }}
      >
        <h2 id="publicacion-titulo">
          {conflicto ? "Conflicto con Canvas" : "Confirmar publicación"}
        </h2>
        <Mensajes error={op.error} mensaje={null} />
        {conflicto ? (
          <>
            <Aviso tipo="warning">
              Canvas ya tiene otra nota. Nada se publicó. Elige cómo resolver la
              diferencia.
            </Aviso>
            <ul>
              {conflicto.conflictos?.map((c) => (
                <li key={c.estudiante}>
                  {c.estudiante}: Canvas {c.nota_canvas ?? "sin nota"} · tu nota{" "}
                  {conflicto.nota_propia ?? "sin nota"}
                  {c.calificada_en && (
                    <div className="help">
                      {fechaFinal(c.calificada_en, curso.zona_horaria)}
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <label className="check">
              <input
                type="checkbox"
                checked={aceptoReemplazar}
                disabled={op.ocupado}
                onChange={(e) => setAceptoReemplazar(e.target.checked)}
              />
              Entiendo que reemplazaré la nota de Canvas
            </label>
            <div className="actions">
              <button
                className="primary"
                disabled={!aceptoReemplazar || op.ocupado}
                onClick={() => publicar("PUBLICAR_MIA")}
              >
                Publicar la mía
              </button>
              <button
                disabled={op.ocupado}
                onClick={() => accion("adoptar-canvas")}
              >
                Adoptar la de Canvas
              </button>
              <button disabled={op.ocupado} onClick={cerrar}>
                Dejarlo como está
              </button>
            </div>
          </>
        ) : (
          <>
            <p>
              Se publicará la calificación de{" "}
              <strong>{datos.sujeto.nombre}</strong> para{" "}
              <strong>{datos.entrega.nombre}</strong>, a nombre de{" "}
              <strong>{datos.titular}</strong>.
            </p>
            {datos.borrador ? (
              <>
                <p>
                  <strong>Nota: {datos.borrador.nota ?? "Sin nota"}</strong>
                </p>
                <h3>Comentario guardado</h3>
                <pre style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                  {datos.borrador.comentario || "Sin comentario adicional."}
                </pre>
              </>
            ) : (
              <Aviso>
                El borrador está restringido a su corrector. Se publicará la
                nota guardada que fue marcada lista.
              </Aviso>
            )}
            <p className="help">
              Canvas añadirá la entrega, su cierre, el SHA de la versión
              revisada y la autoría de la corrección al comentario. Versión:{" "}
              {datos.version?.sha ?? "sin commits al cierre"}.
            </p>
            {datos.banderas.version_desactualizada && (
              <label className="check">
                <input
                  type="checkbox"
                  checked={versionRevisada}
                  onChange={(e) => setVersionRevisada(e.target.checked)}
                />
                He revisado la versión nueva
              </label>
            )}
            {datos.banderas.reclamo_abierto && (
              <label>
                Motivo para publicar con un reclamo abierto
                <input
                  value={confirmacionReclamo}
                  onChange={(e) => setConfirmacionReclamo(e.target.value)}
                />
              </label>
            )}
            {datos.repositorio_estado === "INACCESIBLE" &&
              !datos.banderas.reconocimiento_sin_codigo && (
                <label className="check">
                  <input
                    type="checkbox"
                    checked={sinCodigo}
                    onChange={(e) => setSinCodigo(e.target.checked)}
                  />
                  Califico sin haber podido abrir el código de esta versión
                </label>
              )}
            <p className="help">
              La aplicación solicita publicar sin descuento automático por
              atraso y verifica la nota después del envío.
            </p>
            <div className="actions end">
              <button autoFocus disabled={op.ocupado} onClick={cerrar}>
                Cancelar
              </button>
              <button
                className="primary"
                disabled={op.ocupado || confirmacionesPendientes}
                onClick={() => publicar()}
              >
                {op.ocupado ? "Publicando…" : "Confirmar y publicar"}
              </button>
            </div>
          </>
        )}
      </dialog>
    </section>
  );
}
