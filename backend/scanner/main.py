import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import grab_contours as imutils_grab_contours
from imutils.contours import sort_contours as imutils_sort_contours
from scipy.spatial.distance import euclidean
import os


# Global variables for manual selection
manual_polygons = []
current_polygon = []
polygon_complete = False

# Constants
IMAGES_DIRECTORY = "test-images"
MEASURE_UNIT = "cm"
REFERENCE_OBJECTS = {
    "card": {"cm": 8.56, "in": 3.37},
    "coin": {"cm": 2.42, "in": 0.95},
}
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
BOX_PADDING = 10  # Padding around text
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


def adjust_canny_thresholds(image, upper_threshold=None):
    if upper_threshold == None:
        window_name = 'Canny Edge Detection'
        cv.namedWindow(window_name)
        cv.createTrackbar('Upper Threshold', window_name,
                          100, 255, lambda value: value)
        while True:
            upper_threshold = cv.getTrackbarPos(
                'Upper Threshold', window_name)
            edges_detected = cv.Canny(
                image, 10, upper_threshold)
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
            image, 10, upper_threshold)
        edges_detected = cv.dilate(
            edges_detected, CANNY_KERNEL, iterations=CANNY_DILATE_ITERATIONS)
        edges_detected = cv.erode(
            edges_detected, CANNY_KERNEL, iterations=CANNY_ERODE_ITERATIONS)

    return edges_detected


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


def get_sorting_order(ref_obj_pos):
    if (ref_obj_pos == "left"):
        return "left-to-right"
    elif (ref_obj_pos == "right"):
        return "right-to-left"
    elif (ref_obj_pos == "top"):
        return "top-to-bottom"
    elif (ref_obj_pos == "bottom"):
        return "bottom-to-top"

    return "left-to-right"


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
        "int")], -1, (0, 255, 0), LINE_THICKNESS)

    # Draw cross lines
    cv.line(image, (int(top_edge_mid_x), int(top_edge_mid_y)),
            (int(bottom_edge_mid_x), int(bottom_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)
    cv.line(image, (int(left_edge_mid_x), int(left_edge_mid_y)),
            (int(right_edge_mid_x), int(right_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)

    # Get text sizes
    (width_text, height_text), _ = cv.getTextSize(
        f"{width_real}{MEASURE_UNIT}", TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS)
    (height_text_h, width_text_h), _ = cv.getTextSize(
        f"{height_real}{MEASURE_UNIT}", TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS)

    # Positioning for width text
    width_text_x = int(left_edge_mid_x - 50)
    width_text_y = int(left_edge_mid_y)

    # Positioning for height text
    height_text_x = int(top_edge_mid_x - 15)
    height_text_y = int(top_edge_mid_y + 30)

    # Draw black rectangle for width text
    cv.rectangle(image,
                 (width_text_x - BOX_PADDING,
                  width_text_y - height_text - BOX_PADDING),
                 (width_text_x + width_text + BOX_PADDING,
                  width_text_y + BOX_PADDING),
                 BOX_COLOR, cv.FILLED)

    # Draw black rectangle for height text
    cv.rectangle(image,
                 (height_text_x - BOX_PADDING,
                  height_text_y - width_text_h - BOX_PADDING),
                 (height_text_x + height_text_h +
                  BOX_PADDING, height_text_y + BOX_PADDING),
                 BOX_COLOR, cv.FILLED)

    # Put text on top of black rectangles
    cv.putText(image, f"{width_real}{MEASURE_UNIT}", (width_text_x,
                                                      width_text_y), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
    cv.putText(image, f"{height_real}{MEASURE_UNIT}", (height_text_x,
                                                       height_text_y), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)


def draw_polygon(event, x, y, flags, param):
    global current_polygon, manual_polygons, polygon_complete

    if event == cv.EVENT_LBUTTONDOWN:
        # Add a new point to the current polygon
        current_polygon.append((x, y))

    elif event == cv.EVENT_RBUTTONDOWN and len(current_polygon) >= 3:
        # Close the current polygon if it has at least 3 points
        manual_polygons.append(np.array(current_polygon, dtype=np.int32))
        current_polygon = []  # Reset for the next polygon
        # Stop when two polygons are drawn
        polygon_complete = len(manual_polygons) >= 2


def get_manual_contours(image):
    global manual_polygons, current_polygon, polygon_complete

    manual_polygons = []
    current_polygon = []
    polygon_complete = False
    clone = image.copy()

    cv.namedWindow(
        "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)")
    cv.setMouseCallback(
        "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)", draw_polygon)

    while True:
        temp = clone.copy()

        # Draw all completed polygons
        for poly in manual_polygons:
            cv.polylines(temp, [poly], isClosed=True,
                         color=(0, 255, 0), thickness=2)

        # Draw the current polygon
        if len(current_polygon) > 1:
            cv.polylines(temp, [np.array(current_polygon, dtype=np.int32)],
                         isClosed=False, color=(0, 255, 255), thickness=2)

        cv.imshow(
            "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)", temp)

        key = cv.waitKey(1) & 0xFF

        if key == ord('z'):  # Undo feature
            if current_polygon:
                current_polygon.pop()  # Remove last point if still drawing
            elif manual_polygons:
                manual_polygons.pop()  # Remove last completed polygon

        if polygon_complete:
            break

    cv.destroyAllWindows()

    return manual_polygons[:2]  # Return the first two closed polygons


def get_contours(image):
    if MANUAL_SELECTION:
        return get_manual_contours(image)
    else:
        gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        blurred_image = cv.GaussianBlur(gray_image, BLUR_SIZE, 0)

        # Edge Detection
        edges_detected = adjust_canny_thresholds(
            blurred_image, upper_threshold=120)

        # Find Contours
        contour_list = cv.findContours(
            edges_detected, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contour_list = imutils_grab_contours(contour_list)
        return contour_list


def measure_2d_item(image_path, ref_obj_pos, ref_obj_width_real):
    # Load and Preprocess the Image
    image = cv.imread(image_path)
    image = resize_image(image)

    # Find Contours
    contour_list = get_contours(image)
    (contour_list, _) = imutils_sort_contours(
        contour_list, method=get_sorting_order(ref_obj_pos))

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

    annotate_image(image, ref_obj_bounding_box,
                   ref_obj_width_real, ref_obj_height_real)
    annotate_image(image, obj_bounding_box,
                   obj_width_real, obj_height_real)

    if DISPLAY_OUTPUT_WINDOW:
        cv.imshow(OUTPUT_WINDOW_NAME, image)
        cv.waitKey(0)
        cv.destroyAllWindows()

    return {"width": obj_width_real, "height": obj_height_real}


def measure_3d_item(front_image_path, side_image_path, ref_obj, ref_obj_pos):
    ref_obj_width_real = REFERENCE_OBJECTS[ref_obj][MEASURE_UNIT]

    front_measurements = measure_2d_item(
        front_image_path, ref_obj_pos, ref_obj_width_real)
    side_measurements = measure_2d_item(
        side_image_path, ref_obj_pos, ref_obj_width_real)

    front_width, front_height = front_measurements["width"], front_measurements["height"]
    side_width, side_height = side_measurements["width"], side_measurements["height"]

    # Store in a sorted list from largest to smallest
    dimensions = [front_width, front_height, side_width, side_height]
    dimensions.sort(reverse=True)

    # The smallest value is the depth
    width, height = dimensions[0], dimensions[1]
    depth = dimensions[3]

    # Check if the two largest values come from the same image
    if (dimensions[0] == front_width and dimensions[1] == front_height) or \
       (dimensions[0] == side_width and dimensions[1] == side_height):
        pass
    else:
        width, height = dimensions[0], dimensions[2]

    item_name = front_image_path.split("/")[-1].split(".")[0]

    return {"item": item_name, "width": width, "height": height, "depth": depth}


# Testing
if __name__ == "__main__":
    for file_name in os.listdir(IMAGES_DIRECTORY):
        image_path = os.path.join(IMAGES_DIRECTORY, file_name)

        if image_path.endswith("-1.jpg"):
            item_dimensions = measure_3d_item(
                image_path, image_path.replace("-1", "-2"), "card", "left")
            print(item_dimensions)
    # item_dimensions = measure_3d_item(
    #     IMAGES_DIRECTORY + "/card-usb-1.jpg", IMAGES_DIRECTORY + "/card-usb-2.jpg", "card", "left")
    # print(item_dimensions)


'''
real_measurements_cm = {
    # Item: Width, Height, Depth
    "Card": [8.5, 5.3],
    "Laptop": [32.5, 21.5, 2.0],
    "Matchbox": [5.8, 4.5, 1.5],
    "Mouse": [11.8, 5.8, 2.4],
    "Phone": [7.5, 15.5, 0.8],
    "USB": [4, 1.2, 0.3],
    "Tissue Box": [24, 12, 8.5],
    "Mini Bucket": [16, 16, 15],
    "Milkpack": [9, 25, 6.2],
    "2 Coin": [2, 2],
    "1 Coin": [1.8, 1.8],
    "5 Coin": [1.6, 1.6],
}
'''
