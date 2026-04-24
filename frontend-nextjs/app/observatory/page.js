import Link from "next/link";

import { getModelObservatorySummaryData } from "../../lib/pwr-api";

export const dynamic = "force-dynamic";

function formatRate(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) return "-";
  return Number(value).toFixed(digits);
}

function formatTaskType(value) {
  return value || "generic";
}

function BestHintCard({ hint }) {
  return (
    <div className="summary-pill" key={`${hint.provider}-${hint.model}-${hint.task_type}`}>
      <strong>{hint.model || "-"}</strong>
      <span>{hint.provider || "-"} · {formatTaskType(hint.task_type)}</span>
      <span>score {formatNumber(hint.score, 4)} · confianza {hint.confidence || "-"}</span>
      <span>
        quality {formatNumber(hint.quality_score, 4)} · cost {formatNumber(hint.cost_efficiency, 4)} · latency{" "}
        {formatNumber(hint.latency_efficiency, 4)} · reliability {formatNumber(hint.reliability_score, 4)}
      </span>
      <span>{hint.reason || "Sin motivo disponible."}</span>
    </div>
  );
}

export default async function ObservatoryPage() {
  try {
    const { apiBaseUrl, summary, bestHints, totalRuns } = await getModelObservatorySummaryData();

    return (
      <main className="shell">
        <header className="topbar">
          <div className="topbar-inner">
            <div className="brand-block">
              <div className="brand">PWR</div>
              <div className="subtle">Model Observatory minimal desde Next.js</div>
            </div>
            <div className="status-chip ok">API conectada</div>
          </div>
        </header>

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Observatorio</span>
            </div>
            <h1>Model Observatory</h1>
            <p>Aprendizaje observable sobre uso de modelos. No ejecuta routing automatico.</p>
            <div className="subtle">API base actual: {apiBaseUrl}</div>
            <div className="subtle">Runs visibles en el resumen: {totalRuns}</div>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="band-head">
                <h2>Resumen por modelo</h2>
                <div className="subtle">Metricas observadas sobre uso real y conversion en activos.</div>
              </div>

              {!summary.length ? (
                <div className="muted-box">Todavia no hay suficientes ejecuciones observadas.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>provider</th>
                        <th>model</th>
                        <th>task_type</th>
                        <th>total_runs</th>
                        <th>success_rate</th>
                        <th>preview_rate</th>
                        <th>failed_rate</th>
                        <th>avg_latency_ms</th>
                        <th>avg_cost_usd</th>
                        <th>conversion_rate</th>
                        <th>reuse_rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.map((row) => (
                        <tr key={`${row.provider}-${row.model}-${row.task_type}`}>
                          <td>{row.provider || "-"}</td>
                          <td>{row.model || "-"}</td>
                          <td>{formatTaskType(row.task_type)}</td>
                          <td>{row.total_runs || 0}</td>
                          <td>{formatRate(row.success_rate)}</td>
                          <td>{formatRate(row.preview_rate)}</td>
                          <td>{formatRate(row.failed_rate)}</td>
                          <td>{formatNumber(row.avg_latency_ms, 0)}</td>
                          <td>{formatNumber(row.avg_cost_usd, 6)}</td>
                          <td>{formatRate(row.conversion_rate)}</td>
                          <td>{formatRate(row.reuse_rate)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </section>

          {bestHints.length ? (
            <section className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Best hints</h2>
                  <div className="subtle">Hints experimentales por task_type. No cambian el routing real.</div>
                </div>
                <div className="summary-grid">
                  {bestHints.map((hint) => (
                    <BestHintCard hint={hint} key={`${hint.provider}-${hint.model}-${hint.task_type}`} />
                  ))}
                </div>
              </div>
            </section>
          ) : summary.length ? (
            <section className="panel">
              <div className="panel-body">
                <div className="muted-box">Todavia no hay hints experimentales suficientes para mostrar.</div>
              </div>
            </section>
          ) : null}
        </div>
      </main>
    );
  } catch (error) {
    return (
      <main className="shell">
        <header className="topbar">
          <div className="topbar-inner">
            <div className="brand-block">
              <div className="brand">PWR</div>
              <div className="subtle">Model Observatory minimal desde Next.js</div>
            </div>
            <div className="status-chip">Error</div>
          </div>
        </header>

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Observatorio</span>
            </div>
            <h1>Model Observatory</h1>
            <p>No fue posible cargar el observatorio con la API actual.</p>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="feedback-banner error">
                {error instanceof Error ? error.message : "Error desconocido al cargar el observatorio."}
              </div>
            </div>
          </section>
        </div>
      </main>
    );
  }
}
