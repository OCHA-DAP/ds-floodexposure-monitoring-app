// Shared helpers for the locations heatmap/points layers (see
// heat_layer_handler and points_layer_handler in callbacks/callbacks.py).
// Dash auto-loads every file in assets/, so these are available as
// plain globals to the clientside functions dash_extensions generates -
// keeping the fetch-caching and bounds-filtering logic here (rather
// than duplicated inline in each assign()'d string) is what lets the
// heat layer and the points layer share one fetch of
// /data/locations.json without either re-fetching on every zoom/pan.

// window.LOCATIONS_POINT_COLOR is set from points_layer_handler in
// callbacks/callbacks.py (Python-templated from OCHA_BLUE) before this
// is ever read - not hardcoded here, so there's one source of truth.

window.getLocationsData = function () {
    window._locationsDataPromise =
        window._locationsDataPromise ||
        fetch("/data/locations.json")
            .then((r) => r.json())
            .then((geojson) => geojson.features);
    return window._locationsDataPromise;
};

// Rebuilds window._pointsLayer's contents from scratch, keeping only
// the points that fall inside `bounds` ([[south, west], [north, east]],
// the shape dash-leaflet's Map "bounds" prop is serialized as). Never
// constructs markers for the full ~12k-point dataset at once - only
// for whatever's actually in view.
window.rebuildPointsLayer = function (bounds) {
    const layer = window._pointsLayer;
    if (!layer) return;
    layer.clearLayers();

    const latLngBounds = L.latLngBounds(bounds);
    window.getLocationsData().then((features) => {
        // If the points layer got torn down/rebuilt while this
        // (possibly already-cached, but still async) fetch was
        // pending, don't populate a stale layer.
        if (window._pointsLayer !== layer) return;
        features.forEach((f) => {
            const lng = f.geometry.coordinates[0];
            const lat = f.geometry.coordinates[1];
            if (!latLngBounds.contains([lat, lng])) return;
            // No `renderer` override here - deliberately left as
            // Leaflet's default SVG (not L.canvas()). A shared canvas
            // renderer would draw one <canvas> covering the whole
            // viewport, and canvas elements capture clicks across
            // their full bounding box at the DOM level regardless of
            // what's actually drawn - blocking clicks on the
            // choropleth beneath wherever there's no marker. SVG
            // paths get real per-shape hit-testing via Leaflet's own
            // CSS (pointer-events: none on the container, auto only
            // on .leaflet-interactive paths), so empty areas correctly
            // pass clicks through. Fine performance-wise since this
            // only ever holds the current viewport's points, not all
            // ~12k.
            L.circleMarker([lat, lng], {
                pane: "locations",
                radius: 5,
                weight: 1,
                color: window.LOCATIONS_POINT_COLOR,
                fillColor: window.LOCATIONS_POINT_COLOR,
                fillOpacity: 0.8,
                // No hover/click behavior on points at all. Without
                // this, a point sitting on top of the choropleth still
                // receives mouseover/mouseout as the cursor crosses
                // it - even though they're not parent/child in the
                // DOM, the polygon underneath loses its own mouseover
                // state when the marker becomes the topmost hit
                // target, which drops the choropleth's hoverStyle back
                // to its unselected look. interactive: false removes
                // the marker from hit-testing entirely (same
                // pointer-events mechanism already relied on for
                // click-passthrough), so the polygon's hover/selected
                // state is never disturbed by a point above it.
                interactive: false,
            }).addTo(layer);
        });
    });
};
