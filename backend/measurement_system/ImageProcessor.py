import cv2 as cv
from Config import *


class ImageProcessor:
    """Handles image processing operations like resizing and edge detection."""

    @staticmethod
    def resize_image(image, max_width=1920, max_height=1080):
        h, w = image.shape[:2]
        aspect_ratio = w / h

        while w > max_width or h > max_height:
            if w > max_width:
                w = max_width
                h = int(w / aspect_ratio)

            if h > max_height:
                h = max_height
                w = int(h * aspect_ratio)

        return cv.resize(image, (w, h), interpolation=cv.INTER_LANCZOS4)

    @staticmethod
    def detect_edges(image, upper_threshold=None):
        edges = cv.Canny(image, 10, upper_threshold)
        edges = cv.dilate(edges, Config.CANNY_KERNEL,
                          iterations=Config.CANNY_DILATE_ITERATIONS)
        edges = cv.erode(edges, Config.CANNY_KERNEL,
                         iterations=Config.CANNY_ERODE_ITERATIONS)

        return edges
