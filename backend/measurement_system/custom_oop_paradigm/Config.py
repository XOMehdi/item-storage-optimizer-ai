import cv2 as cv
import numpy as np


class Config:
    IMAGES_DIRECTORY = "item-images"
    MEASURE_UNIT = "cm"
    MANUAL_SELECTION = False
    DISPLAY_OUTPUT_WINDOW = True if MANUAL_SELECTION else False
    BLUR_SIZE = (7, 7)
    CANNY_KERNEL = np.ones((3, 3), np.uint8)
    CANNY_DILATE_ITERATIONS = 5
    CANNY_ERODE_ITERATIONS = 3
    TEXT_FONT = cv.FONT_HERSHEY_SIMPLEX
    TEXT_SCALE = 1.2
    TEXT_COLOR = (255, 255, 255)
    TEXT_THICKNESS = 2
    BOX_COLOR = (0, 0, 0)
    BOX_PADDING = 10
    LINE_COLOR = (255, 0, 255)
    LINE_THICKNESS = 2
    OUTPUT_WINDOW_NAME = 'Estimated Measurements'


# class Config:
#     @staticmethod
#     def __init__(self, images_dir, measure_unit, draw_selection, display_output):
#         IMAGES_DIRECTORY = images_dir
#         MEASURE_UNIT = measure_unit
#         MANUAL_SELECTION = draw_selection
#         DISPLAY_OUTPUT_WINDOW = True if MANUAL_SELECTION else display_output
#         BLUR_SIZE = (7, 7)
#         CANNY_KERNEL = np.ones((3, 3), np.uint8)
#         CANNY_DILATE_ITERATIONS = 5
#         CANNY_ERODE_ITERATIONS = 3
#         TEXT_FONT = cv.FONT_HERSHEY_SIMPLEX
#         TEXT_SCALE = 1.2
#         TEXT_COLOR = (255, 255, 255)
#         TEXT_THICKNESS = 2
#         BOX_COLOR = (0, 0, 0)
#         BOX_PADDING = 10
#         LINE_COLOR = (255, 0, 255)
#         LINE_THICKNESS = 2
#         OUTPUT_WINDOW_NAME = 'Estimated Measurements'

