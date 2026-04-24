export default function Loading() {
  return (
    <main className="shell">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand-block">
            <div className="brand">PWR</div>
            <div className="subtle">Model Observatory minimal desde Next.js</div>
          </div>
          <div className="status-chip">Cargando</div>
        </div>
      </header>

      <div className="page">
        <section className="hero">
          <h1>Model Observatory</h1>
          <p>Cargando observatorio...</p>
        </section>
      </div>
    </main>
  );
}
