(function () {
  const cfg = window.SUB;
  const geometryInput = document.getElementById("geometry");
  const statusEl = document.getElementById("shape-status");
  const form = document.getElementById("submit-form"); // null on read-only pages

  const map = L.map("draw-map").setView([cfg.lat, cfg.lng], cfg.zoom);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  // Existing communities in grey, for context (so people can spot duplicates).
  fetch("/api/communities")
    .then((r) => r.json())
    .then((data) => {
      const others = data.features.filter((f) => f.properties.id !== cfg.excludeId);
      L.geoJSON({ type: "FeatureCollection", features: others }, {
        style: { color: "#888", weight: 1, fillOpacity: 0.15, interactive: false },
        pointToLayer: (f, latlng) => L.circleMarker(latlng, { radius: 5, color: "#888", interactive: false }),
        interactive: false,
      }).addTo(map);
    })
    .catch(() => {});

  // Admin review of an edit: show the current shape as a dashed blue outline.
  if (cfg.existing) {
    L.geoJSON(cfg.existing, {
      style: { color: "#1f78b4", weight: 2, dashArray: "6 4", fillOpacity: 0 },
      pointToLayer: (f, latlng) => L.circleMarker(latlng, { radius: 8, color: "#1f78b4", fillOpacity: 0 }),
      interactive: false,
    }).addTo(map);
  }

  const drawn = new L.FeatureGroup().addTo(map);

  function updateStatus() {
    const layers = drawn.getLayers();
    if (!layers.length) {
      geometryInput.value = "";
      statusEl.textContent = "No shape drawn yet.";
      return;
    }
    const geom = layers[0].toGeoJSON().geometry;
    geometryInput.value = JSON.stringify(geom);
    statusEl.textContent = geom.type === "Polygon"
      ? "Boundary drawn. You can edit or delete it with the toolbar."
      : "Pin placed. You can move or delete it with the toolbar.";
  }

  // Load an existing shape (editing, review, or the form re-shown after an error).
  if (geometryInput.value) {
    try {
      L.geoJSON(JSON.parse(geometryInput.value), {
        style: { color: "#c0392b", weight: 3, fillOpacity: 0.25 },
      }).eachLayer((l) => drawn.addLayer(l));
      if (drawn.getLayers().length) {
        const layer = drawn.getLayers()[0];
        if (layer.getBounds) map.fitBounds(layer.getBounds(), { maxZoom: 17, padding: [30, 30] });
        else map.setView(layer.getLatLng(), 17);
      }
      updateStatus();
    } catch (e) {
      geometryInput.value = "";
    }
  }

  if (!cfg.readOnly) {
    map.addControl(new L.Control.Draw({
      edit: { featureGroup: drawn },
      draw: {
        polygon: { allowIntersection: false, showArea: false },
        marker: true,
        polyline: false, rectangle: false, circle: false, circlemarker: false,
      },
    }));

    // Only one shape per submission.
    map.on(L.Draw.Event.CREATED, (e) => {
      drawn.clearLayers();
      drawn.addLayer(e.layer);
      updateStatus();
    });
    map.on(L.Draw.Event.EDITED, updateStatus);
    map.on(L.Draw.Event.DELETED, updateStatus);
  }

  if (form) {
    form.addEventListener("submit", (e) => {
      const skip = e.submitter && e.submitter.hasAttribute("data-skip-geometry");
      if (!skip && !geometryInput.value) {
        e.preventDefault();
        alert("Please draw a boundary or drop a pin on the map first.");
      }
    });
  }
})();
