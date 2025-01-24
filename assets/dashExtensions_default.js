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

    }
});