import cv2 as cv
from imutils.contours import sort_contours as imutils_sort_contours
from Config import *
from ManualContourSelector import *
from ImageProcessor import *
from ContourProcessor import *
from GeometryCalculator import *
from ImageAnnotator import *


class MeasurementSystem:
    """Main class that coordinates the measurement functionality."""

    def __init__(self):
        Config.initialize()

    def measure_2d_item(self, image_path, ref_obj_pos, ref_obj_width_real):
        # Load and Preprocess the Image
        image = cv.imread(image_path)
        image = ImageProcessor.resize_image(image)

        # Find Contours
        contour_list = ContourProcessor.get_contours(image)
        (contour_list, _) = imutils_sort_contours(
            contour_list, method=ContourProcessor.get_sorting_order(ref_obj_pos))

        ref_obj_contour, obj_contour = ContourProcessor.get_two_largest_contours(
            contour_list)

        ref_obj_width_px, ref_obj_height_px, ref_obj_bounding_box = GeometryCalculator.calc_dimensions_px(
            ref_obj_contour)

        pixels_per_metric = GeometryCalculator.calc_pixels_per_metric(
            ref_obj_width_px, ref_obj_width_real)

        _, ref_obj_height_real = GeometryCalculator.calc_dimensions_real(
            ref_obj_width_px, ref_obj_height_px, pixels_per_metric)

        obj_width_px, obj_height_px, obj_bounding_box = GeometryCalculator.calc_dimensions_px(
            obj_contour)
        obj_width_real, obj_height_real = GeometryCalculator.calc_dimensions_real(
            obj_width_px, obj_height_px, pixels_per_metric)

        ImageAnnotator.annotate_image(image, ref_obj_bounding_box,
                                      ref_obj_width_real, ref_obj_height_real)
        ImageAnnotator.annotate_image(image, obj_bounding_box,
                                      obj_width_real, obj_height_real)

        if Config.DISPLAY_OUTPUT_WINDOW:
            cv.imshow(Config.OUTPUT_WINDOW_NAME, image)
            cv.waitKey(0)
            cv.destroyAllWindows()

    def measure_3d_item(self, front_image_path, side_image_path, ref_obj, ref_obj_pos):
        ref_obj_width_real = Config.REFERENCE_OBJECTS[ref_obj][Config.MEASURE_UNIT]

        front_measurements = self.measure_2d_item(
            front_image_path, ref_obj_pos, ref_obj_width_real)
        side_measurements = self.measure_2d_item(
            side_image_path, ref_obj_pos, ref_obj_width_real)

        front_width, front_height = front_measurements["width"], front_measurements["height"]
        side_width, side_height = side_measurements["width"], side_measurements["height"]

        # Store in a sorted list from largest to smallest
        dimensions = [front_width, front_height, side_width, side_height]
        dimensions.sort(reverse=True)

        # The smallest value is the depth
        width, height, depth = dimensions[0], dimensions[1], dimensions[3]

        # Check if the two largest values come from the same image
        if (dimensions[0] == front_width and dimensions[1] == front_height) or \
                (dimensions[0] == side_width and dimensions[1] == side_height):
            pass
        else:
            width, height = dimensions[0], dimensions[2]

        item_name = front_image_path.split(
            "/")[-1].split(".")[0].rsplit("-", 1)[0]

        return {"item": item_name, "width": width, "height": height, "depth": depth}
