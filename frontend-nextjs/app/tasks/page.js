import Link from "next/link";

import AppHeader from "../_components/app-header";
import { getTasksPageData } from "../../lib/pwr-api";
import TaskQuickCreatePanel from "./task-quick-create-panel";

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

function FilterRow({ projects, selectedProjectId }) {
  return (
    <div className="filter-row">
      <Link
        href="/tasks"
        className={`filter-chip${selectedProjectId ? "" : " active"}`}
      >
        Todas
      </Link>
      {projects.map((project) => (
        <Link
          key={project.id}
          href={`/tasks?project_id=${project.id}`}
          className={`filter-chip${String(selectedProjectId || "") === String(project.id) ? " active" : ""}`}
        >
          {project.name}
        </Link>
      ))}
    </div>
  );
}

function TaskList({ items, emptyMessage }) {
  if (!items.length) {
    return <div className="muted-box">{emptyMessage}</div>;
  }

  return (
    <div className="list">
      {items.map((task) => (
        <Link className="row row-link" key={task.id} href={`/tasks/${task.id}`}>
          <div className="row-top">
            <div className="row-title">{task.title || "Tarea sin titulo"}</div>
            <StateBadge state={task.execution_status} />
          </div>
          <div className="row-meta">
            <span>{task.project_name || `Proyecto ${task.project_id}`}</span>
            <span>{task.task_type || "Pensar"}</span>
            <span>{formatDate(task.updated_at)}</span>
            {task.suggested_model ? <span>{task.suggested_model}</span> : null}
          </div>
          <div className="subtle">
            {task.description || task.context || task.router_summary || "Sin contexto visible para esta tarea."}
          </div>
        </Link>
      ))}
    </div>
  );
}

export default async function TasksPage({ searchParams }) {
  const resolvedSearchParams = (await searchParams) || {};
  const selectedProjectId = resolvedSearchParams.project_id || null;
  const { apiBaseUrl, tasks, projects, selectedProject, errors } = await getTasksPageData(selectedProjectId);

  return (
    <main className="shell">
      <AppHeader
        subtitle="Vista global de tareas con contexto de proyecto"
        statusText="API conectada"
        statusTone="ok"
      />

      <div className="page">
        <section className="hero hero-home">
          <div className="hero-copy">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Tasks</span>
            </div>
            <h1>{selectedProject ? `Tareas de ${selectedProject.name}` : "Tasks"}</h1>
            <p>
              La vista global sigue existiendo, pero cada tarea deja claro a qu&eacute; proyecto pertenece.
              El flujo preferente es entrar por proyecto y crear trabajo dentro de su contexto.
            </p>
            <div className="subtle">API base actual: {apiBaseUrl}</div>
          </div>
          <div className="hero-actions">
            <Link href="/tasks/workspace" className="hero-primary">
              Abrir task workspace
            </Link>
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

        <section className="workspace-grid">
          <div className="workspace-main">
            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Filtro por proyecto</h2>
                  <div className="subtle">
                    {selectedProject ? "Mostrando un solo proyecto" : "Mostrando todas las tareas visibles"}
                  </div>
                </div>
                <FilterRow projects={projects} selectedProjectId={selectedProjectId} />
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Lista global</h2>
                  <div className="subtle">{tasks.length} tareas visibles</div>
                </div>
              </div>
              <TaskList
                items={tasks}
                emptyMessage={
                  selectedProject
                    ? "Este proyecto todavia no tiene tareas visibles."
                    : "Todavia no hay tareas visibles en la API."
                }
              />
            </div>
          </div>

          <aside className="workspace-side">
            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Task Workspace</h2>
                  <div className="subtle">Carril rapido para escribir, copiar y guardar</div>
                </div>
                <Link href="/tasks/workspace" className="hero-primary">
                  Abrir workspace
                </Link>
              </div>
            </div>

            <TaskQuickCreatePanel projects={projects} />

            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Ir a projects</h2>
                  <div className="subtle">Entrada natural al trabajo</div>
                </div>
                {projects.slice(0, 6).map((project) => (
                  <Link key={project.id} href={`/projects/${project.id}`} className="inline-link">
                    {project.name}
                  </Link>
                ))}
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
