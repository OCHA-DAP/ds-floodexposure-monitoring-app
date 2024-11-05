window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, context) {
            const selected = context.hideout.selected

            if (selected.includes(feature.properties.ADM2_PCODE)) {
                return {
                    fillColor: '#1f77b4',
                    weight: 0.8,
                    opacity: 1,
                    color: 'white',
                    fillOpacity: 0.5
                }
            }
            return {
                fillColor: '#1f77b4',
                weight: 0.8,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.3
            }
        }

    }
});