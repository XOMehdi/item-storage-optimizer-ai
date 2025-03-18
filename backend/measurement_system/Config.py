import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import grab_contours as imutils_grab_contours
from imutils.contours import sort_contours as imutils_sort_contours
from scipy.spatial.distance import euclidean
import os
import base64
import io
from PIL import Image
from flask import Flask, request, jsonify


class Config:
    """Configuration class for measurement system."""

    MEASURE_UNIT = "cm"
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
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
