import Link from "next/link";

import AppHeader from "../../_components/app-header";
import { getTaskDetailData } from "../../../lib/pwr-api";
import TaskExecutionPanel from "./task-execution-panel";
import TaskHintFeedback from "./task-hint-feedback";
import TaskResultActions, { ResultSecondaryActions } from "./task-result-actions";

export const dynamic = "force-dynamic";

function formatDate(value) {
  if (!value) return "sin fecha";
  try {
    return new Intl.DateTimeFormat("es-ES", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function StateBadge({ state }) {
  const normalized = String(state || "pending").toLowerCase();
  const labels = {
    draft: "Draft",
    pending: "Pending",
    preview: "Preview",
    failed: "Failed",
    executed: "Executed",
  };

  return <span className={`badge ${normalized}`}>{labels[normalized] || normalized}</span>;
}

function stateCopy(state) {
  const normalized = String(state || "pending").toLowerCase();
  return {
    draft: "Draft",
    pending: "Pending",
    preview: "Preview",
    failed: "Failed",
    executed: "Executed",
  }[normalized] || normalized;
}

function ExecutionHistory({ items }) {
  if (!items.length) {
    return <div className="muted-box">Todavia no hay ejecuciones registradas. Ejecuta la tarea desde la accion principal.</div>;
  }

  return (
    <div className="list">
      {items.slice(0, 6).map((run) => (
        <div className="row" key={run.id}>
          <div className="row-top">
            <div className="row-title">Run #{run.id}</div>
            <StateBadge state={run.execution_status} />
          </div>
          <div className="row-meta">
            {run.provider ? <span>{run.provider}</span> : null}
            {run.model ? <span>{run.model}</span> : null}
            <span>{formatDate(run.executed_at || run.created_at)}</span>
            {run.latency_ms ? <span>{run.latency_ms} ms</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

function getResultMode(taskState, resultContent) {
  const normalized = String(taskState || "pending").toLowerCase();
  if (normalized === "failed") return "error";
  if (String(resultContent || "").trim()) return "ready";
  return "empty";
}

function getResultStatusCopy(mode) {
  return {
    ready: "Resultado listo",
    empty: "Resultado vacio",
    error: "Error de ejecucion",
  }[mode] || "Resultado";
}

function getExecutionActionLabel(state) {
  const normalized = String(state || "pending").toLowerCase();
  return {
    draft: "Ejecutar ahora",
    pending: "Ejecutar ahora",
    preview: "Continuar",
    failed: "Reintentar",
    executed: "Ejecutar de nuevo",
  }[normalized] || "Ejecutar ahora";
}

function ResultOutputBlock({ mode, task, latestExecution, resultContent }) {
  const errorText = latestExecution?.error_message || task?.router_summary || "";

  if (mode === "error") {
    return (
      <div className="result-output-block error">
        <div className="label">No se pudo generar el resultado.</div>
        <div>Revisa la ejecucion o vuelve a intentarlo.</div>
        <pre className="content-block">
          {errorText || "La ejecucion fallo, pero no hay mensaje de error visible."}
        </pre>
      </div>
    );
  }

  if (mode === "empty") {
    return (
      <div className="result-output-block empty">
        <div className="label">Resultado</div>
        <div>
          Todavia no hay resultado para esta tarea.
          <br />
          Ejecuta la tarea o anade un resultado antes de guardarlo como activo.
        </div>
      </div>
    );
  }

  return (
    <div className="result-output-block ready">
      <div className="label">Output principal</div>
      <pre className="content-block">{resultContent}</pre>
    </div>
  );
}

function DetailDisclosure({ title, eyebrow, children }) {
  return (
    <details className="panel disclosure-panel">
      <summary className="disclosure-summary">
        <span>{title}</span>
        {eyebrow ? <span className="subtle">{eyebrow}</span> : null}
      </summary>
      <div className="panel-body stack">{children}</div>
    </details>
  );
}

function ResultNextStep({ mode, taskId }) {
  const isError = mode === "error";
  return (
    <div className="result-action-card next-step">
      <div className="result-conversion-copy">
        {isError
          ? "La tarea necesita una revision antes de poder cerrarse."
          : "El siguiente paso es capturar el resultado final."}
      </div>
      <Link className="primary-button result-primary-action" href={`/tasks/workspace?taskId=${taskId}`}>
        {isError ? "Revisar en workspace" : "Anadir resultado"}
      </Link>
      <div className="subtle">
        {isError
          ? "Vuelve al carril de trabajo para ajustar prompt, modelo o resultado."
          : "Pega la salida que obtuviste fuera de PWR y vuelve aqui para guardarla como activo."}
      </div>
    </div>
  );
}

export default async function TaskDetailPage({ params, searchParams }) {
  const { taskId } = await params;
  const resolvedSearchParams = (await searchParams) || {};
  const { apiBaseUrl, task, latestExecution, executions, recommendation, errors, missing } =
    await getTaskDetailData(taskId);

  if (!task) {
    return (
      <main className="shell">
        <AppHeader subtitle="Detalle operativo de tarea" statusText="API en revision" statusTone="default" />

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <Link href="/tasks">Tasks</Link>
              <span>/</span>
              <span>Tarea</span>
            </div>
            <h1>{missing ? "Tarea no encontrada" : "Tarea no disponible"}</h1>
            <p>
              {missing
                ? "La API no devolvio ninguna tarea para este id."
                : "No fue posible cargar la tarea desde FastAPI en este momento."}
            </p>
          </section>

          <section className="panel">
            <div className="panel-body stack">
              {errors.length ? (
                <div className="muted-box">
                  <ul>
                    {errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              <div className="stack compact">
                <Link href="/tasks" className="inline-link">
                  Volver a Tasks
                </Link>
                <Link href="/" className="inline-link">
                  Volver a Home
                </Link>
              </div>
            </div>
          </section>
        </div>
      </main>
    );
  }

  const taskState = latestExecution?.execution_status || task.execution_status || task.status || "pending";
  const updatedState = resolvedSearchParams.updated === "1" ? resolvedSearchParams.status || "" : "";
  const createdTask = resolvedSearchParams.created === "1";
  const fromAsset = resolvedSearchParams.fromAsset === "1";
  const resultContent = String(latestExecution?.output_text || task.llm_output || "").trim();
  const canSaveAsset =
    ["preview", "executed"].includes(String(taskState).toLowerCase()) && Boolean(resultContent);
  const defaultAssetType = String(taskState).toLowerCase() === "preview" ? "preview" : "output";
  const projectLabel = task.project_name || `Proyecto ${task.project_id}`;
  const resultMode = getResultMode(taskState, resultContent);
  const resultStatusCopy = getResultStatusCopy(resultMode);
  const executionActionLabel = getExecutionActionLabel(taskState);

  return (
    <main className="shell">
      <AppHeader subtitle="Detalle operativo de tarea" statusText="API conectada" statusTone="ok" />

      <div className="page result-page">
        <section className="result-top">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            <Link href="/projects">Projects</Link>
            <span>/</span>
            <Link href={`/projects/${task.project_id}`}>{projectLabel}</Link>
            <span>/</span>
            <Link href={`/tasks/workspace?taskId=${task.id}`}>Workspace</Link>
          </div>
        </section>

        {errors.length ? (
          <section className="panel">
            <div className="muted-box">
              Se detectaron respuestas incompletas desde la API:
              <ul>
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          </section>
        ) : null}

        {createdTask ? (
          <section className="feedback-banner ok">Tarea creada. Ya puedes ejecutar o seguir afinando el briefing.</section>
        ) : null}

        {updatedState ? (
          <section className="feedback-banner ok">Actualizado. Estado actual: {stateCopy(updatedState)}.</section>
        ) : null}

        {fromAsset ? (
          <section className="feedback-banner ok">
            Tarea creada desde un activo reutilizable. El titulo y el contexto ya llegaron prellenados.
          </section>
        ) : null}

        <section className={`panel result-first-panel ${resultMode}`}>
          <div className="panel-body result-first-body">
            <div className="result-heading">
              <div className="result-status-line">
                <span className={`result-status-dot ${resultMode}`} aria-hidden="true" />
                <span className="result-status-copy">{resultStatusCopy}</span>
              </div>
              <h1>{task.title || `Tarea ${task.id}`}</h1>
              <div className="subtle">
                {resultMode === "ready"
                  ? "El output principal esta listo."
                  : resultMode === "error"
                    ? "No se pudo generar el resultado. Revisa la ejecucion o vuelve a intentarlo."
                    : "Aun no hay output principal para esta tarea."}
              </div>
            </div>

            <div className={`result-decision-grid ${resultMode === "ready" ? "" : "single"}`}>
              <ResultOutputBlock
                mode={resultMode}
                task={task}
                latestExecution={latestExecution}
                resultContent={resultContent}
              />

              {resultMode === "ready" ? (
                <TaskResultActions
                  taskId={task.id}
                  projectId={task.project_id}
                  projectHref={`/projects/${task.project_id}`}
                  taskTitle={task.title || `Tarea ${task.id}`}
                  defaultAssetType={defaultAssetType}
                  resultContent={resultContent}
                  sourceExecutionId={latestExecution?.id || null}
                  sourceExecutionStatus={taskState}
                  canSaveAsset={canSaveAsset}
                />
              ) : (
                <ResultNextStep mode={resultMode} taskId={task.id} />
              )}
            </div>
          </div>
        </section>

        <details className="panel more-options-panel">
          <summary className="disclosure-summary more-options-summary">
            <span>Mas opciones</span>
            <span className="subtle">Copiar, iterar, contexto y metadatos</span>
          </summary>

          <div className="panel-body result-more-options">
            <ResultSecondaryActions
              taskId={task.id}
              taskTitle={task.title || `Tarea ${task.id}`}
              stateLabel={resultStatusCopy}
              resultContent={resultContent}
            />

            <section className="result-disclosures">
              <DetailDisclosure title="Contexto usado" eyebrow="Cerrado por defecto">
                <div className="info-block">
                  <div className="label">Proyecto</div>
                  <div>{projectLabel}</div>
                </div>
                <div className="info-block">
                  <div className="label">Contexto de proyecto</div>
                  <div>{task.project_description || task.project_objective || "Sin descripcion visible para este proyecto."}</div>
                </div>
                <div className="info-block">
                  <div className="label">Task type</div>
                  <div>{task.task_type || "Pensar"}</div>
                </div>
                <div className="info-block">
                  <div className="label">Briefing</div>
                  <pre className="content-block">
                    {task.context || task.description || "Sin contexto visible para esta tarea."}
                  </pre>
                </div>
                <div className="info-block">
                  <div className="label">Resumen</div>
                  <div>{task.description || task.router_summary || "Sin resumen visible para esta tarea."}</div>
                </div>
              </DetailDisclosure>

              <DetailDisclosure title="Ejecucion" eyebrow={`Siguiente accion: ${executionActionLabel}`}>
                {latestExecution ? (
                  <div className="stack">
                    <div className="info-block">
                      <div className="label">Estado</div>
                      <div>{latestExecution.execution_status || "Sin estado visible."}</div>
                    </div>
                    <div className="info-block">
                      <div className="label">Modelo y provider</div>
                      <div>
                        {latestExecution.provider || "provider?"} / {latestExecution.model || "modelo?"}
                      </div>
                    </div>
                    <div className="info-block">
                      <div className="label">Timestamp</div>
                      <div>{formatDate(latestExecution.executed_at || latestExecution.created_at)}</div>
                    </div>
                    <div className="info-block">
                      <div className="label">Latencia</div>
                      <div>
                        {latestExecution.latency_ms
                          ? `${latestExecution.latency_ms} ms`
                          : "Sin latencia visible."}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="muted-box">Todavia no hay ejecuciones registradas. Ejecuta la tarea desde la accion principal.</div>
                )}
                <TaskExecutionPanel taskId={task.id} currentState={taskState} />
              </DetailDisclosure>

              <DetailDisclosure title="Historial" eyebrow={`${executions.length} ejecuciones visibles`}>
                <ExecutionHistory items={executions} />
              </DetailDisclosure>

              <DetailDisclosure title="Hint experimental" eyebrow={recommendation?.model || "Sin hint activo"}>
                <TaskHintFeedback
                  taskId={task.id}
                  taskType={task.task_type || "generic"}
                  recommendation={recommendation}
                />
              </DetailDisclosure>

              <DetailDisclosure title="Metadatos tecnicos" eyebrow="Referencia">
                <div className="info-block">
                  <div className="label">API base</div>
                  <div>{apiBaseUrl}</div>
                </div>
                <div className="info-block">
                  <div className="label">Task id</div>
                  <div>{task.id}</div>
                </div>
                <div className="info-block">
                  <div className="label">Project id</div>
                  <div>{task.project_id}</div>
                </div>
                <div className="stack compact">
                  <Link href={`/projects/${task.project_id}`} className="inline-link">
                    Volver al proyecto
                  </Link>
                  <Link href={`/tasks/workspace?taskId=${task.id}`} className="inline-link">
                    Volver al workspace
                  </Link>
                  <Link href="/tasks" className="inline-link">
                    Volver a Tasks
                  </Link>
                </div>
              </DetailDisclosure>
            </section>
          </div>
        </details>
      </div>
    </main>
  );
}
