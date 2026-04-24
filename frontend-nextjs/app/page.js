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
        <div className="row" key={`${item.project_id}-${item.id}`}>
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
        </div>
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
        <div className="row project-row" key={project.id}>
          <div className="row-top">
            <div className="row-title">{project.name}</div>
            {project.is_favorite ? <span className="badge executed">Favorito</span> : null}
          </div>
          <div className="subtle">{project.objective || project.description || "Sin objetivo definido."}</div>
          <div className="project-stats">
            <span>{project.task_count || 0} tareas</span>
            <span>{project.asset_count || 0} activos</span>
            <span>{formatDate(project.updated_at || project.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default async function HomePage() {
  const { apiBaseUrl, health, activity, reentry, projects, errors } = await getShellHomeData();

  return (
    <main className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-block">
            <div className="brand">PWR</div>
            <div className="subtle">Next.js shell paralela sobre FastAPI</div>
          </div>
          <div className={`status-chip ${health?.status === "ok" ? "ok" : ""}`}>
            API {health?.status === "ok" ? "conectada" : "no disponible"}
          </div>
        </div>
      </header>

      <div className="page">
        <section className="hero">
          <h1>Home MVP paralela</h1>
          <p>
            Esta shell demuestra que PWR ya puede vivir fuera de Streamlit sin duplicar logica.
            Home consume FastAPI directamente y mantiene a Streamlit como runtime principal durante la transicion.
          </p>
          <div className="subtle">API base actual: {apiBaseUrl}</div>
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
            <h2>Home</h2>
            <div className="subtle">Primera shell Next.js centrada en actividad, reentrada y proyectos.</div>
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
                  <div className="subtle">Listado base para la siguiente fase</div>
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
