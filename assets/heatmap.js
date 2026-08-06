// Shared helpers for the locations points layer (see
// points_layer_handler in callbacks/callbacks.py). Dash auto-loads
// every file in assets/, so these are available as plain globals to
// the clientside functions dash_extensions generates - keeping the
// fetch-caching and bounds/type-filtering logic here (rather than
// inline in the assign()'d string) is what lets the fetch of
// /data/locations.json happen once and get reused on every
// pan/zoom/filter change instead of re-fetching each time.

// window.LOCATIONS_POINT_COLOR is set from points_layer_handler in
// callbacks/callbacks.py (Python-templated from OCHA_BLUE) before this
// is ever read - not hardcoded here, so there's one source of truth.

// All points render at the same size now that type is already
// distinguished by color (see SITE_TYPE_COLOR) - this matches what
// was previously the smallest (Village) size.
const POINT_RADIUS = 3;

const VILLAGE_SITE_TYPE = "POP_5 - Village";

// Marker color by settlement type - distinct per type, so type is
// legible on its own. Hex values match this app's existing brand
// color constants (constants.py: CHD_LIGHTBLUE, CHD_MINT, CHD_GREEN,
// CHD_GREY, OCHA_BLUE, CHD_RED) - kept in sync manually since this
// file isn't Python-templated. Administrative Centre uses grey
// (CHD_GREY) rather than a third blue - CHD_BLUE and OCHA_BLUE were
// too close to each other to tell apart at point size. Falls back to
// window.LOCATIONS_POINT_COLOR (OCHA_BLUE, threaded in from
// points_layer_handler) for any unlisted site_type.
const SITE_TYPE_COLOR = {
    "POP_5 - Village": "#66b0ec",
    "POP_3 - Secondary Town": "#1ebfb3",
    "POP_2 - Primary Town": "#1bb580",
    "POP_4 - Administrative Centre": "#888888",
    "POP_1 - Admin1 Capital": "#0072BC",
    "POP_0 - National Capital": "#f2645a",
};

window.getLocationsData = function () {
    window._locationsDataPromise =
        window._locationsDataPromise ||
        fetch("/data/locations.json")
            .then((r) => r.json())
            .then((geojson) => geojson.features);
    return window._locationsDataPromise;
};

// Shows a tooltip for whichever point is nearest the cursor, without
// making the points themselves interactive - if the markers received
// their own mouseover (via Leaflet's usual .bindTooltip()), hovering
// one would make it the topmost hit-tested element and steal
// mouseover/mouseout from the choropleth polygon underneath (the
// exact bug interactive: false in rebuildPointsLayer below already
// fixed once). Tracking the cursor at the map level instead, and
// manually showing/hiding one shared tooltip based on proximity,
// never touches which DOM element the browser considers "hovered" -
// the polygon's own native hover keeps working undisturbed regardless
// of how close the cursor gets to a point sitting on top of it.
const POINT_HOVER_RADIUS_PX = 8;

window.attachPointsHoverTooltip = function (map) {
    if (window._pointsHoverAttached) return;
    window._pointsHoverAttached = true;

    // A dedicated pane, above "locations" (where the points themselves
    // live) - without this, the tooltip and the point markers share
    // one pane and DOM/stacking order between an SVG marker layer and
    // an HTML tooltip div isn't reliably "whichever was added last
    // wins," so a tooltip could render underneath a nearby point.
    if (!map.getPane("locations-tooltip")) {
        map.createPane("locations-tooltip");
        map.getPane("locations-tooltip").style.zIndex = 1003;
    }
    const tooltip = L.tooltip({
        pane: "locations-tooltip",
        className: "point-hover-tooltip",
    });

    map.on("mousemove", (e) => {
        const layer = window._pointsLayer;
        if (!layer) return;

        const cursorPoint = map.latLngToContainerPoint(e.latlng);
        let nearest = null;
        let nearestDist = POINT_HOVER_RADIUS_PX;

        layer.eachLayer((marker) => {
            const markerPoint = map.latLngToContainerPoint(
                marker.getLatLng()
            );
            const dist = cursorPoint.distanceTo(markerPoint);
            if (dist < nearestDist) {
                nearestDist = dist;
                nearest = marker;
            }
        });

        if (nearest) {
            const nameLine = `<div><strong>Place Name:</strong> ${nearest.siteName || ""}</div>`;
            const typeLine = `<div><strong>Site type:</strong> ${nearest.siteType || ""}</div>`;
            tooltip
                .setLatLng(nearest.getLatLng())
                .setContent(nameLine + typeLine)
                .addTo(map);
        } else if (map.hasLayer(tooltip)) {
            map.removeLayer(tooltip);
        }
    });
};

// Rebuilds window._pointsLayer's contents from scratch, keeping only
// the points currently within the map's own live bounds AND whose
// site_type is in `allowedTypes`. Never constructs markers for the
// full ~12k-point dataset at once - only for whatever's actually in
// view and checked.
//
// Bounds are read directly from the map (map.getBounds()) rather than
// taking a `bounds` argument sourced from dash-leaflet's "bounds"
// prop - that prop only gets populated after the first moveend fires,
// so on a fresh page load (before any pan/zoom has ever happened) it's
// undefined, and points would never show until the map was manually
// moved once. The live map object always has real bounds immediately.
window.rebuildPointsLayer = function (allowedTypes) {
    const layer = window._pointsLayer;
    if (!layer) return;
    const map = layer._map;
    if (!map) return;

    // Detach from the map while rebuilding, then reattach once at the
    // end. Leaflet only touches the DOM for layers actually attached
    // to the map - each marker.addTo(layer) below would otherwise
    // trigger its own synchronous position calc + SVG <path> insertion
    // immediately, since layer is already live. Clearing and
    // repopulating while detached turns what would be hundreds of
    // individual DOM operations into a single one on reattach - this
    // is the main cost for however many hundred points end up
    // matching, not the plain array scan over all ~12k below it.
    map.removeLayer(layer);
    layer.clearLayers();

    const latLngBounds = map.getBounds();
    const allowed = new Set(allowedTypes || []);
    window.getLocationsData().then((features) => {
        // If the points layer got torn down/rebuilt while this
        // (possibly already-cached, but still async) fetch was
        // pending, don't populate a stale layer.
        if (window._pointsLayer !== layer) return;
        features.forEach((f) => {
            if (!allowed.has(f.properties.site_type)) return;
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
            const color =
                SITE_TYPE_COLOR[f.properties.site_type] ??
                window.LOCATIONS_POINT_COLOR;
            // Villages keep a stroke matching their own fill (the
            // original look); every other type gets a very thin black
            // outline instead, to stand out a bit more against the
            // basemap/choropleth now that color is what distinguishes
            // type rather than size.
            const isVillage = f.properties.site_type === VILLAGE_SITE_TYPE;
            const marker = L.circleMarker([lat, lng], {
                pane: "locations",
                radius: POINT_RADIUS,
                weight: isVillage ? 1 : 0.5,
                color: isVillage ? color : "black",
                fillColor: color,
                fillOpacity: 0.8,
                // No native hover/click behavior on the marker DOM
                // element itself. Without this, a point sitting on top
                // of the choropleth still receives mouseover/mouseout
                // as the cursor crosses it - even though they're not
                // parent/child in the DOM, the polygon underneath
                // loses its own mouseover state when the marker
                // becomes the topmost hit target, which drops the
                // choropleth's hoverStyle back to its unselected look.
                // interactive: false removes the marker from
                // hit-testing entirely (same pointer-events mechanism
                // already relied on for click-passthrough), so the
                // polygon's hover/selected state is never disturbed by
                // a point above it. The hover tooltip is instead shown
                // via attachPointsHoverTooltip's cursor-proximity
                // check above, which reads .siteName directly rather
                // than needing the marker to be interactive.
                interactive: false,
            });
            marker.siteName = f.properties.name;
            // Drop the "POP_N - " code prefix (e.g. "POP_5 - Village"
            // -> "Village") - the raw code isn't meaningful to look at
            // in a hover tooltip.
            marker.siteType = (f.properties.site_type || "").replace(
                /^POP_\d+\s*-\s*/,
                ""
            );
            marker.addTo(layer);
        });
        map.addLayer(layer);
    });
};
