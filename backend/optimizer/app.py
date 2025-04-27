from Optimizer import *
from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/optimize', methods=['POST'])
def optimize():
    try:
        data = request.get_json()

        # Validate request
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        if "container" not in data or "items" not in data:
            return jsonify({"status": "error", "message": "Missing container or items data"}), 400

        container = data["container"]
        if "width" not in container or "height" not in container or "depth" not in container:
            return jsonify({"status": "error", "message": "Container dimensions not specified"}), 400

        # Ensure that the container dimensions are integers
        container['width'] = int(container['width'])
        container['height'] = int(container['height'])
        container['depth'] = int(container['depth'])

        items = data["items"]
        if not items or not isinstance(items, list):
            return jsonify({"status": "error", "message": "No items provided or invalid items format"}), 400

        for item in items:
            if "dimensions" not in item:
                return jsonify({"status": "error", "message": "Item missing dimensions"}), 400
            dim = item["dimensions"]
            if "width" not in dim or "height" not in dim or "depth" not in dim:
                return jsonify({"status": "error", "message": "Item dimensions incomplete"}), 400

            # Ensure item dimensions are integers
            dim['width'] = int(dim['width'])
            dim['height'] = int(dim['height'])
            dim['depth'] = int(dim['depth'])

        # Optional configuration
        config = data.get("config", None)

        # Set default values if config is None or contains invalid/empty values
        if not config or not isinstance(config, dict):
            config = {
                "population_size": 30,
                "generations": 50
            }
        else:
            config["population_size"] = int(
                config.get("population_size", 30) or 30)
            config["generations"] = int(config.get("generations", 50) or 50)

        optimizer = Optimizer(container, items)

        # Perform optimization
        result = optimizer.genetic_algorithm(
            config["population_size"], config["generations"])

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
