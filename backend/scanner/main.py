import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import contours as imutils_contours
from imutils import grab_contours as imutils_grab_contours
from scipy.spatial.distance import euclidean
import os

# Constants
IMAGES_DIRECTORY = "test-images"
MEASURE_UNIT = "cm"
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


def annotate_image(image, bounding_box, width_real, height_real):
    top_left, top_right, bottom_right, bottom_left = bounding_box

    # Calculate Midpoints of Edges
    (top_edge_mid_x, top_edge_mid_y) = calc_midpoint(
        top_left, top_right)
    (bottom_edge_mid_x, bottom_edge_mid_y) = calc_midpoint(
        bottom_left, bottom_right)
    (left_edge_mid_x, left_edge_mid_y) = calc_midpoint(
        top_left, bottom_left)
    (right_edge_mid_x, right_edge_mid_y) = calc_midpoint(
        top_right, bottom_right)

    cv.drawContours(image, [bounding_box.astype(
        "int")], -1, BOX_COLOR, LINE_THICKNESS)

    cv.line(image, (int(top_edge_mid_x), int(top_edge_mid_y)), (int(
            bottom_edge_mid_x), int(bottom_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)
    cv.line(image, (int(left_edge_mid_x), int(left_edge_mid_y)), (int(
            right_edge_mid_x), int(right_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)

    cv.putText(image, f"{width_real:.1f}{MEASURE_UNIT}", (int(left_edge_mid_x - 50), int(
        left_edge_mid_y)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
    cv.putText(image, f"{height_real:.1f}{MEASURE_UNIT}", (int(top_edge_mid_x - 15), int(
        top_edge_mid_y + 30)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)


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


def calc_midpoint(first_point, second_point):
    midpoint_x = (first_point[0] + second_point[0]) * 0.5
    midpoint_y = (first_point[1] + second_point[1]) * 0.5
    return (midpoint_x, midpoint_y)


def calc_dimensions_px(contour):
    # Calculate Rotated Bounding Box
    bounding_box = cv.minAreaRect(contour)
    bounding_box = cv.boxPoints(bounding_box)
    bounding_box = np.array(bounding_box, dtype="int")
    bounding_box = imutils_perspective.order_points(bounding_box)
    tl, tr, br, bl = bounding_box

    width_px = euclidean(calc_midpoint(tl, bl), calc_midpoint(tr, br))
    height_px = euclidean(
        calc_midpoint(tl, tr), calc_midpoint(bl, br))

    return width_px, height_px, bounding_box


def calc_pixels_per_metric(width_px, ref_obj_width_real):
    return width_px / ref_obj_width_real


def calc_dimensions_real(width_px, height_px, pixels_per_metric):
    real_width = round(width_px / pixels_per_metric, 2)
    real_height = round(height_px / pixels_per_metric, 2)

    return real_width, real_height


def get_two_largest_contours(contour_list):
    if len(contour_list) < 2:
        # raise ValueError("At least two contours are required")
        return contour_list[0], contour_list[0]

    # Find the two largest contours by area, but keep their original indices
    contour_areas = [(cv.contourArea(contour), index, contour)
                     for index, contour in enumerate(contour_list)]

    # Sort by area in descending order
    sorted_contours = sorted(contour_areas, key=lambda x: x[0], reverse=True)

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


def estimate_measurement(image_path, ref_obj_width_real):
    # Load and Preprocess the Image
    input_image = cv.imread(image_path)
    input_image = resize_image(input_image)

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

    ref_obj_contour, obj_contour = get_two_largest_contours(contour_list)

    ref_obj_width_px, ref_obj_height_px, ref_obj_bounding_box = calc_dimensions_px(
        ref_obj_contour)

    pixels_per_metric = calc_pixels_per_metric(
        ref_obj_width_px, ref_obj_width_real)

    _, ref_obj_height_real = calc_dimensions_real(
        ref_obj_width_px, ref_obj_height_px, pixels_per_metric)

    obj_width_px, obj_height_px, obj_bounding_box = calc_dimensions_px(
        obj_contour)
    obj_width_real, obj_height_real = calc_dimensions_real(
        obj_width_px, obj_height_px, pixels_per_metric)

    annotate_image(input_image, ref_obj_bounding_box,
                   ref_obj_width_real, ref_obj_height_real)
    annotate_image(input_image, obj_bounding_box,
                   obj_width_real, obj_height_real)

    # cv.imshow(OUTPUT_WINDOW_NAME, input_image)
    # cv.waitKey(0)
    # cv.destroyAllWindows()

    return {"width": obj_width_real, "height": obj_height_real}


def measure_3d_object(front_image_path, side_image_path, ref_obj):
    ref_obj_width_real = REFERENCE_OBJECTS[ref_obj][MEASURE_UNIT]

    front_measurements = estimate_measurement(
        front_image_path, ref_obj_width_real)
    side_measurements = estimate_measurement(
        side_image_path, ref_obj_width_real)

    width, height = front_measurements["width"], front_measurements["height"]
    side_width, side_height = side_measurements["width"], side_measurements["height"]

    # Determine the depth by picking the side measurement that doesn't match the front dimensions
    if side_width not in (width, height):
        depth = side_width
    elif side_height not in (width, height):
        depth = side_height
    else:
        depth = side_height  # Default fallback

    item = front_image_path.split("\\")[-1].split(".")[0]

    return {"item": item, "width": width, "height": height, "depth": depth}


# # Testing
# for file_name in os.listdir(IMAGES_DIRECTORY):
#     image_path = os.path.join(IMAGES_DIRECTORY, file_name)

#     item_dimensions = measure_3d_object(image_path, image_path, "card")
#     print(item_dimensions)

# item_dimensions = measure_3d_object(
#     IMAGES_DIRECTORY + "/card-usb-1.jpg", IMAGES_DIRECTORY + "/card-matchbox-2.jpg", "card")
# print(item_dimensions)


'''
real_measurements_cm = {
    # Item: Width, Height, Depth
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
'''
