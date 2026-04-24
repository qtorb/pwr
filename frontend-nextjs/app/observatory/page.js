import Link from "next/link";

import AppHeader from "../_components/app-header";
import { getModelObservatorySummaryData } from "../../lib/pwr-api";

export const dynamic = "force-dynamic";

function formatRate(value) {
  return new Intl.NumberFormat("es-ES", {
    style: "percent",
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  }).format(Number(value || 0));
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) return "-";
  return new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(Number(value));
}

function formatTaskType(value) {
  return value || "generic";
}

function BestHintCard({ hint }) {
  return (
    <div className="summary-pill observatory-hint-card" key={`${hint.provider}-${hint.model}-${hint.task_type}`}>
      <strong>{hint.model || "-"}</strong>
      <span>
        {hint.provider || "-"} | {formatTaskType(hint.task_type)}
      </span>
      <span>
        score {formatNumber(hint.score, 3)} | confianza {hint.confidence || "-"}
      </span>
      <span>
        quality {formatNumber(hint.quality_score, 3)} | cost {formatNumber(hint.cost_efficiency, 3)} |
        latency {formatNumber(hint.latency_efficiency, 3)} | reliability {formatNumber(hint.reliability_score, 3)}
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
        <AppHeader subtitle="Observatorio minimo sobre uso real de modelos" statusText="API conectada" statusTone="ok" />

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Observatory</span>
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
                <div className="subtle">Metricas observadas sobre uso real, coste, latencia y conversion.</div>
              </div>

              {!summary.length ? (
                <div className="muted-box">Todavia no hay suficientes ejecuciones observadas.</div>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Provider</th>
                        <th>Model</th>
                        <th>Task type</th>
                        <th className="num">Runs</th>
                        <th className="num">Success</th>
                        <th className="num">Preview</th>
                        <th className="num">Failed</th>
                        <th className="num">Latency</th>
                        <th className="num">Cost</th>
                        <th className="num">Conversion</th>
                        <th className="num">Reuse</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.map((row) => (
                        <tr key={`${row.provider}-${row.model}-${row.task_type}`}>
                          <td>{row.provider || "-"}</td>
                          <td>{row.model || "-"}</td>
                          <td>{formatTaskType(row.task_type)}</td>
                          <td className="num">{row.total_runs || 0}</td>
                          <td className="num">{formatRate(row.success_rate)}</td>
                          <td className="num">{formatRate(row.preview_rate)}</td>
                          <td className="num">{formatRate(row.failed_rate)}</td>
                          <td className="num">{row.avg_latency_ms === null || row.avg_latency_ms === undefined ? "-" : `${formatNumber(row.avg_latency_ms, 0)} ms`}</td>
                          <td className="num">{formatNumber(row.avg_cost_usd, 3)}</td>
                          <td className="num">{formatRate(row.conversion_rate)}</td>
                          <td className="num">{formatRate(row.reuse_rate)}</td>
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
                  <div className="subtle">Hints experimentales por task type. No cambian el routing real.</div>
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
        <AppHeader subtitle="Observatorio minimo sobre uso real de modelos" statusText="Error" statusTone="default" />

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <span>Observatory</span>
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
