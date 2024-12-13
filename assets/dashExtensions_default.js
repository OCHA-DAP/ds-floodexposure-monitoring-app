window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const {
                classes,
                colorscale,
                style,
                colorProp,
                selected
            } = context.hideout; // get props from hideout
            const value = feature.properties[colorProp]; // get value the determines the color
            if (value == -1) {
                style.fillColor = colorscale[0];
            } else if (value == 0) {
                style.fillColor = colorscale[1];
            } else if (value == 1) {
                style.fillColor = colorscale[2];
            }
            return style;

        }

    }
});
