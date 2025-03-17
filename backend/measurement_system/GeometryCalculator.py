import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from scipy.spatial.distance import euclidean


class GeometryCalculator:
    """Handles geometric calculations for measurements."""

    @staticmethod
    def calc_midpoint(first_point, second_point):
        midpoint_x = (first_point[0] + second_point[0]) * 0.5
        midpoint_y = (first_point[1] + second_point[1]) * 0.5
        return (midpoint_x, midpoint_y)

    @staticmethod
    def calc_dimensions_px(contour):
        # Calculate Rotated Bounding Box
        bounding_box = cv.minAreaRect(contour)
        bounding_box = cv.boxPoints(bounding_box)
        bounding_box = np.array(bounding_box, dtype="int")
        bounding_box = imutils_perspective.order_points(bounding_box)
        tl, tr, br, bl = bounding_box

        width_px = euclidean(GeometryCalculator.calc_midpoint(
            tl, bl), GeometryCalculator.calc_midpoint(tr, br))
        height_px = euclidean(GeometryCalculator.calc_midpoint(
            tl, tr), GeometryCalculator.calc_midpoint(bl, br))

        return width_px, height_px, bounding_box

    @staticmethod
    def calc_pixels_per_metric(width_px, ref_obj_width_real):
        return width_px / ref_obj_width_real

    @staticmethod
    def calc_dimensions_real(width_px, height_px, pixels_per_metric):
        real_width = round(width_px / pixels_per_metric, 2)
        real_height = round(height_px / pixels_per_metric, 2)

        return real_width, real_height
