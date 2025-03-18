import cv2 as cv
from imutils import grab_contours as imutils_grab_contours
from Config import *
from ManualContourSelector import *
from ImageProcessor import *


class ContourProcessor:
    """Handles contour operations and calculations."""

    @staticmethod
    def get_sorting_order(ref_obj_pos):
        if ref_obj_pos == "left":
            return "left-to-right"
        elif ref_obj_pos == "right":
            return "right-to-left"
        elif ref_obj_pos == "top":
            return "top-to-bottom"
        elif ref_obj_pos == "bottom":
            return "bottom-to-top"

        return "left-to-right"

    @staticmethod
    def get_two_largest_contours(contour_list):
        if len(contour_list) < 2:
            return contour_list[0], contour_list[0]

        # Find the two largest contours by area, but keep their original indices
        contour_areas = [(cv.contourArea(contour), index, contour)
                         for index, contour in enumerate(contour_list)]

        # Sort by area in descending order
        sorted_contours = sorted(
            contour_areas, key=lambda x: x[0], reverse=True)

        largest_contour = sorted_contours[0][2]
        second_largest_contour = sorted_contours[1][2]

        # Maintain original order in the list
        if sorted_contours[0][1] < sorted_contours[1][1]:  # Compare original indices
            ref_obj_contour = largest_contour
            obj_contour = second_largest_contour
        else:
            ref_obj_contour = second_largest_contour
            obj_contour = largest_contour

        return ref_obj_contour, obj_contour

    @staticmethod
    def get_contours(image, polygons=None):
        if polygons:
            selector = ManualContourSelector()
            return selector.set_polygons_from_flutter(polygons)
        else:
            gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
            blurred_image = cv.GaussianBlur(gray_image, Config.BLUR_SIZE, 0)

            # Edge Detection
            edges_detected = ImageProcessor.detect_edges(
                blurred_image, upper_threshold=120)

            # Find Contours
            contour_list = cv.findContours(
                edges_detected, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            contour_list = imutils_grab_contours(contour_list)
            return contour_list
