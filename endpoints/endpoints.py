from data.load_data import load_data


def register_endpoints(app):
    @app.server.route("/reload-data", methods=["POST"])
    def reload_data():
        app.data = load_data()
        return "Data reloaded", 200
