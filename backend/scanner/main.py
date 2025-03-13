import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import grab_contours as imutils_grab_contours
from imutils.contours import sort_contours as imutils_sort_contours
from scipy.spatial.distance import euclidean
import os


# Global variables for interactive selection
drawing = False  # True when drawing a rectangle
ix, iy = -1, -1  # Initial x, y coordinates
boxes = []  # Stores selected bounding boxes
temp_box = None  # Temporary box for real-time preview


# Constants
IMAGES_DIRECTORY = "test-images"
MEASURE_UNIT = "cm"
REFERENCE_OBJECTS = {
    "card": {"cm": 8.56, "in": 3.37},
    "coin": {"cm": 2.42, "in": 0.95},
}
ENABLE_BLUR_SELECTION = False
DISPLAY_OUTPUT_WINDOW = False
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


# Mouse callback function for interactive bounding box selection
def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, boxes, temp_box, img_copy

    img_temp = img_copy.copy()  # Reset image to redraw dynamically

    if event == cv.EVENT_LBUTTONDOWN:  # Start drawing
        drawing = True
        ix, iy = x, y

    elif event == cv.EVENT_MOUSEMOVE:  # Update rectangle while dragging
        if drawing:
            temp_box = (ix, iy, x, y)
            cv.rectangle(img_temp, (ix, iy), (x, y),
                         BOX_COLOR, LINE_THICKNESS)  # Show dynamic box
            cv.imshow("Select Focus Area", img_temp)

    elif event == cv.EVENT_LBUTTONUP:  # Finalize selection
        drawing = False
        if ix != x and iy != y:  # Avoid zero-size boxes
            boxes.append((ix, iy, x, y))
            cv.rectangle(img_copy, (ix, iy), (x, y),
                         BOX_COLOR, LINE_THICKNESS)  # Draw final box
        temp_box = None  # Reset temp box
        cv.imshow("Select Focus Area", img_copy)


# Function to apply blur effect while keeping selected areas sharp
def apply_blur_with_boxes(img, blur_strength=50):
    global img_copy, boxes, drawing, ix, iy, temp_box

    # Reset global variables
    boxes = []
    drawing = False
    ix, iy = -1, -1
    temp_box = None

    # Load and resize the image
    img_copy = img.copy()

    # Interactive selection
    cv.namedWindow("Select Focus Area")
    cv.setMouseCallback("Select Focus Area", draw_rectangle)

    print("Draw rectangles over the objects to keep. Press 'ENTER' when done. Press 'Z' to undo last selection.")

    while True:
        cv.imshow("Select Focus Area", img_copy)
        key = cv.waitKey(1) & 0xFF
        if key == 13:  # Press ENTER to finish selection
            break
        elif key == ord('z') and boxes:  # Press 'Z' to undo last box
            boxes.pop()
            img_copy = img.copy()  # Reset image and redraw remaining boxes
            for (x1, y1, x2, y2) in boxes:
                cv.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv.imshow("Select Focus Area", img_copy)

    cv.destroyAllWindows()

    # If no bounding boxes were selected, return original image
    if not boxes:
        print("No bounding box selected. Returning original image.")
        return img  # Return the unmodified image

    # Create a mask for selected focus areas
    mask = np.zeros(img.shape[:2], dtype=np.uint8)

    for (x1, y1, x2, y2) in boxes:
        mask[y1:y2, x1:x2] = 255  # Mark foreground (focus area) as white

    # Apply morphological operations to smooth edges
    kernel = np.ones((10, 10), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

    # Create a blurred version of the image
    blurred_img = cv.GaussianBlur(img, (99, 99), blur_strength)

    # Convert mask to 3 channels
    mask_3ch = cv.merge([mask, mask, mask])

    # Blend images: Keep selected areas sharp, blur the rest
    result = np.where(mask_3ch == 255, img, blurred_img)

    return result


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
        "int")], -1, BOX_COLOR, LINE_THICKNESS)

    cv.line(image, (int(top_edge_mid_x), int(top_edge_mid_y)), (int(
            bottom_edge_mid_x), int(bottom_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)
    cv.line(image, (int(left_edge_mid_x), int(left_edge_mid_y)), (int(
            right_edge_mid_x), int(right_edge_mid_y)), LINE_COLOR, LINE_THICKNESS)

    cv.putText(image, f"{width_real:.1f}{MEASURE_UNIT}", (int(left_edge_mid_x - 50), int(
        left_edge_mid_y)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
    cv.putText(image, f"{height_real:.1f}{MEASURE_UNIT}", (int(top_edge_mid_x - 15), int(
        top_edge_mid_y + 30)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)


def measure_2d_item(image_path, ref_obj_pos, ref_obj_width_real):
    # Load and Preprocess the Image
    image = cv.imread(image_path)
    image = resize_image(image)

    if ENABLE_BLUR_SELECTION:
        image = apply_blur_with_boxes(image)

    # Convert to Grayscale and Apply Gaussian Blur
    gray_image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred_image = cv.GaussianBlur(gray_image, BLUR_SIZE, 0)

    # Edge Detection
    edges_detected = adjust_canny_thresholds(
        blurred_image, upper_threshold=120)

    # Find Contours
    contour_list = cv.findContours(
        edges_detected, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contour_list = imutils_grab_contours(contour_list)
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

#     item_dimensions = measure_3d_item(image_path, image_path, "card", "left")
#     print(item_dimensions)

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
