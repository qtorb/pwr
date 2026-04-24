import Link from "next/link";
import { redirect } from "next/navigation";

import { reuseAssetToTask } from "../../../../../../lib/pwr-api";

export const dynamic = "force-dynamic";

export default async function ReuseAssetPage({ params }) {
  const { projectId, assetId } = await params;

  try {
    const { createdTask } = await reuseAssetToTask(projectId, assetId);
    redirect(`/tasks/${createdTask.id}?fromAsset=1&assetId=${assetId}`);
  } catch (error) {
    if (error && typeof error === "object" && String(error.digest || "").startsWith("NEXT_REDIRECT")) {
      throw error;
    }

    return (
      <main className="shell">
        <header className="topbar">
          <div className="topbar-inner">
            <div className="brand-block">
              <div className="brand">PWR</div>
              <div className="subtle">Reutilizacion de activo desde Next.js</div>
            </div>
            <div className="status-chip">Error</div>
          </div>
        </header>

        <div className="page">
          <section className="hero">
            <div className="breadcrumbs">
              <Link href="/">Home</Link>
              <span>/</span>
              <Link href={`/projects/${projectId}`}>Proyecto {projectId}</Link>
              <span>/</span>
              <span>Reutilizar activo</span>
            </div>
            <h1>No fue posible crear la tarea desde el activo</h1>
            <p>La shell no pudo reutilizar este activo con la API actual.</p>
          </section>

          <section className="panel">
            <div className="panel-body stack">
              <div className="feedback-banner error">
                {error instanceof Error ? error.message : "Error desconocido al reutilizar el activo."}
              </div>
              <Link href={`/projects/${projectId}`} className="inline-link">
                Volver al proyecto
              </Link>
            </div>
          </section>
        </div>
      </main>
    );
  }
}
