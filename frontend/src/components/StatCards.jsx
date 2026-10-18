const LEVELS = ["info", "warning", "error", "critical"];

export default function StatCards({ stats }) {
  const byLevel = stats?.events_by_level || {};
  return (
    <section className="cards">
      <div className="card">
        <span className="label">Events (1h)</span>
        <strong>{stats ? stats.events_last_hour : "–"}</strong>
      </div>
      <div className="card">
        <span className="label">Open incidents</span>
        <strong className={stats?.open_incidents ? "bad" : ""}>{stats ? stats.open_incidents : "–"}</strong>
      </div>
      {LEVELS.slice(1).map((level) => (
        <div className="card" key={level}>
          <span className="label">{level}s (1h)</span>
          <strong>{stats ? byLevel[level] || 0 : "–"}</strong>
        </div>
      ))}
    </section>
  );
}
