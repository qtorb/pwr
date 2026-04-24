"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";

import { saveAssetAction } from "./actions";

function normalizeText(value) {
  return String(value || "").trim();
}

export default function TaskAssetPanel({
  taskId,
  projectId,
  projectHref,
  defaultAssetType,
  defaultTitle,
  defaultSummary,
  resultContent,
  briefingContent,
  sourceExecutionId,
  sourceExecutionStatus,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [assetType, setAssetType] = useState(defaultAssetType || "output");
  const [title, setTitle] = useState(defaultTitle || "");
  const [summary, setSummary] = useState(defaultSummary || "");
  const [errorMessage, setErrorMessage] = useState("");
  const [successPayload, setSuccessPayload] = useState(null);
  const [isSaving, startTransition] = useTransition();

  const resolvedContent = useMemo(() => {
    if (assetType === "briefing") {
      return normalizeText(briefingContent) || normalizeText(resultContent);
    }
    return normalizeText(resultContent);
  }, [assetType, briefingContent, resultContent]);

  function handleSave() {
    const cleanTitle = normalizeText(title);
    if (!cleanTitle) {
      setErrorMessage("El activo necesita un titulo.");
      return;
    }
    if (!resolvedContent) {
      setErrorMessage("No hay contenido util para guardar como activo.");
      return;
    }

    setErrorMessage("");
    setSuccessPayload(null);

    startTransition(async () => {
      try {
        const payload = await saveAssetAction({
          projectId,
          taskId,
          sourceExecutionId,
          sourceExecutionStatus,
          assetType,
          title: cleanTitle,
          summary: summary || "",
          content: resolvedContent,
        });
        setSuccessPayload(payload);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible guardar el activo.");
      }
    });
  }

  return (
    <div className="panel">
      <div className="panel-body stack">
        <div className="band-head">
          <h2>Activo reutilizable</h2>
          <div className="subtle">Desde esta tarea</div>
        </div>

        {!isOpen ? (
          <button className="secondary-button" type="button" onClick={() => setIsOpen(true)}>
            Guardar como activo
          </button>
        ) : (
          <div className="asset-form">
            <div className="form-field">
              <label htmlFor={`asset-type-${taskId}`}>Tipo</label>
              <select
                id={`asset-type-${taskId}`}
                value={assetType}
                onChange={(event) => setAssetType(event.target.value)}
              >
                <option value="output">output</option>
                <option value="preview">preview</option>
                <option value="briefing">briefing</option>
              </select>
            </div>

            <div className="form-field">
              <label htmlFor={`asset-title-${taskId}`}>Titulo</label>
              <input
                id={`asset-title-${taskId}`}
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Nombre del activo"
              />
            </div>

            <div className="form-field">
              <label htmlFor={`asset-summary-${taskId}`}>Resumen</label>
              <textarea
                id={`asset-summary-${taskId}`}
                rows={3}
                value={summary}
                onChange={(event) => setSummary(event.target.value)}
                placeholder="Resumen opcional"
              />
            </div>

            <div className="subtle">
              {isSaving ? "Guardando..." : "Se guardara sin salir de esta tarea."}
            </div>

            <div className="form-actions">
              <button className="primary-button" type="button" onClick={handleSave} disabled={isSaving}>
                {isSaving ? "Guardando..." : "Guardar como activo"}
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => {
                  setIsOpen(false);
                  setErrorMessage("");
                }}
                disabled={isSaving}
              >
                Cancelar
              </button>
            </div>
          </div>
        )}

        {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}

        {successPayload ? (
          <div className="feedback-banner ok">
            Activo guardado.
            <div className="stack compact">
              <div className="subtle">Quedo vinculado a la tarea actual y persistido en el proyecto.</div>
              <Link href={projectHref} className="inline-link">
                Ver en proyecto
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
