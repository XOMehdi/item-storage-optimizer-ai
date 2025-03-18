import cv2 as cv
import numpy as np


class Config:
    """Configuration class for measurement system."""

    IMAGES_DIRECTORY = "test-images"
    MEASURE_UNIT = "cm"
    MANUAL_SELECTION = False
    DISPLAY_OUTPUT_WINDOW = True  # Will be updated based on MANUAL_SELECTION
    BLUR_SIZE = (7, 7)
    CANNY_KERNEL = np.ones((3, 3), np.uint8)
    CANNY_DILATE_ITERATIONS = 5
    CANNY_ERODE_ITERATIONS = 3
    TEXT_FONT = cv.FONT_HERSHEY_SIMPLEX
    TEXT_SCALE = 1.2
    TEXT_COLOR = (255, 255, 255)
    TEXT_THICKNESS = 2
    BOX_COLOR = (0, 0, 0)
    BOX_PADDING = 10  # Padding around text
    LINE_COLOR = (255, 0, 255)
    LINE_THICKNESS = 2
    OUTPUT_WINDOW_NAME = 'Image With Estimated Measurements'

    @classmethod
    def initialize(cls):
        cls.DISPLAY_OUTPUT_WINDOW = True if cls.MANUAL_SELECTION else True
