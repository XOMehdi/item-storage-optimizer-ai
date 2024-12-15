import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import contours as imutils_contours
from imutils import grab_contours as imutils_grab_contours
from scipy.spatial import distance
import os

# Constants
IMAGES_DIRECTORY = "test-images"
MEASURE_UNIT = "in"
REFERENCE_OBJECTS = {
    "card": {"cm": 8.56, "in": 3.37},
    "coin": {"cm": 2.42, "in": 0.95},
}
BLUR_SIZE = (7, 7)
CANNY_KERNEL = np.ones((3, 3), np.uint8)
CANNY_DILATE_ITERATIONS = 5
CANNY_ERODE_ITERATIONS = 3
TEXT_FONT = cv.FONT_HERSHEY_SIMPLEX
TEXT_SCALE = 1.2
TEXT_COLOR = (0, 0, 0)
TEXT_THICKNESS = 3
BOX_COLOR = (0, 255, 0)
LINE_COLOR = (255, 0, 255)
LINE_THICKNESS = 2
OUTPUT_WINDOW_NAME = 'Image With Estimated Measurements'


# Functions
def calc_midpoint(first_point, second_point):
    midpoint_x = (first_point[0] + second_point[0]) * 0.5
    midpoint_y = (first_point[1] + second_point[1]) * 0.5
    return (midpoint_x, midpoint_y)


def adjust_canny_thresholds(input_image, upper_threshold=None):
    if upper_threshold == None:
        window_name = 'Canny Edge Detection'
        cv.namedWindow(window_name)
        cv.createTrackbar('Upper Threshold', window_name,
                          100, 255, lambda value: value)
        while True:
            upper_threshold = cv.getTrackbarPos(
                'Upper Threshold', window_name)
            edges_detected = cv.Canny(
                input_image, 10, upper_threshold)
            edges_detected = cv.dilate(
                edges_detected, CANNY_KERNEL, iterations=CANNY_DILATE_ITERATIONS)
            edges_detected = cv.erode(
                edges_detected, CANNY_KERNEL, iterations=CANNY_ERODE_ITERATIONS)

            cv.imshow(window_name, edges_detected)
            if cv.waitKey(1) & 0xFF == ord('q'):
                cv.destroyWindow(window_name)
                break
    else:
        edges_detected = cv.Canny(
            input_image, 10, upper_threshold)
        edges_detected = cv.dilate(
            edges_detected, CANNY_KERNEL, iterations=CANNY_DILATE_ITERATIONS)
        edges_detected = cv.erode(
            edges_detected, CANNY_KERNEL, iterations=CANNY_ERODE_ITERATIONS)

    return edges_detected


def calc_dimensions_px(contour):
    # Calculate Rotated Bounding Box
    bounding_box = cv.minAreaRect(contour)
    bounding_box = cv.boxPoints(bounding_box)
    bounding_box = np.array(bounding_box, dtype="int")
    bounding_box = imutils_perspective.order_points(bounding_box)

    # Calculate Midpoints and Dimensions
    (top_left, top_right, bottom_right, bottom_left) = bounding_box

    # Calculate Midpoints of Edges
    (top_edge_mid_x, top_edge_mid_y) = calc_midpoint(
        top_left, top_right)
    (bottom_edge_mid_x, bottom_edge_mid_y) = calc_midpoint(
        bottom_left, bottom_right)
    (left_edge_mid_x, left_edge_mid_y) = calc_midpoint(
        top_left, bottom_left)
    (right_edge_mid_x, right_edge_mid_y) = calc_midpoint(
        top_right, bottom_right)

    width_px = distance.euclidean((left_edge_mid_x, left_edge_mid_y), (
        right_edge_mid_x, right_edge_mid_y))
    height_px = distance.euclidean((top_edge_mid_x, top_edge_mid_y), (
        bottom_edge_mid_x, bottom_edge_mid_y))

    return width_px, height_px


def calc_pixels_per_metric(width_px, reference_object_width):
    return width_px / reference_object_width


def calc_dimensions_real(width_px, height_px, pixels_per_metric):
    real_width = width_px / pixels_per_metric
    real_height = height_px / pixels_per_metric

    return real_width, real_height


def estimate_measurement(image_path, reference_object_width):
    # Load and Preprocess the Image
    input_image = cv.imread(image_path)

    # Convert to Grayscale and Apply Gaussian Blur
    gray_image = cv.cvtColor(input_image, cv.COLOR_BGR2GRAY)
    blurred_image = cv.GaussianBlur(gray_image, BLUR_SIZE, 0)

    # Edge Detection
    edges_detected = adjust_canny_thresholds(
        blurred_image, upper_threshold=120)

    # Find Contours
    contour_list = cv.findContours(
        edges_detected.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contour_list = imutils_grab_contours(contour_list)
    (contour_list, _) = imutils_contours.sort_contours(contour_list)

    # Initiallize the Pixel per Metric
    reference_object_contour = contour_list[0]
    width_px, height_px = calc_dimensions_px(reference_object_contour)
    pixels_per_metric = calc_pixels_per_metric(
        width_px, reference_object_width)
    width_real, height_real = calc_dimensions_real(
        width_px, height_px, pixels_per_metric)

    contour_list = [contour_list[0], contour_list[-1]]

    # Process Each Contour
    for contour in contour_list:
        # Calculate Rotated Bounding Box
        bounding_box = cv.minAreaRect(contour)
        bounding_box = cv.boxPoints(bounding_box)
        bounding_box = np.array(bounding_box, dtype="int")
        bounding_box = imutils_perspective.order_points(bounding_box)
        cv.drawContours(input_image, [bounding_box.astype(
            "int")], -1, BOX_COLOR, LINE_THICKNESS)

        # Calculate Midpoints and Dimensions
        (top_left, top_right, bottom_right, bottom_left) = bounding_box
        (top_edge_mid_x, top_edge_mid_y) = calc_midpoint(
            top_left, top_right)
        (bottom_edge_mid_x, bottom_edge_mid_y) = calc_midpoint(
            bottom_left, bottom_right)
        (left_edge_mid_x, left_edge_mid_y) = calc_midpoint(
            top_left, bottom_left)
        (right_edge_mid_x, right_edge_mid_y) = calc_midpoint(
            top_right, bottom_right)

        cv.line(input_image, (int(top_edge_mid_x), int(top_edge_mid_y)), (int(
            bottom_edge_mid_x), int(bottom_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)
        cv.line(input_image, (int(left_edge_mid_x), int(left_edge_mid_y)), (int(
            right_edge_mid_x), int(right_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)

        width_px = distance.euclidean((left_edge_mid_x, left_edge_mid_y), (
            right_edge_mid_x, right_edge_mid_y))
        height_px = distance.euclidean((top_edge_mid_x, top_edge_mid_y), (
            bottom_edge_mid_x, bottom_edge_mid_y))

        width_real, height_real = calc_dimensions_real(
            width_px, height_px, pixels_per_metric)

        print(f"{width_real:.2f}, {height_real:.2f}")

        cv.putText(input_image, f"{width_real:.1f}{MEASURE_UNIT}", (int(left_edge_mid_x - 50), int(
            left_edge_mid_y)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
        cv.putText(input_image, f"{height_real:.1f}{MEASURE_UNIT}", (int(top_edge_mid_x - 15), int(
            top_edge_mid_y + 30)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)

    # Display the Result
    cv.imshow(OUTPUT_WINDOW_NAME, input_image)
    cv.waitKey(0)
    cv.destroyAllWindows()


for file_name in os.listdir(IMAGES_DIRECTORY):
    if file_name.lower().startswith('coin-'):
        reference_object_width = REFERENCE_OBJECTS['coin'][MEASURE_UNIT]

    elif file_name.lower().startswith('card-'):
        reference_object_width = REFERENCE_OBJECTS['card'][MEASURE_UNIT]

    image_path = os.path.join(IMAGES_DIRECTORY, file_name)

    estimate_measurement(image_path, reference_object_width)

# image_path = IMAGES_DIRECTORY + "/card-phone.jpg"
# reference_object_width = REFERENCE_OBJECTS['card'][MEASURE_UNIT]
# estimate_measurement(image_path, reference_object_width)

real_measurements_cm = {
    # Item: Width, Height, Breath
    "Card": [8.5, 5.3],
    "Laptop": [32.5, 21.5, 2.0],
    "Matchbox": [5.8, 4.5, 1.5],
    "Mouse": [11.8, 5.8, 2.4],
    "Phone": [15.5, 7.5, 0.8],
    "USB": [4, 1.2, 0.3],
    "Tissue Box": [24, 12, 8.5],
    "Mini Bucket": [16, 16, 15],
    "Milkpack": [9, 25, 6.2],
    "2 Coin": [2, 2],
    "1 Coin": [1.8, 1.8],
    "5 Coin": [1.6, 1.6],
}
