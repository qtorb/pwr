import AppHeader from "../_components/app-header";

export default function Loading() {
  return (
    <main className="shell">
      <AppHeader subtitle="Observatorio minimo sobre uso real de modelos" statusText="Cargando" statusTone="default" />

      <div className="page">
        <section className="hero">
          <h1>Model Observatory</h1>
          <p>Cargando observatorio...</p>
        </section>
      </div>
    </main>
  );
}
