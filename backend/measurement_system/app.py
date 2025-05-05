from MeasurementSystem import *


# API Setup
app = Flask(__name__)


@app.route('/measure2d', methods=['POST'])
def measure_2d():
    """
    API endpoint to measure a 2D object from one image.
    Expects a JSON request with base64 encoded image.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format."}), 400

        # Extract data
        image_b64 = data.get("image_b64")
        ref_obj_pos = data.get("ref_obj_pos")
        ref_obj_width_real = data.get("ref_obj_width_real")
        ref_obj_height_real = data.get("ref_obj_height_real")
        polygons_image = data.get("polygons_image", None)

        if not all([image_b64, ref_obj_pos, ref_obj_width_real, ref_obj_height_real]):
            return jsonify({"error": "Missing required parameters."}), 400

        # Ensure polygonst_image is None if it is an empty value
        if not polygons_image:
            polygons_image = None

        # Decode image
        image = ImageProcessor.decode_base64_image(image_b64)

        if image is None:
            return jsonify({"error": "Invalid image data."}), 400

        measurement_system = MeasurementSystem(
            ref_obj_pos, ref_obj_width_real, ref_obj_height_real, (polygons_image, None))

        # Perform measurement
        results = measurement_system.measure_2d_item(image, polygons_image)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/measure', methods=['POST'])
def measure_3d():
    """
    API endpoint to measure a 3D object from two images.
    Expects a JSON request with base64 encoded images.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format."}), 400

        # Extract data
        front_image_b64 = data.get("front_image_b64")
        side_image_b64 = data.get("side_image_b64")
        ref_obj_pos = data.get("ref_obj_pos")
        ref_obj_width_real = data.get("ref_obj_width_real")
        ref_obj_height_real = data.get("ref_obj_height_real")
        polygons_front_image = data.get("polygons_front_image", None)
        polygons_side_image = data.get("polygons_side_image", None)

        if not all([front_image_b64, side_image_b64, ref_obj_pos, ref_obj_width_real, ref_obj_height_real]):
            return jsonify({"error": "Missing required parameters."}), 400

        # Ensure polygons_front_image is None if it is an empty value
        if not polygons_front_image:
            polygons_front_image = None
        if not polygons_side_image:
            polygons_side_image = None

        # Decode images
        front_image = ImageProcessor.decode_base64_image(front_image_b64)
        side_image = ImageProcessor.decode_base64_image(side_image_b64)

        if front_image is None or side_image is None:
            return jsonify({"error": "Invalid image data."}), 400

        measurement_system = MeasurementSystem(
            ref_obj_pos, ref_obj_width_real, ref_obj_height_real, (polygons_front_image, polygons_side_image))

        # Perform measurement
        results = measurement_system.measure_3d_item(front_image, side_image)

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
