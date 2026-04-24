import Link from "next/link";

import { getAssetDetailData } from "../../../lib/pwr-api";

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

function formatAssetType(value) {
  const normalized = String(value || "asset").toLowerCase();
  const labels = {
    output: "Resultado",
    preview: "Preview",
    briefing: "Briefing",
  };
  return labels[normalized] || normalized;
}

function PathRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="info-block">
      <div className="label">{label}</div>
      <div className="mono-text">{value}</div>
    </div>
  );
}

export default async function AssetDetailPage({ params }) {
  const { assetId } = await params;
  const { apiBaseUrl, asset, errors, missing } = await getAssetDetailData(assetId);

  if (!asset) {
    return (
      <main className="shell">
        <header className="topbar">
          <div className="topbar-inner">
            <div className="brand-block">
              <div className="brand">PWR</div>
              <div className="subtle">Detalle readonly de activo desde Next.js</div>
            </div>
            <div className="status-chip">API en revision</div>
          </div>
        </header>

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Activos</span>
            </div>
            <h1>{missing ? "Activo no encontrado" : "Activo no disponible"}</h1>
            <p>
              {missing
                ? "La API no devolvio ningun activo para este id."
                : "No fue posible cargar el activo desde FastAPI en este momento."}
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
              <div>
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

  return (
    <main className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-block">
            <div className="brand">PWR</div>
            <div className="subtle">Detalle readonly de activo desde Next.js</div>
          </div>
          <div className="status-chip ok">API conectada</div>
        </div>
      </header>

      <div className="page">
        <section className="hero">
          <div className="breadcrumbs">
            <Link href="/">Home</Link>
            <span>/</span>
            {asset.project_id ? <Link href={`/projects/${asset.project_id}`}>{asset.project_name || "Proyecto"}</Link> : null}
            {asset.project_id ? <span>/</span> : null}
            <span>{asset.title || `Activo ${asset.id}`}</span>
          </div>
          <h1>{asset.title || `Activo ${asset.id}`}</h1>
          <p>Vista readonly del activo reusable, consumida directamente desde FastAPI.</p>
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
                  <h2>Resumen del activo</h2>
                  <span className="badge executed">{formatAssetType(asset.asset_type)}</span>
                </div>
                <div className="stack">
                  <div className="info-block">
                    <div className="label">Resumen</div>
                    <div>{asset.summary || "Sin resumen visible para este activo."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Contenido</div>
                    <pre className="content-block">{asset.content || "Sin contenido visible para este activo."}</pre>
                  </div>
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Origen</h2>
                  <div className="subtle">Trazabilidad readonly</div>
                </div>
                <div className="stack">
                  <div className="info-block">
                    <div className="label">Proyecto</div>
                    <div>{asset.project_name || "Sin proyecto visible."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Tarea origen</div>
                    <div>{asset.task_title || "Sin tarea origen."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Run origen</div>
                    <div>{asset.source_execution_id || "Sin run origen."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Estado origen</div>
                    <div>{asset.source_execution_status || "Sin estado origen."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Provider / modelo</div>
                    <div>{asset.source_provider || asset.source_model ? `${asset.source_provider || "provider?"} / ${asset.source_model || "modelo?"}` : "Sin provider ni modelo visibles."}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Creado</div>
                    <div>{formatDate(asset.created_at)}</div>
                  </div>
                  <div className="info-block">
                    <div className="label">Actualizado</div>
                    <div>{formatDate(asset.updated_at || asset.created_at)}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <aside className="workspace-side">
            <div className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Portable paths</h2>
                  <div className="subtle">Readonly</div>
                </div>
                <div className="stack">
                  <PathRow label="Markdown" value={asset.artifact_md_path} />
                  <PathRow label="JSON" value={asset.artifact_json_path} />
                </div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-body stack">
                <div className="band-head">
                  <h2>Navegacion</h2>
                  <div className="subtle">Sin acciones mutables</div>
                </div>
                {asset.project_id ? (
                  <Link href={`/projects/${asset.project_id}`} className="inline-link">
                    Volver al proyecto
                  </Link>
                ) : null}
                <Link href="/" className="inline-link">
                  Volver a Home
                </Link>
              </div>
            </div>
          </aside>
        </section>
      </div>
    </main>
  );
}
