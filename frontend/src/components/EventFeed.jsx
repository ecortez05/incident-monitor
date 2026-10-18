import { useMemo, useState } from "react";
import { toDate } from "../api.js";

const LEVELS = ["debug", "info", "warning", "error", "critical"];

export default function EventFeed({ events }) {
  const [levels, setLevels] = useState(new Set(LEVELS));
  const [search, setSearch] = useState("");
  const [paused, setPaused] = useState(false);
  const [frozen, setFrozen] = useState([]);

  function toggle(level) {
    const next = new Set(levels);
    next.has(level) ? next.delete(level) : next.add(level);
    setLevels(next);
  }

  function togglePause() {
    if (!paused) setFrozen(events);
    setPaused(!paused);
  }

  const source = paused ? frozen : events;
  const shown = useMemo(() => {
    const term = search.toLowerCase();
    return source.filter(
      (e) =>
        levels.has(e.level) &&
        (!term || e.message.toLowerCase().includes(term) || e.source.toLowerCase().includes(term))
    );
  }, [source, levels, search]);

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Live events</h2>
        <button className="small" onClick={togglePause}>{paused ? "Resume" : "Pause"}</button>
      </div>

      <div className="filters">
        {LEVELS.map((l) => (
          <label key={l} className={`chip ${l} ${levels.has(l) ? "on" : ""}`}>
            <input type="checkbox" checked={levels.has(l)} onChange={() => toggle(l)} />
            {l}
          </label>
        ))}
        <input className="search" placeholder="Filter by source or message" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <ul className="feed">
        {shown.length === 0 && <li className="empty">Nothing to show.</li>}
        {shown.map((e) => (
          <li key={e.id}>
            <time>{toDate(e.created_at).toLocaleTimeString()}</time>
            <span className={`tag ${e.level}`}>{e.level}</span>
            <b>{e.source}</b>
            <span className="msg">{e.message}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
