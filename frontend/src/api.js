async function request(path, options) {
  const res = await fetch(`/api${path}`, options);
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

export const api = {
  events: (params) => request(`/events?${new URLSearchParams(params)}`),
  incidents: (params) => request(`/incidents?${new URLSearchParams(params)}`),
  stats: () => request("/stats"),
  updateIncident: (id, changes) =>
    request(`/incidents/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(changes),
    }),
};

// timestamps from the API are UTC without a trailing Z
export const toDate = (ts) => new Date(ts.endsWith("Z") ? ts : ts + "Z");
