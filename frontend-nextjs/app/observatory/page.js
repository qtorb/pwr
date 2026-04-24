import Link from "next/link";

import { getModelObservatorySummaryData } from "../../lib/pwr-api";

export const dynamic = "force-dynamic";

function formatRate(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) return "—";
  return Number(value).toFixed(digits);
}

export default async function ObservatoryPage() {
  try {
    const { apiBaseUrl, summary, totalRuns } = await getModelObservatorySummaryData();

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
            <p>
              Vista minima para entender que modelos convierten mejor el trabajo real en activos reutilizables.
            </p>
            <div className="subtle">API base actual: {apiBaseUrl}</div>
            <div className="subtle">Runs visibles en el resumen: {totalRuns}</div>
          </section>

          <section className="panel">
            <div className="panel-body">
              <div className="band-head">
                <h2>Resumen por modelo</h2>
                <div className="subtle">Ordenado por conversion y reutilizacion</div>
              </div>

              {!summary.length ? (
                <div className="muted-box">No hay datos todavia</div>
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
                        <th>conversion_rate</th>
                        <th>reuse_rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.map((row) => (
                        <tr key={`${row.provider}-${row.model}-${row.task_type}`}>
                          <td>{row.provider || "—"}</td>
                          <td>{row.model || "—"}</td>
                          <td>{row.task_type || "—"}</td>
                          <td>{row.total_runs || 0}</td>
                          <td>{formatRate(row.success_rate)}</td>
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

          {summary.length ? (
            <section className="panel">
              <div className="panel-body">
                <div className="band-head">
                  <h2>Lectura rapida</h2>
                  <div className="subtle">Sin analitica avanzada</div>
                </div>
                <div className="summary-grid">
                  <div className="summary-pill">
                    <strong>{summary[0].model || "—"}</strong>
                    <span>
                      Mejor posicionado por conversion ({formatRate(summary[0].conversion_rate)}) y reutilizacion (
                      {formatRate(summary[0].reuse_rate)}).
                    </span>
                  </div>
                  <div className="summary-pill">
                    <strong>{formatNumber(summary[0].avg_cost_usd, 6)}</strong>
                    <span>Coste medio observado para el primer grupo</span>
                  </div>
                  <div className="summary-pill">
                    <strong>{formatNumber(summary[0].avg_latency_ms, 0)}</strong>
                    <span>Latencia media observada para el primer grupo</span>
                  </div>
                </div>
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
            <p>No fue posible cargar el resumen del observatorio con la API actual.</p>
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
