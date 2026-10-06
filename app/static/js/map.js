(function () {
  const cfg = window.GM;
  const map = L.map("map").setView([cfg.lat, cfg.lng], cfg.zoom);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const searchEl = document.getElementById("search");
  const cityEl = document.getElementById("city");
  const gatingEl = document.getElementById("gating");
  const countEl = document.getElementById("count");

  let allFeatures = [];
  let layer = null;

  // User-submitted text must always be escaped before going into HTML.
  function esc(value) {
    return String(value ?? "").replace(/[&<>"']/g, (c) => (
      { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
    ));
  }

  function colorFor(props) {
    return cfg.colors[props.gating_status] || "#7f8c8d";
  }

  function popupHtml(p) {
    const rows = [];
    const add = (label, value) => { if (value) rows.push(`<dt>${label}:</dt><dd>${esc(value)}</dd>`); };
    add("City", p.city);
    add("Barangay", p.barangay);
    add("Also known as", p.alt_names);
    add("Entry points", p.entry_points);
    add("Last verified", p.last_verified);
    add("Notes", p.notes);
    return `
      <div class="popup">
        <h3>${esc(p.name)}</h3>
        <span class="badge" style="background:${colorFor(p)}">${esc(cfg.labels[p.gating_status] || p.gating_status)}</span>
        <dl>${rows.join("")}</dl>
        <a class="edit-link" href="/submit?edit=${encodeURIComponent(p.id)}">Suggest an edit</a>
      </div>`;
  }

  function matches(f) {
    const p = f.properties;
    const q = searchEl.value.trim().toLowerCase();
    if (cityEl.value && p.city !== cityEl.value) return false;
    if (gatingEl.value && p.gating_status !== gatingEl.value) return false;
    if (q) {
      const haystack = `${p.name} ${p.alt_names || ""}`.toLowerCase();
      if (!haystack.includes(q)) return false;
    }
    return true;
  }

  function render(fitToResults) {
    if (layer) map.removeLayer(layer);
    const shown = allFeatures.filter(matches);

    layer = L.geoJSON({ type: "FeatureCollection", features: shown }, {
      style: (f) => ({ color: colorFor(f.properties), weight: 2, fillOpacity: 0.3 }),
      pointToLayer: (f, latlng) => L.circleMarker(latlng, {
        radius: 8, color: "#fff", weight: 2, fillColor: colorFor(f.properties), fillOpacity: 0.9,
      }),
      onEachFeature: (f, lyr) => lyr.bindPopup(popupHtml(f.properties)),
    }).addTo(map);

    countEl.textContent = `Showing ${shown.length} of ${allFeatures.length}`;

    if (fitToResults && shown.length) {
      map.fitBounds(layer.getBounds(), { maxZoom: 16, padding: [30, 30] });
    }
  }

  [cityEl, gatingEl].forEach((el) => el.addEventListener("change", () => render(true)));
  searchEl.addEventListener("input", () => render(false));

  fetch("/api/communities")
    .then((r) => r.json())
    .then((data) => { allFeatures = data.features; render(false); })
    .catch(() => { countEl.textContent = "Could not load communities."; });
})();
