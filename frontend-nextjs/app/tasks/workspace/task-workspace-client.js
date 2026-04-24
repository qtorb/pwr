"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import TaskHintFeedback from "../[taskId]/task-hint-feedback";
import { createWorkspaceTaskAction, saveWorkspaceResultAction } from "./actions";

const MODEL_OPTIONS = [
  { value: "gemini-2.5-flash-lite", label: "gemini-2.5-flash-lite" },
  { value: "gemini-2.5-pro", label: "gemini-2.5-pro" },
  { value: "mock-eco", label: "mock-eco" },
  { value: "mock-racing", label: "mock-racing" },
];

function StateBadge({ state }) {
  const normalized = String(state || "draft").toLowerCase();
  const labels = {
    draft: "Draft",
    pending: "Pending",
    preview: "Preview",
    failed: "Failed",
    executed: "Executed",
  };

  return <span className={`badge ${normalized}`}>{labels[normalized] || normalized}</span>;
}

function buildFallbackTitle(title, prompt, resultText) {
  const cleanTitle = String(title || "").trim();
  if (cleanTitle) return cleanTitle;

  const source = String(prompt || resultText || "").trim();
  if (!source) {
    return `Task ${new Date().toISOString().slice(0, 16).replace("T", " ")}`;
  }

  const firstLine = source.split(/\r?\n/, 1)[0].replace(/\s+/g, " ").trim();
  return firstLine.slice(0, 72) || "Task sin titulo";
}

export default function TaskWorkspaceClient({
  projects,
  selectedProject,
  task,
  latestExecution,
  recommendation,
  flags,
}) {
  const router = useRouter();
  const [taskRecord, setTaskRecord] = useState(task || null);
  const [taskId, setTaskId] = useState(task?.id ? Number(task.id) : null);
  const [projectId, setProjectId] = useState(
    String(task?.project_id || selectedProject?.id || projects[0]?.id || ""),
  );
  const [model, setModel] = useState(
    String(latestExecution?.model || task?.suggested_model || MODEL_OPTIONS[0].value),
  );
  const [title, setTitle] = useState(String(task?.title || ""));
  const [prompt, setPrompt] = useState(
    String(latestExecution?.prompt_text || task?.context || ""),
  );
  const [resultText, setResultText] = useState(
    String(latestExecution?.output_text || task?.llm_output || ""),
  );
  const [status, setStatus] = useState(
    String(latestExecution?.execution_status || task?.execution_status || task?.status || "draft"),
  );
  const [copyMessage, setCopyMessage] = useState("");
  const [savedMessage, setSavedMessage] = useState(
    flags.saved ? "Resultado guardado." : flags.created ? "Tarea creada." : "",
  );
  const [errorMessage, setErrorMessage] = useState("");
  const [pendingAction, setPendingAction] = useState("");

  const projectOptions = useMemo(
    () => projects.map((project) => ({ value: String(project.id), label: project.name })),
    [projects],
  );
  const activeProject =
    projects.find((project) => String(project.id) === String(projectId)) || taskRecord || selectedProject || null;
  const hasProjects = Boolean(projects.length);
  const recommendationTaskType = recommendation?.task_type || task?.task_type || "generic";

  async function ensureTask() {
    if (taskId) return taskId;
    if (!projectId) {
      setErrorMessage("Crea primero un proyecto para usar la workspace.");
      return null;
    }

    const createdTask = await createWorkspaceTaskAction({
      projectId: Number(projectId),
      title: buildFallbackTitle(title, prompt, resultText),
      prompt: String(prompt || "").trim(),
      model,
    });

    setTaskRecord(createdTask);
    setTaskId(Number(createdTask.id));
    setTitle(createdTask.title || title);
    setStatus(createdTask.execution_status || createdTask.status || "pending");
    setSavedMessage("Tarea creada.");
    router.replace(`/tasks/workspace?taskId=${createdTask.id}&created=1`);
    return Number(createdTask.id);
  }

  async function handleCopyPrompt() {
    setErrorMessage("");
    setSavedMessage("");
    setPendingAction("copy");
    try {
      await ensureTask();
      await navigator.clipboard.writeText(String(prompt || ""));
      setCopyMessage(prompt ? "Prompt copiado." : "Prompt vacio copiado.");
      window.setTimeout(() => setCopyMessage(""), 1800);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No fue posible copiar el prompt.");
    } finally {
      setPendingAction("");
    }
  }

  async function handleSaveResult() {
    setErrorMessage("");
    setSavedMessage("");
    if (!String(resultText || "").trim()) {
      setErrorMessage("Pega un resultado antes de guardarlo.");
      return;
    }

    setPendingAction("save");
    try {
      const resolvedTaskId = await ensureTask();
      if (!resolvedTaskId) return;

      const payload = await saveWorkspaceResultAction({
        taskId: resolvedTaskId,
        model,
        prompt: String(prompt || "").trim(),
        resultText: String(resultText || "").trim(),
      });
      setStatus(payload.status || "executed");
      setSavedMessage(payload.message || "Resultado guardado.");
      router.replace(`/tasks/workspace?taskId=${resolvedTaskId}&saved=1`);
      router.refresh();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "No fue posible guardar el resultado.");
    } finally {
      setPendingAction("");
    }
  }

  return (
    <section className="workspace-grid">
      <div className="workspace-main">
        <div className="panel">
          <div className="panel-body stack">
            <div className="band-head">
              <h2>Task Workspace</h2>
              <div className="subtle">Flujo directo para crear, copiar, pegar y guardar</div>
            </div>

            {!hasProjects ? (
              <div className="muted-box">
                Todavia no hay proyectos disponibles.{" "}
                <Link href="/projects" className="inline-link">
                  Crea el primer proyecto
                </Link>
                {" "}y vuelve a la workspace.
              </div>
            ) : (
              <div className="workspace-form-grid">
                <div className="form-field">
                  <label htmlFor="workspace-project">Proyecto</label>
                  <select
                    id="workspace-project"
                    value={projectId}
                    onChange={(event) => setProjectId(event.target.value)}
                    disabled={Boolean(taskId)}
                  >
                    {projectOptions.map((project) => (
                      <option key={project.value} value={project.value}>
                        {project.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-field">
                  <label htmlFor="workspace-model">Modelo</label>
                  <select
                    id="workspace-model"
                    value={model}
                    onChange={(event) => setModel(event.target.value)}
                  >
                    {MODEL_OPTIONS.map((item) => (
                      <option key={item.value} value={item.value}>
                        {item.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-field">
                  <label>Status</label>
                  <div className="workspace-status">
                    <StateBadge state={status} />
                    <span className="subtle">
                      {taskId ? `Task #${taskId}` : "Se creara al copiar o guardar"}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="form-field">
              <label htmlFor="workspace-title">Titulo</label>
              <input
                id="workspace-title"
                type="text"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="Que necesitas mover ahora"
              />
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-body stack">
            <div className="band-head">
              <h2>Prompt</h2>
              <div className="subtle">Escribe, copia y ejecuta fuera de PWR</div>
            </div>

            <div className="form-field">
              <label htmlFor="workspace-prompt">Prompt</label>
              <textarea
                id="workspace-prompt"
                rows={14}
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                placeholder="Escribe aqui el prompt que vas a ejecutar fuera."
              />
            </div>

            <div className="form-actions workspace-inline-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={handleCopyPrompt}
                disabled={!hasProjects || pendingAction === "copy" || pendingAction === "save"}
              >
                {pendingAction === "copy" ? "Copiando..." : "Copiar prompt"}
              </button>
              <div className="subtle">
                {copyMessage || "La tarea se crea automaticamente en el primer paso util del flujo."}
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
          <div className="panel-body stack">
            <div className="band-head">
              <h2>Resultado</h2>
              <div className="subtle">Pega la salida final y guardala en la tarea</div>
            </div>

            <div className="form-field">
              <label htmlFor="workspace-result">Resultado</label>
              <textarea
                id="workspace-result"
                rows={16}
                value={resultText}
                onChange={(event) => setResultText(event.target.value)}
                placeholder="Pega aqui el resultado que obtuviste fuera de PWR."
              />
            </div>

            <div className="form-actions workspace-inline-actions">
              <button
                className="primary-button"
                type="button"
                onClick={handleSaveResult}
                disabled={!hasProjects || pendingAction === "save" || pendingAction === "copy"}
              >
                {pendingAction === "save" ? "Guardando..." : "Guardar resultado"}
              </button>
              <div className="subtle">
                {savedMessage || "El resultado quedara dentro de la tarea actual y aparecera en /tasks."}
              </div>
            </div>

            {errorMessage ? <div className="feedback-banner error">{errorMessage}</div> : null}
          </div>
        </div>
      </div>

      <aside className="workspace-side">
        <div className="panel">
          <div className="panel-body stack">
            <div className="band-head">
              <h2>Contexto actual</h2>
              <div className="subtle">Lo justo para no perder el hilo</div>
            </div>
            <div className="info-block">
              <div className="label">Proyecto</div>
              <div>{activeProject?.name || taskRecord?.project_name || "Sin proyecto"}</div>
            </div>
            <div className="info-block">
              <div className="label">Modelo</div>
              <div>{model}</div>
            </div>
            <div className="info-block">
              <div className="label">Estado</div>
              <div>{status}</div>
            </div>
            {taskId ? (
              <div className="stack compact">
                <Link href={`/tasks/${taskId}`} className="inline-link">
                  Ver tarea completa
                </Link>
                <Link href="/tasks" className="inline-link">
                  Ver en /tasks
                </Link>
              </div>
            ) : null}
          </div>
        </div>

        <details className="panel hint-panel">
          <summary className="hint-summary">
            <span>Hint experimental</span>
            <span className="subtle">
              {recommendation?.model ? recommendation.model : "Se mostrara cuando la tarea tenga contexto"}
            </span>
          </summary>
          <div className="panel-body">
            {taskId && recommendation ? (
              <TaskHintFeedback
                taskId={taskId}
                taskType={recommendationTaskType}
                recommendation={recommendation}
              />
            ) : (
              <div className="muted-box">
                Crea la tarea y vuelve a abrir la workspace para revisar el hint y dejar feedback rapido.
              </div>
            )}
          </div>
        </details>
      </aside>
    </section>
  );
}
