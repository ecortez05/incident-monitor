import { useState } from "react";
import { api, toDate } from "../api.js";

const FILTERS = [
  ["active", "Active"],
  ["resolved", "Resolved"],
  ["all", "All"],
];

export default function IncidentList({ incidents }) {
  const [filter, setFilter] = useState("active");
  const [error, setError] = useState("");

  const shown = incidents.filter((i) => {
    if (filter === "active") return i.status !== "resolved";
    if (filter === "resolved") return i.status === "resolved";
    return true;
  });

  // the websocket pushes the updated incident back, so no local state to patch
  async function change(id, status) {
    setError("");
    try {
      await api.updateIncident(id, { status });
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Incidents</h2>
        <div className="tabs">
          {FILTERS.map(([value, label]) => (
            <button key={value} className={`small ${filter === value ? "active" : ""}`} onClick={() => setFilter(value)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <ul className="incidents">
        {shown.length === 0 && <li className="empty">No incidents.</li>}
        {shown.map((i) => (
          <li key={i.id}>
            <div className="top">
              <span className={`tag ${i.severity}`}>{i.severity}</span>
              <strong>{i.title}</strong>
            </div>
            <div className="meta">
              #{i.id} · {i.status} · opened {toDate(i.created_at).toLocaleString()}
              {i.auto_created && " · auto-detected"}
            </div>
            <div className="actions">
              {i.status === "open" && <button className="small" onClick={() => change(i.id, "acknowledged")}>Acknowledge</button>}
              {i.status !== "resolved" && <button className="small" onClick={() => change(i.id, "resolved")}>Resolve</button>}
              {i.status === "resolved" && <button className="small" onClick={() => change(i.id, "open")}>Reopen</button>}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
