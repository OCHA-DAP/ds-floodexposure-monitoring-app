window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
                const {
                    colorscale,
                    style,
                    colorProp,
                    selected
                } = context.hideout; // get props from hideout
                const value = feature.properties[colorProp]; // get value that determines the color
                let featureStyle = {
                    ...style
                };

                // Only modify opacity if this feature's pcode matches selected
                if (selected === feature.properties.pcode) {
                    featureStyle.fillOpacity = 1;
                    featureStyle.color = "black";
                    featureStyle.weight = 1;
                }

                // Set color based on value
                if (value === -2) {
                    featureStyle.fillColor = colorscale[0];
                } else if (value === -1) {
                    featureStyle.fillColor = colorscale[1];
                } else if (value === 0) {
                    featureStyle.fillColor = colorscale[2];
                } else if (value === 1) {
                    featureStyle.fillColor = colorscale[3];
                } else if (value === 2) {
                    featureStyle.fillColor = colorscale[4];
                }

                return featureStyle;
            }

            ,
        function1: function(e, ctx) {
                const layerGroup = e.target;
                const map = layerGroup._map;
                const overlayPane = map.getPane("overlayPane");
                if (overlayPane) overlayPane.style.zIndex = 1001;

                function buildHeatLayer() {
                    window.getLocationsData()
                        .then((features) => {
                            const points = features.map(
                                (f) => [f.geometry.coordinates[1], f.geometry.coordinates[0]]
                            );
                            const heat = L.heatLayer(points, {
                                radius: 10,
                                blur: 3,
                                maxZoom: 12,
                                minOpacity: 0.1,
                                gradient: {
                                    0.3: "#66b0ec",
                                    0.6: "#007ce0",
                                    1.0: "#0072BC"
                                },
                            });
                            layerGroup.addLayer(heat);
                            window._heatLayer = heat;
                        })
                        .catch((err) => console.error("Heatmap layer failed:", err));
                }

                if (typeof L.heatLayer === "function") {
                    buildHeatLayer();
                } else {
                    const script = document.createElement("script");
                    script.src = "https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js";
                    script.onload = buildHeatLayer;
                    script.onerror = () => console.error("Failed to load leaflet.heat plugin");
                    document.head.appendChild(script);
                }
            }

            ,
        function2: function(e, ctx) {
            const layerGroup = e.target;
            const points = L.layerGroup();
            layerGroup.addLayer(points);
            window._pointsLayer = points;
            window.LOCATIONS_POINT_COLOR = "#0072BC";
        }

    }
});
