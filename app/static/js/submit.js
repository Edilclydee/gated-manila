(function () {
  const cfg = window.SUB;
  const geometryInput = document.getElementById("geometry");
  const statusEl = document.getElementById("shape-status");
  const form = document.getElementById("submit-form");

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

  // Load an existing shape (editing, or the form was re-shown after an error).
  if (geometryInput.value) {
    try {
      L.geoJSON(JSON.parse(geometryInput.value)).eachLayer((l) => drawn.addLayer(l));
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

  form.addEventListener("submit", (e) => {
    if (!geometryInput.value) {
      e.preventDefault();
      alert("Please draw a boundary or drop a pin on the map first.");
    }
  });
})();
