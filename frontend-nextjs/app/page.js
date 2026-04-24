import Link from "next/link";

import AppHeader from "./_components/app-header";
import { getShellHomeData } from "../lib/pwr-api";

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

function TaskList({ items, emptyMessage }) {
  if (!items.length) {
    return <div className="muted-box">{emptyMessage}</div>;
  }

  return (
    <div className="list">
      {items.map((item) => (
        <Link className="row row-link" key={`${item.project_id}-${item.id}`} href={`/tasks/${item.id}`}>
          <div className="row-top">
            <div className="row-title">{item.title || "Tarea sin titulo"}</div>
            <StateBadge state={item.execution_status} />
          </div>
          <div className="row-meta">
            <span>{item.project_name || "Sin proyecto"}</span>
            <span>{item.task_type || "Pensar"}</span>
            <span>{formatDate(item.updated_at)}</span>
            {item.suggested_model ? <span>{item.suggested_model}</span> : null}
          </div>
        </Link>
      ))}
    </div>
  );
}

function ProjectList({ items }) {
  if (!items.length) {
    return <div className="muted-box">La API no devolvio proyectos todavia.</div>;
  }

  return (
    <div className="list">
      {items.map((project) => (
        <Link className="row project-row row-link" key={project.id} href={`/projects/${project.id}`}>
          <div className="row-top">
            <div className="row-title">{project.name}</div>
            {project.is_favorite ? <span className="badge executed">Favorito</span> : null}
          </div>
          <div className="subtle">{project.objective || project.description || "Sin objetivo definido."}</div>
          <div className="project-stats">
            <span>{project.task_count || 0} tareas</span>
            <span>{project.asset_count || 0} activos</span>
            <span>{formatDate(project.last_activity_at || project.updated_at || project.created_at)}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}

export default async function HomePage() {
  const { apiBaseUrl, health, activity, reentry, projects, errors } = await getShellHomeData();

  return (
    <main className="shell">
      <AppHeader
        subtitle="Shell operativa sobre FastAPI para uso real"
        statusText={`API ${health?.status === "ok" ? "conectada" : "no disponible"}`}
        statusTone={health?.status === "ok" ? "ok" : "default"}
      />

      <div className="page">
        <section className="hero hero-home">
          <div className="hero-copy">
            <h1>PWR listo para dogfooding</h1>
            <p>
              La shell Next.js ya cubre el loop principal sin duplicar la logica del producto. Esta capa
              esta pensada para usar PWR varias veces al dia con menos friccion y mas calma visual.
            </p>
            <div className="subtle">API base actual: {apiBaseUrl}</div>
          </div>

          <div className="hero-actions">
            <Link href="/tasks/workspace" className="hero-primary">
              Abrir task workspace
            </Link>
            <Link href="/projects" className="hero-primary">
              Crear proyecto
            </Link>
            <Link href="/projects" className="hero-secondary">
              Ver projects
            </Link>
          </div>

          {errors.length ? (
            <div className="muted-box">
              Se detectaron respuestas incompletas desde la API:
              <ul>
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>

        <section className="band">
          <div className="band-head">
            <h2>Entrada</h2>
            <div className="subtle">Actividad reciente, reentrada y proyectos en una sola pantalla calmada.</div>
          </div>
          <div className="grid home">
            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Hoy</h2>
                  <div className="subtle">Actividad reciente desde FastAPI</div>
                </div>
              </div>
              <TaskList items={activity} emptyMessage="Sin actividad reciente hoy." />
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Para retomar</h2>
                  <div className="subtle">Estados accionables para volver al trabajo</div>
                </div>
              </div>
              <TaskList items={reentry} emptyMessage="Sin tareas abiertas o con fallo para retomar." />
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Proyectos</h2>
                  <div className="subtle">Entrada natural para crear y entender tareas con contexto</div>
                </div>
              </div>
              <ProjectList items={projects} />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
