import { useCallback, useEffect, useState } from "react";
import { api } from "./api.js";
import useLiveStream from "./useLiveStream.js";
import StatCards from "./components/StatCards.jsx";
import EventFeed from "./components/EventFeed.jsx";
import IncidentList from "./components/IncidentList.jsx";

const MAX_EVENTS = 300;

export default function App() {
  const [events, setEvents] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState(null);

  const loadStats = useCallback(() => api.stats().then(setStats).catch(() => {}), []);

  useEffect(() => {
    api.events({ limit: 100 }).then(setEvents).catch(() => {});
    api.incidents({ limit: 100 }).then(setIncidents).catch(() => {});
    loadStats();
    const timer = setInterval(loadStats, 10000);
    return () => clearInterval(timer);
  }, [loadStats]);

  const connected = useLiveStream((msg) => {
    if (msg.type === "event") {
      setEvents((prev) => [msg.data, ...prev].slice(0, MAX_EVENTS));
    } else if (msg.type === "incident") {
      setIncidents((prev) => {
        const exists = prev.some((i) => i.id === msg.data.id);
        return exists
          ? prev.map((i) => (i.id === msg.data.id ? msg.data : i))
          : [msg.data, ...prev];
      });
    }
    loadStats();
  });

  return (
    <div className="wrap">
      <header>
        <h1>Incident Monitor</h1>
        <span className={`status ${connected ? "up" : "down"}`}>
          {connected ? "Live" : "Reconnecting…"}
        </span>
      </header>

      <StatCards stats={stats} />

      <div className="columns">
        <EventFeed events={events} />
        <IncidentList incidents={incidents} />
      </div>
    </div>
  );
}
