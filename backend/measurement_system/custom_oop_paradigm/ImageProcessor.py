import os
import cv2 as cv
from imutils import perspective as imutils_perspective
from imutils import grab_contours as imutils_grab_contours
from imutils.contours import sort_contours as imutils_sort_contours
from Config import *


class ImageProcessor:
    def __init__(self, image_path, item_id, item_side):
        self.image = cv.imread(image_path)
        self.image = self.resize_image(self.image)
        self.store_image(item_id, item_side)

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

    # Store image in backend file system
    def store_image(self, item_id, item_side):
        item_directory = os.path.join(Config.IMAGES_DIRECTORY, item_id)
        os.makedirs(item_directory, exist_ok=True)

        filename = os.path.join(item_directory, f"{item_side}.jpg")
        success = cv.imwrite(filename, self.image)
        if success:
            print(f"Image saved at: {filename}")
        else:
            print("Error: Could not save the image.")

    # Retrieve specified image from backend file system
    def retrieve_image(self, item_id, item_side):
        filename = os.path.join(Config.IMAGES_DIRECTORY,
                                item_id, f"{item_side}.jpg")

        # Check if the file exists
        if os.path.exists(filename):
            return filename  # Return image path

        print(f"Error: Image '{filename}' not found.")
        return None

    def convert_to_grayscale(self):
        self.image = cv.cvtColor(self.image, cv.COLOR_BGR2GRAY)

    def apply_gaussian_blur(self):
        self.image = cv.GaussianBlur(self.image, Config.BLUR_SIZE, 0)

    def detect_edges(self, upper_threshold=120):
        edges = cv.Canny(self.image, 10, upper_threshold)
        edges = cv.dilate(edges, Config.CANNY_KERNEL,
                          iterations=Config.CANNY_DILATE_ITERATIONS)
        edges = cv.erode(edges, Config.CANNY_KERNEL,
                         iterations=Config.CANNY_ERODE_ITERATIONS)

        return edges

    def get_contours(self):
        if Config.MANUAL_SELECTION:
            return self.get_manual_contours(self.image)
        else:
            self.convert_to_grayscale()
            self.apply_gaussian_blur()

            # Edge Detection
            edges_detected = self.detect_edges()

            # Find Contours
            contour_list = cv.findContours(
                edges_detected, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
            contour_list = imutils_grab_contours(contour_list)
            return contour_list

    def draw_polygon(self, event, x, y, flags, param):
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

    def get_manual_contours(self, image):
        global manual_polygons, current_polygon, polygon_complete

        manual_polygons = []
        current_polygon = []
        polygon_complete = False
        clone = image.copy()

        cv.namedWindow(
            "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)")
        cv.setMouseCallback(
            "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)", self.draw_polygon)

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
