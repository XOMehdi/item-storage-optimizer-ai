import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import contours as imutils_contours
from imutils import grab_contours as imutils_grab_contours
from scipy.spatial import distance
import os


# Global variables
g_drawing = False  # True when drawing a rectangle
g_ix, g_iy = -1, -1  # Starting coordinates
g_selected_boxes = []  # Stores final bounding boxes
g_temp_box = None  # Temporary box for real-time preview


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
def resize_image(image, max_width=1600, max_height=900):
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
    global g_ix, g_iy, g_drawing, g_selected_boxes, g_temp_box, img_copy

    img_temp = img_copy.copy()  # Reset image to redraw dynamically

    if event == cv.EVENT_LBUTTONDOWN:  # Start drawing
        g_drawing = True
        g_ix, g_iy = x, y

    elif event == cv.EVENT_MOUSEMOVE:  # Update rectangle while dragging
        if g_drawing:
            g_temp_box = (g_ix, g_iy, x, y)
            cv.rectangle(img_temp, (g_ix, g_iy), (x, y),
                         (0, 255, 0), 5)  # Show dynamic box
            cv.imshow("Select Focus Area", img_temp)

    elif event == cv.EVENT_LBUTTONUP:  # Finalize selection
        g_drawing = False
        if g_ix != x and g_iy != y:  # Avoid zero-size boxes
            g_selected_boxes.append((g_ix, g_iy, x, y))
            cv.rectangle(img_copy, (g_ix, g_iy), (x, y),
                         (0, 255, 0), 5)  # Draw final box
        g_temp_box = None  # Reset temp box
        cv.imshow("Select Focus Area", img_copy)


# Mouse callback function for interactive polygon selection
def draw_polygon(event, x, y, flags, param):
    global g_drawing, g_selected_boxes, g_temp_box, img_copy, g_polygon_points

    img_temp = img_copy.copy()  # Reset image to redraw dynamically

    if event == cv.EVENT_LBUTTONDOWN:  # Start drawing
        g_drawing = True
        g_polygon_points.append((x, y))

    elif event == cv.EVENT_MOUSEMOVE:  # Update polygon while dragging
        if g_drawing:
            img_temp = img_copy.copy()
            if len(g_polygon_points) > 0:
                cv.polylines(img_temp, [np.array(
                    g_polygon_points + [(x, y)], np.int32)], False, (0, 255, 0), 5)
            cv.imshow("Select Focus Area", img_temp)

    elif event == cv.EVENT_RBUTTONDOWN:  # Finalize selection
        g_drawing = False
        if len(g_polygon_points) > 2:  # Avoid zero-size or line polygons
            g_polygon_points.append((x, y))
            g_selected_boxes.append(np.array(g_polygon_points, np.int32))
            # Draw final polygon
            cv.polylines(
                img_copy, [np.array(g_polygon_points, np.int32)], True, (0, 255, 0), 5)
        g_polygon_points = []  # Reset polygon points
        cv.imshow("Select Focus Area", img_copy)


# Function to remove background while keeping focus areas
def remove_background(image, polygon=False):
    global img, img_copy, g_polygon_points, g_ix, g_iy, g_drawing, g_selected_boxes, g_temp_box

    # Reset global variables
    g_polygon_points = []  # Stores polygon points
    g_drawing = False  # True when drawing a rectangle
    g_ix, g_iy = -1, -1  # Starting coordinates
    g_selected_boxes = []  # Stores final bounding boxes
    g_temp_box = None  # Temporary box for real-time preview

    img_copy = image.copy()

    # Interactive selection
    cv.namedWindow("Select Focus Area")

    if polygon:
        g_polygon_points = []

        cv.setMouseCallback("Select Focus Area", draw_polygon)

        print("Draw polygons over the objects to keep. Press 'ENTER' when done. Press 'Z' to undo last selection.")

        while True:
            cv.imshow("Select Focus Area", img_copy)
            key = cv.waitKey(1) & 0xFF
            if key == 13:  # Press ENTER to finish selection
                break
            elif key == ord('z') and g_selected_boxes:  # Press 'Z' to undo last box
                g_selected_boxes.pop()
                img_copy = image.copy()  # Reset image and redraw remaining boxes
                for polygon in g_selected_boxes:
                    cv.polylines(img_copy, [polygon], True, (0, 255, 0), 2)
                cv.imshow("Select Focus Area", img_copy)

        cv.destroyAllWindows()

        # Create a binary mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for polygon in g_selected_boxes:
            cv.fillPoly(mask, [polygon], 255)  # Mark foreground

    else:
        cv.setMouseCallback("Select Focus Area", draw_rectangle)

        print("Draw rectangles over the objects to keep. Press 'ENTER' when done. Press 'Z' to undo last selection.")

        while True:
            cv.imshow("Select Focus Area", img_copy)
            key = cv.waitKey(1) & 0xFF
            if key == 13:  # Press ENTER to finish selection
                break
            elif key == ord('z') and g_selected_boxes:  # Press 'Z' to undo last box
                g_selected_boxes.pop()
                img_copy = image.copy()  # Reset image and redraw remaining boxes
                for (x1, y1, x2, y2) in g_selected_boxes:
                    cv.rectangle(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv.imshow("Select Focus Area", img_copy)

        cv.destroyAllWindows()

        # Create a binary mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for (x1, y1, x2, y2) in g_selected_boxes:
            mask[y1:y2, x1:x2] = 255  # Mark foreground

    # Apply morphological operations to smooth edges
    kernel = np.ones((10, 10), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

    # Create a green background
    image[mask == 0] = (0, 255, 0)  # Set background to green

    # Keep only BGR (no alpha channel needed)
    img_green_bg = image

    return img_green_bg


def calc_midpoint(pt1, pt2):
    return ((pt1[0] + pt2[0]) / 2, (pt1[1] + pt2[1]) / 2)


def adjust_canny_thresholds(image, upper_threshold=120):
    edges = cv.Canny(image, 10, upper_threshold)
    edges = cv.dilate(edges, CANNY_KERNEL, iterations=CANNY_DILATE_ITERATIONS)
    edges = cv.erode(edges, CANNY_KERNEL, iterations=CANNY_ERODE_ITERATIONS)
    return edges


def calc_dimensions_px(contour):
    box = cv.minAreaRect(contour)
    box = cv.boxPoints(box)
    box = np.array(box, dtype="int")
    box = imutils_perspective.order_points(box)
    (tl, tr, br, bl) = box

    width_px = distance.euclidean(calc_midpoint(tl, bl), calc_midpoint(tr, br))
    height_px = distance.euclidean(
        calc_midpoint(tl, tr), calc_midpoint(bl, br))
    return width_px, height_px, box


def calc_pixels_per_metric(width_px, reference_width):
    return width_px / reference_width


def calc_real_dimensions(width_px, height_px, ppm):
    return round(width_px / ppm, 2), round(height_px / ppm, 2)


def annotate_image(image, bounding_box, width_real, height_real):
    tl, tr, br, bl = bounding_box
    cv.drawContours(image, [bounding_box.astype(
        "int")], -1, BOX_COLOR, LINE_THICKNESS)

    width_mid_top = calc_midpoint(tl, tr)
    width_mid_bottom = calc_midpoint(bl, br)

    height_mid_top = calc_midpoint(tl, bl)
    height_mid_bottom = calc_midpoint(tr, br)

    cv.line(image, (int(width_mid_top[0]), int(width_mid_top[1])), (int(
        width_mid_bottom[0]), int(width_mid_bottom[1])), LINE_COLOR, LINE_THICKNESS)

    cv.line(image, (int(height_mid_top[0]), int(height_mid_top[1])), (int(
        height_mid_bottom[0]), int(height_mid_bottom[1])), LINE_COLOR, LINE_THICKNESS)

    cv.putText(image, f"{width_real:.1f}{MEASURE_UNIT}", (int(
        height_mid_top[0] - 50), int(height_mid_top[1])), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)
    cv.putText(image, f"{height_real:.1f}{MEASURE_UNIT}", (int(
        width_mid_top[0] - 15), int(width_mid_top[1] + 30)), TEXT_FONT, TEXT_SCALE, TEXT_COLOR, TEXT_THICKNESS)

    cv.imshow(OUTPUT_WINDOW_NAME, image)
    cv.waitKey(0)
    cv.destroyAllWindows()


def measure_object(image_path, reference_object, annotate=True):

    image = cv.imread(image_path)
    image = resize_image(image)
    image = remove_background(image, polygon=False)

    # image = cv.imread(image_path)
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, BLUR_SIZE, 0)
    edges = adjust_canny_thresholds(blurred)
    contours = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = imutils_grab_contours(contours)

    contours, _ = imutils_contours.sort_contours(contours)

    ref_contour = contours[0]
    ref_width_px, ref_height_px, ref_bounding_box = calc_dimensions_px(
        ref_contour)
    ppm = calc_pixels_per_metric(
        ref_width_px, REFERENCE_OBJECTS[reference_object][MEASURE_UNIT])

    ref_width, ref_height = calc_real_dimensions(
        ref_width_px, ref_height_px, ppm)

    obj_contour = contours[-1]
    obj_width_px, obj_height_px, obj_bounding_box = calc_dimensions_px(
        obj_contour)
    obj_width, obj_height = calc_real_dimensions(
        obj_width_px, obj_height_px, ppm)

    if annotate:
        annotate_image(image, ref_bounding_box, ref_width, ref_height)
        annotate_image(image, obj_bounding_box, obj_width, obj_height)

    return {"width": obj_width, "height": obj_height}


def measure_3d_object(front_image_path, side_image_path, reference_object):
    front_measurements = measure_object(front_image_path, reference_object)
    side_measurements = measure_object(side_image_path, reference_object)

    return {
        "width": front_measurements["width"],
        "height": front_measurements["height"],
        "depth": side_measurements["height"],
    }


# # Example usage:
# item_dimensions = measure_3d_object(
#     "test-images/card-usb-1.jpg", "test-images/card-usb-2.jpg", "card")
# print(item_dimensions)

for file_name in os.listdir(IMAGES_DIRECTORY):

    # if file_name.lower().startswith("original-"):
    image_path = os.path.join(IMAGES_DIRECTORY, file_name)

    item_dimensions = measure_3d_object(image_path, image_path, "card")
    print(item_dimensions)

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
