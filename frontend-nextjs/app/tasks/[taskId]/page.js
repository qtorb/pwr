import Link from "next/link";

import AppHeader from "../../_components/app-header";
import { getTaskDetailData } from "../../../lib/pwr-api";
import TaskAssetPanel from "./task-asset-panel";
import TaskExecutionPanel from "./task-execution-panel";
import TaskHintFeedback from "./task-hint-feedback";

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
    return <div className="muted-box">Sin ejecuciones todavia.</div>;
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

function OutputPanel({ task, latestExecution }) {
  const state = String(
    latestExecution?.execution_status || task?.execution_status || task?.status || "pending",
  ).toLowerCase();
  const outputText = latestExecution?.output_text || task?.llm_output || "";
  const errorText = latestExecution?.error_message || "";

  if (state === "failed") {
    return (
      <div className="info-block">
        <div className="label">Error</div>
        <pre className="content-block">
          {errorText || task?.router_summary || "Sin error visible para esta tarea."}
        </pre>
      </div>
    );
  }

  if (state === "executed" || state === "preview") {
    return (
      <div className="info-block">
        <div className="label">{state === "preview" ? "Preview" : "Resultado"}</div>
        <pre className="content-block">
          {outputText || task?.router_summary || "Sin resultado visible para esta tarea."}
        </pre>
      </div>
    );
  }

  return (
    <div className="muted-box">
      Esta tarea todavia no tiene una salida visible. Cuando exista una ejecucion, aparecera aqui.
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
  const briefingContent = String(task.context || task.description || task.router_summary || "").trim();
  const canSaveAsset =
    ["preview", "executed"].includes(String(taskState).toLowerCase()) && Boolean(resultContent || briefingContent);
  const defaultAssetType = String(taskState).toLowerCase() === "preview" ? "preview" : "output";
  const projectLabel = task.project_name || `Proyecto ${task.project_id}`;

  return (
    <main className="shell">
      <AppHeader subtitle="Detalle operativo de tarea" statusText="API conectada" statusTone="ok" />

      <div className="page">
        <section className="hero">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            <Link href="/projects">Projects</Link>
            <span>/</span>
            <Link href={`/projects/${task.project_id}`}>{projectLabel}</Link>
            <span>/</span>
            <span>{task.title || `Tarea ${task.id}`}</span>
          </div>
          <div className="row-top">
            <h1>{task.title || `Tarea ${task.id}`}</h1>
            <StateBadge state={taskState} />
          </div>
          <p>
            Detalle operativo de la tarea sobre FastAPI. Desde aqui puedes revisar contexto, ejecutar y
            convertir resultado en activo reutilizable.
          </p>
          <div className="subtle">API base actual: {apiBaseUrl}</div>
        </section>

        <TaskHintFeedback
          taskId={task.id}
          taskType={task.task_type || "generic"}
          recommendation={recommendation}
        />

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

        <section className="workspace-grid">
          <div className="workspace-main">
            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Tarea</h2>
                  <div className="subtle">Contexto operativo</div>
                </div>
                <div className="stack">
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
                    <div className="label">Resumen</div>
                    <div>{task.description || task.router_summary || "Sin resumen visible para esta tarea."}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Briefing</h2>
                  <div className="subtle">Base de trabajo actual</div>
                </div>
                <div className="info-block">
                  <div className="label">Contexto</div>
                  <pre className="content-block">
                    {task.context || task.description || "Sin contexto visible para esta tarea."}
                  </pre>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Ejecucion</h2>
                  <div className="subtle">Ultimo intento conocido</div>
                </div>
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
                  <div className="muted-box">Sin ejecuciones todavia.</div>
                )}
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Resultado</h2>
                  <div className="subtle">Ultima salida visible</div>
                </div>
                <OutputPanel task={task} latestExecution={latestExecution} />
              </div>
            </div>
          </div>

          <aside className="workspace-side">
            <TaskExecutionPanel taskId={task.id} currentState={taskState} />
            {canSaveAsset ? (
              <TaskAssetPanel
                taskId={task.id}
                projectId={task.project_id}
                projectHref={`/projects/${task.project_id}`}
                defaultAssetType={defaultAssetType}
                defaultTitle={task.title || `Tarea ${task.id}`}
                defaultSummary=""
                resultContent={resultContent}
                briefingContent={briefingContent}
                sourceExecutionId={latestExecution?.id || null}
                sourceExecutionStatus={taskState}
              />
            ) : null}

            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Navegacion</h2>
                  <div className="subtle">Movimiento rapido</div>
                </div>
                <Link href={`/projects/${task.project_id}`} className="inline-link">
                  Volver al proyecto
                </Link>
                <Link href="/" className="inline-link">
                  Volver a Home
                </Link>
                <Link href="/tasks" className="inline-link">
                  Volver a Tasks
                </Link>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Historial</h2>
                  <div className="subtle">{executions.length} ejecuciones visibles</div>
                </div>
              </div>
              <ExecutionHistory items={executions} />
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
