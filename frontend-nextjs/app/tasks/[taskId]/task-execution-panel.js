"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";

import { executeTaskAction } from "./actions";

function getActionConfig(state) {
  const normalized = String(state || "pending").toLowerCase();
  return {
    label:
      {
        draft: "Ejecutar ahora",
        pending: "Ejecutar ahora",
        preview: "Continuar",
        failed: "Reintentar",
        executed: "Ejecutar de nuevo",
      }[normalized] || "Ejecutar ahora",
    hint:
      {
        draft: "La tarea usara el contexto actual y quedara actualizada aqui mismo.",
        pending: "La tarea usara el runtime actual de PWR y refrescara este detalle al terminar.",
        preview: "La propuesta previa se retomara y la vista se actualizara al terminar.",
        failed: "El ultimo intento se volvera a lanzar con el contexto visible.",
        executed: "Se lanzara una nueva ejecucion con el contexto actual.",
      }[normalized] || "La tarea se ejecutara con el runtime actual de PWR.",
  };
}

export default function TaskExecutionPanel({ taskId, currentState }) {
  const router = useRouter();
  const [isRunning, startTransition] = useTransition();
  const [errorMessage, setErrorMessage] = useState("");
  const action = useMemo(() => getActionConfig(currentState), [currentState]);

  function handleExecute() {
    setErrorMessage("");

    startTransition(async () => {
      try {
        const payload = await executeTaskAction(taskId);
        const nextStatus = encodeURIComponent(payload.status || "updated");
        router.replace(`/tasks/${taskId}?updated=1&status=${nextStatus}`);
        router.refresh();
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No fue posible ejecutar la tarea.");
      }
    });
  }

  return (
    <div className="panel">
      <div className="panel-body stack">
        <div className="band-head">
          <h2>Accion principal</h2>
          <div className="subtle">Operativo</div>
        </div>
        <button className="primary-button" type="button" onClick={handleExecute} disabled={isRunning}>
          {isRunning ? "Ejecutando..." : action.label}
        </button>
        <div className="subtle">
          {isRunning ? "La tarea se esta ejecutando y la vista se refrescara al terminar." : action.hint}
        </div>
        {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
      </div>
    </div>
  );
}
