import Link from "next/link";

import AppHeader from "../_components/app-header";
import { getShellHomeData } from "../../lib/pwr-api";
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

function uniqueTasks(...groups) {
  const seen = new Set();
  const items = [];

  groups.flat().forEach((task) => {
    const key = String(task?.id || "");
    if (!key || seen.has(key)) return;
    seen.add(key);
    items.push(task);
  });

  return items;
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
          </div>
          <div className="subtle">
            {task.router_summary || task.description || task.context || "Sin contexto visible para esta tarea."}
          </div>
        </Link>
      ))}
    </div>
  );
}

export default async function TasksPage() {
  const { apiBaseUrl, activity, reentry, projects, errors } = await getShellHomeData();
  const visibleTasks = uniqueTasks(reentry, activity);

  return (
    <main className="shell">
      <AppHeader
        subtitle="Tareas y arranque rapido sobre FastAPI"
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
            <h1>Tareas</h1>
            <p>
              Entrada operativa simple para arrancar trabajo nuevo y revisar tareas activas sin salir de la
              shell Next.js.
            </p>
            <div className="subtle">API base actual: {apiBaseUrl}</div>
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
              <div className="panel-body">
                <div className="band-head">
                  <h2>Para retomar</h2>
                  <div className="subtle">Estados que probablemente necesitan accion</div>
                </div>
              </div>
              <TaskList items={reentry} emptyMessage="No hay tareas abiertas o con fallo para retomar." />
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Recientes</h2>
                  <div className="subtle">{visibleTasks.length} tareas visibles</div>
                </div>
              </div>
              <TaskList items={visibleTasks} emptyMessage="Todavia no hay tareas recientes visibles." />
            </div>
          </div>

          <aside className="workspace-side">
            <TaskQuickCreatePanel projects={projects} />

            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Proyectos</h2>
                  <div className="subtle">Para crear sin perder contexto</div>
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
