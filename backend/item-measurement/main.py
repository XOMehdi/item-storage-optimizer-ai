import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import contours as imutils_contours
from imutils import resize as imutils_resize
from imutils import grab_contours as imutils_grab_contours
from scipy.spatial import distance
import os

# Constants
MEASURE_UNIT = "cm"
REFERENCE_OBJECTS = {
    "card": {"cm": 8.56, "in": 3.37},
    "coin": {"cm": 2.42, "in": 0.95},
}
BLUR_SIZE = (7, 7)
CANNY_WINDOW_NAME = 'Canny Edge Detection'
CANNY_KERNEL = np.ones((3, 3), np.uint8)
CANNY_DILATE_ITERATIONS = 5
CANNY_ERODE_ITERATIONS = 3
MIN_CONTOUR_AREA = 10000
DESIRED_IMAGE_WIDTH = 1600
TEXT_FONT = cv.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 0.65
TEXT_COLOR = (0, 0, 0)
TEXT_THICKNESS = 2
BOX_COLOR = (0, 255, 0)
POINT_COLOR = (0, 0, 255)
LINE_COLOR = (255, 0, 255)
POINT_RADIUS = 5
LINE_THICKNESS = 2
OUTPUT_WINDOW_NAME = 'Image With Measurements'


# Functions
def calculate_midpoint(point_a, point_b):
    """Calculate the midpoint between two points."""
    return ((point_a[0] + point_b[0]) * 0.5, (point_a[1] + point_b[1]) * 0.5)


def adjust_canny_thresholds(input_image):
    """Adjust Canny edge detection thresholds dynamically using trackbars."""
    cv.namedWindow(CANNY_WINDOW_NAME)
    cv.createTrackbar('Upper Threshold', CANNY_WINDOW_NAME,
                      20, 255, lambda value: value)
    while True:
        upper_threshold = cv.getTrackbarPos(
            'Upper Threshold', CANNY_WINDOW_NAME)
        edges_detected = cv.Canny(
            input_image, 10, upper_threshold)
        edges_detected = cv.dilate(
            edges_detected, CANNY_KERNEL, iterations=CANNY_DILATE_ITERATIONS)
        edges_detected = cv.erode(
            edges_detected, CANNY_KERNEL, iterations=CANNY_ERODE_ITERATIONS)

        cv.imshow(CANNY_WINDOW_NAME, edges_detected)
        if cv.waitKey(1) & 0xFF == ord('q'):
            cv.destroyWindow(CANNY_WINDOW_NAME)
            break

    return edges_detected


def estimate_measurement(image_path, reference_object_width):
    # Load and Preprocess the Image
    input_image = cv.imread(image_path)
    input_image = imutils_resize(
        input_image, width=DESIRED_IMAGE_WIDTH) if input_image.shape[1] > DESIRED_IMAGE_WIDTH else input_image

    # Convert to Grayscale and Apply Gaussian Blur
    gray_image = cv.cvtColor(input_image, cv.COLOR_BGR2GRAY)
    blurred_image = cv.GaussianBlur(gray_image, BLUR_SIZE, 0)

    # Edge Detection
    edges_detected = adjust_canny_thresholds(blurred_image)

    # Find Contours
    contour_list = cv.findContours(
        edges_detected.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contour_list = imutils_grab_contours(contour_list)
    (contour_list, _) = imutils_contours.sort_contours(contour_list)

    pixels_per_metric = None

    # Process Each Contour
    for single_contour in contour_list:
        if cv.contourArea(single_contour) < MIN_CONTOUR_AREA:
            continue

        # Calculate Rotated Bounding Box
        bounding_box = cv.minAreaRect(single_contour)
        bounding_box = cv.boxPoints(bounding_box)
        bounding_box = np.array(bounding_box, dtype="int")
        bounding_box = imutils_perspective.order_points(bounding_box)
        cv.drawContours(input_image, [bounding_box.astype(
            "int")], -1, BOX_COLOR, LINE_THICKNESS)

        for (x_coordinate, y_coordinate) in bounding_box:
            cv.circle(input_image, (int(x_coordinate), int(
                y_coordinate)), POINT_RADIUS, POINT_COLOR, -1)

        # Calculate Midpoints and Dimensions
        (top_left, top_right, bottom_right, bottom_left) = bounding_box
        (top_left_top_right_x, top_left_top_right_y) = calculate_midpoint(
            top_left, top_right)
        (bottom_left_bottom_right_x, bottom_left_bottom_right_y) = calculate_midpoint(
            bottom_left, bottom_right)
        (top_left_bottom_left_x, top_left_bottom_left_y) = calculate_midpoint(
            top_left, bottom_left)
        (top_right_bottom_right_x, top_right_bottom_right_y) = calculate_midpoint(
            top_right, bottom_right)

        cv.circle(input_image, (int(top_left_top_right_x), int(
            top_left_top_right_y)), POINT_RADIUS, LINE_COLOR, -1)
        cv.circle(input_image, (int(bottom_left_bottom_right_x), int(
            bottom_left_bottom_right_y)), POINT_RADIUS, LINE_COLOR, -1)
        cv.circle(input_image, (int(top_left_bottom_left_x), int(
            top_left_bottom_left_y)), POINT_RADIUS, LINE_COLOR, -1)
        cv.circle(input_image, (int(top_right_bottom_right_x), int(
            top_right_bottom_right_y)), POINT_RADIUS, LINE_COLOR, -1)
        cv.line(input_image, (int(top_left_top_right_x), int(top_left_top_right_y)), (int(
            bottom_left_bottom_right_x), int(bottom_left_bottom_right_y)), LINE_COLOR, LINE_THICKNESS)
        cv.line(input_image, (int(top_left_bottom_left_x), int(top_left_bottom_left_y)), (int(
            top_right_bottom_right_x), int(top_right_bottom_right_y)), LINE_COLOR, LINE_THICKNESS)

        distance_a = distance.euclidean((top_left_top_right_x, top_left_top_right_y), (
            bottom_left_bottom_right_x, bottom_left_bottom_right_y))
        distance_b = distance.euclidean((top_left_bottom_left_x, top_left_bottom_left_y), (
            top_right_bottom_right_x, top_right_bottom_right_y))

        if pixels_per_metric is None:
            pixels_per_metric = distance_b / reference_object_width

        dimension_a = distance_a / pixels_per_metric
        dimension_b = distance_b / pixels_per_metric

        cv.putText(input_image, f"{dimension_a:.1f}{MEASURE_UNIT}", (int(top_left_top_right_x - 15), int(
            top_left_top_right_y - 10)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
        cv.putText(input_image, f"{dimension_b:.1f}{MEASURE_UNIT}", (int(top_right_bottom_right_x + 10), int(
            top_right_bottom_right_y)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)

    # Display the Result
    cv.imshow(OUTPUT_WINDOW_NAME, input_image)
    cv.waitKey(0)
    cv.destroyAllWindows()


DIRECTORY = "test-images"
for file_name in os.listdir(DIRECTORY):
    # if not file_name.lower().endswith(('.png', '.jpg', '.jpeg')):
    #     continue

    if not file_name.lower().endswith('.jpeg'):
        continue

    if file_name.lower().startswith('coin-'):
        reference_object_width = REFERENCE_OBJECTS['coin'][MEASURE_UNIT]

    elif file_name.lower().startswith('card-'):
        reference_object_width = REFERENCE_OBJECTS['card'][MEASURE_UNIT]

    image_path = os.path.join(DIRECTORY, file_name)

    estimate_measurement(image_path, reference_object_width)

# image_path = "test-images/card-laptop.jpg"
# reference_object_width = REFERENCE_OBJECTS['card'][MEASURE_UNIT]
# estimate_measurement(image_path, reference_object_width)


actual_measurements = {
    # Item: Width, Height, Breath in cm
    "Laptop": [34, 24, 3],
    "Tissue Box": [24, 12, 8.5],
    "Mini Bucket": [16, 16, 15],
    "Milkpack": [9, 25, 6.2],
    "USB": [4, 1.2, 0.3],
    "Matchbox": [5.8, 4.5, 1.5],
    "Card": [8.5, 5.3],
    "2 Coin": [2, 2],
    "1 Coin": [1.8, 1.8],
    "5 Coin": [1.6, 1.6],
}
