"use client";

import Link from "next/link";
import { useMemo, useState, useTransition } from "react";

import { saveAssetAction } from "./actions";

function normalizeText(value) {
  return String(value || "").trim();
}

function buildMarkdown({ taskTitle, stateLabel, content }) {
  return [`# ${taskTitle || "Resultado PWR"}`, "", `Estado: ${stateLabel}`, "", content].join("\n");
}

function safeFilename(value) {
  const clean = String(value || "resultado-pwr")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${clean || "resultado-pwr"}.md`;
}

export default function TaskResultActions({
  taskId,
  projectId,
  projectHref,
  taskTitle,
  defaultAssetType,
  resultContent,
  sourceExecutionId,
  sourceExecutionStatus,
  canSaveAsset,
}) {
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successPayload, setSuccessPayload] = useState(null);
  const [isSaving, startTransition] = useTransition();

  const resolvedContent = useMemo(() => normalizeText(resultContent), [resultContent]);
  const canActOnResult = Boolean(resolvedContent);
  const hasSavedAsset = Boolean(successPayload?.id);
  const saveDisabled = isSaving || !canSaveAsset || !canActOnResult;

  function clearMessages() {
    setErrorMessage("");
    setStatusMessage("");
  }

  function handleSaveAsset() {
    clearMessages();
    setSuccessPayload(null);

    if (!canActOnResult) {
      setErrorMessage("No hay resultado visible para guardar como activo.");
      return;
    }

    startTransition(async () => {
      try {
        const payload = await saveAssetAction({
          projectId,
          taskId,
          sourceExecutionId,
          sourceExecutionStatus,
          assetType: defaultAssetType || "output",
          title: taskTitle || `Tarea ${taskId}`,
          summary: "Guardado desde la pantalla de resultado.",
          content: resolvedContent,
        });
        setSuccessPayload(payload);
        setStatusMessage("Guardado como activo.");
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible guardar el activo.");
      }
    });
  }

  if (!canActOnResult) {
    return (
      <div className="result-action-card passive">
        <div className="feedback-banner">
          Todavia no hay resultado para guardar. Vuelve al workspace y pega la salida final.
        </div>
      </div>
    );
  }

  if (!canSaveAsset) {
    return (
      <div className="result-action-card passive">
        <div className="feedback-banner">
          Este estado todavia no permite guardar como activo. Revisa la tarea o captura un resultado valido.
        </div>
      </div>
    );
  }

  return (
    <div className="result-action-card">
      <div className="result-conversion-copy">
        Cierra la tarea preservando este resultado como activo reutilizable.
      </div>

      {!hasSavedAsset ? (
        <button className="primary-button result-primary-action" type="button" onClick={handleSaveAsset} disabled={saveDisabled}>
          {isSaving ? "Guardando..." : "Guardar como activo"}
        </button>
      ) : null}

      {statusMessage ? (
        <div className="feedback-banner ok">
          <strong>Guardado como activo.</strong>
          <div>
            El valor queda preservado en el proyecto. Puedes volver al trabajo sin perder este resultado.
          </div>
          <div className="stack compact">
            <Link href={`/tasks/workspace?taskId=${taskId}`} className="inline-link">
              Volver al workspace
            </Link>
            <Link href={projectHref} className="inline-link">
              Ver activos del proyecto
            </Link>
          </div>
        </div>
      ) : null}

      {successPayload?.id ? <div className="subtle">Activo #{successPayload.id} creado.</div> : null}
      {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
    </div>
  );
}

export function ResultSecondaryActions({ taskId, taskTitle, stateLabel, resultContent }) {
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const resolvedContent = useMemo(() => normalizeText(resultContent), [resultContent]);
  const canActOnResult = Boolean(resolvedContent);

  function clearMessages() {
    setErrorMessage("");
    setStatusMessage("");
  }

  async function handleCopy() {
    clearMessages();
    if (!canActOnResult) {
      setErrorMessage("No hay resultado visible para copiar.");
      return;
    }

    try {
      await navigator.clipboard.writeText(resolvedContent);
      setStatusMessage("Resultado copiado.");
    } catch {
      setErrorMessage("No fue posible copiar el resultado.");
    }
  }

  function handleExportMarkdown() {
    clearMessages();
    if (!canActOnResult) {
      setErrorMessage("No hay resultado visible para exportar.");
      return;
    }

    const markdown = buildMarkdown({ taskTitle, stateLabel, content: resolvedContent });
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = safeFilename(taskTitle);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
    setStatusMessage("Markdown exportado.");
  }

  return (
    <div className="result-secondary-panel">
      <div className="band-head">
        <h2>Acciones secundarias</h2>
        <div className="subtle">Usalas solo si necesitas salir del flujo principal</div>
      </div>

      <div className="result-secondary-actions" aria-label="Acciones secundarias del resultado">
        <button className="secondary-button" type="button" onClick={handleCopy} disabled={!canActOnResult}>
          Copiar
        </button>
        <Link className="secondary-button" href={`/tasks/workspace?taskId=${taskId}`}>
          Iterar resultado
        </Link>
        <button className="secondary-button" type="button" onClick={handleExportMarkdown} disabled={!canActOnResult}>
          Exportar Markdown
        </button>
      </div>

      {statusMessage ? <div className="feedback-banner ok">{statusMessage}</div> : null}
      {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
    </div>
  );
}
