import Link from "next/link";
import { notFound } from "next/navigation";

import { getProjectWorkspaceData } from "../../../lib/pwr-api";

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

function TaskList({ items }) {
  if (!items.length) {
    return <div className="muted-box">Este proyecto todavia no tiene tareas visibles en la API.</div>;
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
            <span>{task.task_type || "Pensar"}</span>
            <span>{formatDate(task.updated_at)}</span>
            {task.suggested_model ? <span>{task.suggested_model}</span> : null}
          </div>
          <div className="subtle">
            {task.router_summary || task.description || task.context || "Sin resumen visible para esta tarea."}
          </div>
        </Link>
      ))}
    </div>
  );
}

function AssetList({ items }) {
  if (!items.length) {
    return <div className="muted-box">Este proyecto todavia no tiene activos visibles en la API.</div>;
  }

  return (
    <div className="list">
      {items.map((asset) => (
        <div className="row" key={asset.id}>
          <div className="row-top">
            <div className="row-title">{asset.title || "Activo sin titulo"}</div>
            <span className="badge executed">{asset.asset_type || "asset"}</span>
          </div>
          <div className="row-meta">
            {asset.task_title ? <span>{asset.task_title}</span> : null}
            {asset.source_execution_status ? <span>{asset.source_execution_status}</span> : null}
            <span>{formatDate(asset.updated_at || asset.created_at)}</span>
          </div>
          <div className="subtle">{asset.summary || "Sin resumen visible para este activo."}</div>
          <div>
            <Link className="inline-link" href={`/projects/${asset.project_id}/assets/${asset.id}/reuse`}>
              Usar como base
            </Link>
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function ProjectWorkspacePage({ params }) {
  const { projectId } = await params;
  const { apiBaseUrl, project, tasks, assets, errors } = await getProjectWorkspaceData(projectId);

  if (!project) {
    notFound();
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-block">
            <div className="brand">PWR</div>
            <div className="subtle">Project workspace readonly desde Next.js</div>
          </div>
          <div className="status-chip ok">API conectada</div>
        </div>
      </header>

      <div className="page">
        <section className="hero">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            <span>{project.name}</span>
          </div>
          <h1>{project.name}</h1>
          <p>
            Primera vista de proyecto en modo solo lectura. Streamlit sigue vivo; esta shell solo demuestra
            que proyecto, tareas y activos ya pueden consumirse desde FastAPI.
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

        <section className="workspace-grid">
          <div className="workspace-main">
            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Contexto del proyecto</h2>
                  <div className="subtle">Solo lectura</div>
                </div>
                <div className="stack">
                  <div className="info-block">
                    <div className="label">Descripción</div>
                    <div>{project.description || "Sin descripción definida."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Objetivo</div>
                    <div>{project.objective || "Sin objetivo definido."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Base context</div>
                    <div>{project.base_context || "Sin base context visible."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Base instructions</div>
                    <div>{project.base_instructions || "Sin base instructions visibles."}</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Tareas</h2>
                  <div className="subtle">{tasks.length} visibles</div>
                </div>
              </div>
              <TaskList items={tasks} />
            </div>
          </div>

          <aside className="workspace-side">
            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Resumen</h2>
                  <div className="subtle">Proyecto readonly</div>
                </div>
                <div className="summary-grid">
                  <div className="summary-pill">
                    <strong>{tasks.length}</strong>
                    <span>Tareas</span>
                  </div>
                  <div className="summary-pill">
                    <strong>{assets.length}</strong>
                    <span>Activos</span>
                  </div>
                  <div className="summary-pill">
                    <strong>{project.slug || "sin-slug"}</strong>
                    <span>Slug</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Activos relacionados</h2>
                  <div className="subtle">{assets.length} visibles</div>
                </div>
              </div>
              <AssetList items={assets} />
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
