import Link from "next/link";

import AppHeader from "../../_components/app-header";
import { getTaskWorkspaceData } from "../../../lib/pwr-api";
import TaskWorkspaceClient from "./task-workspace-client";

export const dynamic = "force-dynamic";

export default async function TaskWorkspacePage({ searchParams }) {
  const resolvedSearchParams = (await searchParams) || {};
  const taskId = resolvedSearchParams.taskId || null;
  const projectId = resolvedSearchParams.projectId || null;
  const { apiBaseUrl, projects, selectedProject, taskData, errors } = await getTaskWorkspaceData(taskId, projectId);

  return (
    <main className="shell">
      <AppHeader subtitle="Workspace unificada para mover una tarea sin friccion" statusText="API conectada" statusTone="ok" />

      <div className="page">
        <section className="hero">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            <Link href="/tasks">Tasks</Link>
            <span>/</span>
            <span>Workspace</span>
          </div>
          <h1>Task Workspace</h1>
          <p>
            Carril minimo para definir una tarea, elegir modelo, copiar el prompt, ejecutar fuera de
            PWR y guardar el resultado sin abrir varias pantallas.
          </p>
          <div className="subtle">API base actual: {apiBaseUrl}</div>
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

        <TaskWorkspaceClient
          projects={projects}
          selectedProject={selectedProject}
          task={taskData?.task || null}
          latestExecution={taskData?.latestExecution || null}
          recommendation={taskData?.recommendation || null}
          flags={{
            created: resolvedSearchParams.created === "1",
            saved: resolvedSearchParams.saved === "1",
          }}
        />
      </div>
    </main>
  );
}
