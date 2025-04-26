from imutils.contours import sort_contours as imutils_sort_contours
from Config import *
from ManualContourSelector import *
from ImageProcessor import *
from ContourProcessor import *
from GeometryCalculator import *
from ImageAnnotator import *


class MeasurementSystem:
    """Main class that coordinates the measurement functionality."""

    def __init__(self, ref_obj_pos, ref_obj_width_real, ref_obj_height_real, manual_selection_points):
        self.ref_obj_pos = ref_obj_pos
        self.ref_obj_width_real = ref_obj_width_real
        self.ref_obj_height_real = ref_obj_height_real
        self.manual_selection_points = manual_selection_points

    def measure_2d_item(self, image, polygons):
        """
        Measure a 2D item from an image.

        Args:
            image: OpenCV image object

        Returns:
            dict: Measurement results and annotated image
        """
        # Resize the Image
        image = ImageProcessor.resize_image(image)

        # Find Contours
        contour_list = ContourProcessor.get_contours(image, polygons)
        (contour_list, _) = imutils_sort_contours(
            contour_list, method=ContourProcessor.get_sorting_order(self.ref_obj_pos))

        # Get the two largest contours
        ref_obj_contour, obj_contour = ContourProcessor.get_two_largest_contours(
            contour_list)

        # Calculate reference object dimensions in pixels
        ref_obj_width_px, ref_obj_height_px, ref_obj_bounding_box = GeometryCalculator.calc_dimensions_px(
            ref_obj_contour)

        # Calculate pixels per metric
        pixels_per_metric = GeometryCalculator.calc_pixels_per_metric(
            ref_obj_width_px, self.ref_obj_width_real)

        # Calculate reference object real height
        _, ref_obj_height_real = GeometryCalculator.calc_dimensions_real(
            ref_obj_width_px, ref_obj_height_px, pixels_per_metric)

        # Calculate object dimensions in pixels
        obj_width_px, obj_height_px, obj_bounding_box = GeometryCalculator.calc_dimensions_px(
            obj_contour)

        # Calculate object real dimensions
        obj_width_real, obj_height_real = GeometryCalculator.calc_dimensions_real(
            obj_width_px, obj_height_px, pixels_per_metric)

        # Create a copy for annotation
        annotated_image = image.copy()

        # Annotate the image
        ImageAnnotator.annotate_image(annotated_image, ref_obj_bounding_box,
                                      self.ref_obj_width_real, ref_obj_height_real)
        ImageAnnotator.annotate_image(annotated_image, obj_bounding_box,
                                      obj_width_real, obj_height_real)

        # Encode the annotated image to base64
        encoded_image = ImageProcessor.encode_image_to_base64(annotated_image)

        return {
            "width": obj_width_real,
            "height": obj_height_real,
            "annotated_image": encoded_image
        }

    def measure_3d_item(self, front_image, side_image):
        """
        Measure a 3D item from front and side images.

        Args:
            front_image: OpenCV image object of front view
            side_image: OpenCV image object of side view

        Returns:
            dict: Measurement results including width, height, depth, and annotated images.
        """

        polygons_front_image = self.manual_selection_points[0]
        polygons_side_image = self.manual_selection_points[1]

        # Process front image
        front_results = self.measure_2d_item(front_image, polygons_front_image)
        if "error" in front_results:
            return front_results

        # Process side image
        side_results = self.measure_2d_item(side_image, polygons_side_image)
        if "error" in side_results:
            return side_results

        # Store in a sorted list from largest to smallest
        dimensions = [front_results["width"],
                      front_results["height"], side_results["width"], side_results["height"]]
        dimensions.sort(reverse=True)

        # The smallest value is the depth
        width, height, depth = dimensions[0], dimensions[1], dimensions[3]

        # Check if the two largest values come from the same image
        if (dimensions[0] == front_results["width"] and dimensions[1] == front_results["height"]) or \
                (dimensions[0] == side_results["width"] and dimensions[1] == side_results["height"]):
            pass
        else:
            width, height = dimensions[0], dimensions[2]

        return {
            "width": width,
            "height": height,
            "depth": depth,
            "front_annotated_image": front_results["annotated_image"],
            "side_annotated_image": side_results["annotated_image"]
        }
