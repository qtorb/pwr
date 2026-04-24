import Link from "next/link";

import AppHeader from "../_components/app-header";
import { getProjectsPageData } from "../../lib/pwr-api";
import ProjectCreatePanel from "./project-create-panel";

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

function ProjectList({ items }) {
  if (!items.length) {
    return (
      <div className="muted-box">
        Todavia no hay proyectos visibles. Crea el primero para empezar a trabajar con contexto real.
      </div>
    );
  }

  return (
    <div className="list">
      {items.map((project) => (
        <Link className="row row-link project-row" key={project.id} href={`/projects/${project.id}`}>
          <div className="row-top">
            <div className="row-title">{project.name}</div>
            {project.is_favorite ? <span className="badge executed">Favorito</span> : null}
          </div>
          <div className="subtle">{project.description || project.objective || "Sin descripcion visible."}</div>
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

export default async function ProjectsPage() {
  const { apiBaseUrl, projects, errors } = await getProjectsPageData();

  return (
    <main className="shell">
      <AppHeader
        subtitle="Proyectos como contenedor principal del trabajo"
        statusText="API conectada"
        statusTone="ok"
      />

      <div className="page">
        <section className="hero">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            <span>Projects</span>
          </div>
          <h1>Projects</h1>
          <p>
            Los proyectos son la estructura minima que da contexto a tareas, ejecuciones, hints, feedback y
            activos. La tarea deja de estar aislada y pasa a vivir dentro de su contenedor natural.
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
                  <h2>Lista de proyectos</h2>
                  <div className="subtle">{projects.length} visibles</div>
                </div>
              </div>
              <ProjectList items={projects} />
            </div>
          </div>

          <aside className="workspace-side">
            <ProjectCreatePanel />

            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Modelo</h2>
                  <div className="subtle">Jerarquia base</div>
                </div>
                <div className="info-block">
                  <div className="label">Estructura</div>
                  <div>Proyecto -&gt; Tareas -&gt; Ejecuciones / Hints / Feedback / Outputs</div>
                </div>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
