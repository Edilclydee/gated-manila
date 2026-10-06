// Province -> city dropdowns, searchable (Tom Select) with a plain-<select> fallback.
(function () {
  const data = window.LOCATIONS || {};

  function initLocationSelects(provinceEl, cityEl, options) {
    options = options || {};
    const useTS = typeof window.TomSelect === "function";
    const settings = { allowEmptyOption: true, maxOptions: 600, create: false, selectOnTab: true };
    const provinceTS = useTS ? new TomSelect(provinceEl, settings) : null;
    const cityTS = useTS ? new TomSelect(cityEl, settings) : null;

    const emptyLabel = cityEl.dataset.emptyLabel || "Choose\u2026";
    const initialCity = cityEl.dataset.selected || cityEl.value || "";

    // Fill the city list for a province; keep `selected` if it belongs to that province.
    function setCities(province, selected) {
      const cities = data[province] || [];
      const keep = cities.includes(selected) ? selected : "";
      if (cityTS) {
        cityTS.clear(true);
        cityTS.clearOptions();
        cityTS.addOption({ value: "", text: emptyLabel });
        cities.forEach((c) => cityTS.addOption({ value: c, text: c }));
        cityTS.refreshOptions(false);
        cityTS.setValue(keep, true);
        if (province) cityTS.enable(); else cityTS.disable();
      } else {
        cityEl.innerHTML = "";
        cityEl.add(new Option(emptyLabel, ""));
        cities.forEach((c) => cityEl.add(new Option(c, c)));
        cityEl.value = keep;
        cityEl.disabled = !province;
      }
    }

    provinceEl.addEventListener("change", () => {
      setCities(provinceEl.value, "");
      if (options.onProvinceChange) options.onProvinceChange();
    });
    setCities(provinceEl.value, initialCity);
    return { provinceTS, cityTS };
  }

  window.initLocationSelects = initLocationSelects;
})();
