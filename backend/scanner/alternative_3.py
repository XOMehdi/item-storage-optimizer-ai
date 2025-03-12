'''
todo:
- allow user to select position of reference object (top, bottom, left, right)
    - change get_two_largest_contours logic accordingly
'''

import os
import cv2 as cv
import numpy as np
from imutils import perspective as imutils_perspective
from imutils import grab_contours as imutils_grab_contours
# from imutils import contours as imutils_contours
from imutils.contours import sort_contours as imutils_sort_contours

from scipy.spatial.distance import euclidean


class Scanner:
    def __init__(self, measure_unit="cm"):
        self.measure_unit = measure_unit
        self.ref_objects = {"card": {"cm": 8.56, "in": 3.37},
                            "coin": {"cm": 2.42, "in": 0.95}}
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.bounding_boxes = []
        self.temp_box = None

        # Constants
        self.blur_size = (7, 7)
        self.canny_kernel = np.ones((3, 3), np.uint8)
        self.canny_dilate_iterations = 5
        self.canny_erode_iterations = 3
        self.text_font = cv.FONT_HERSHEY_SIMPLEX
        self.text_scale = 1.2
        self.text_color = (0, 0, 0)
        self.text_thickness = 3
        self.box_color = (0, 255, 0)
        self.line_color = (255, 0, 255)
        self.line_thickness = 2
        self.output_window = "Image With Estimated Measurements"
        self.selection_window = "Select Focus Area"

    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_x, self.start_y = x, y

        elif event == cv.EVENT_MOUSEMOVE and self.drawing:
            self.temp_box = (self.start_x, self.start_y, x, y)
            temp_image = self.image.copy()
            cv.rectangle(temp_image, (self.start_x, self.start_y),
                         (x, y), self.box_color, self.line_thickness)
            cv.imshow(self.selection_window, temp_image)

        elif event == cv.EVENT_LBUTTONUP:
            self.drawing = False
            if self.start_x != x and self.start_y != y:
                self.bounding_boxes.append((self.start_x, self.start_y, x, y))
                cv.rectangle(self.image, (self.start_x, self.start_y),
                             (x, y), self.box_color, self.line_thickness)
            self.temp_box = None
            cv.imshow(self.selection_window, self.image)

    def resize_image(self, image, max_width=1920, max_height=1080):
        height, width = image.shape[:2]
        aspect_ratio = width / height

        if width > max_width or height > max_height:
            if width > max_width:
                width = max_width
                height = int(width / aspect_ratio)
            if height > max_height:
                height = max_height
                width = int(height * aspect_ratio)

        return cv.resize(image, (width, height), interpolation=cv.INTER_LANCZOS4)

    def apply_blur_with_boxes(self, image_path, blur_strength=50):
        self.bounding_boxes = []
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.temp_box = None

        self.image = cv.imread(image_path)
        self.image = self.resize_image(self.image)
        image_copy = self.image.copy()

        cv.namedWindow(self.selection_window)
        cv.setMouseCallback(self.selection_window, self.draw_rectangle)

        print("Draw rectangles over objects to keep. Press 'ENTER' when done. Press 'Z' to undo last selection.")

        while True:
            cv.imshow(self.selection_window, self.image)
            key = cv.waitKey(1) & 0xFF
            if key == 13:  # Press ENTER to finish selection
                break
            elif key == ord('z') and self.bounding_boxes:
                self.bounding_boxes.pop()
                self.image = image_copy.copy()
                for (x1, y1, x2, y2) in self.bounding_boxes:
                    cv.rectangle(self.image, (x1, y1), (x2, y2),
                                 self.box_color, self.line_thickness)
                cv.imshow(self.selection_window, self.image)

        cv.destroyAllWindows()
        if not self.bounding_boxes:
            print("No bounding box selected. Returning original image.")
            return self.image

        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        for (x1, y1, x2, y2) in self.bounding_boxes:
            mask[y1:y2, x1:x2] = 255

        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE,
                               np.ones((10, 10), np.uint8))
        blurred_image = cv.GaussianBlur(self.image, (99, 99), blur_strength)
        mask_3ch = cv.merge([mask, mask, mask])

        return np.where(mask_3ch == 255, self.image, blurred_image)

    def get_two_largest_contours(self, contours):
        if len(contours) < 2:
            return contours[0], contours[0] if contours else (None, None)

        # Sort contours by area in descending order, maintaining original indices
        sorted_contours = sorted(
            enumerate(contours), key=lambda x: cv.contourArea(x[1]), reverse=True)

        # Extract the two largest contours, ordered by their original indices
        ref_obj_contour, obj_contour = (sorted_contours[1][1], sorted_contours[0][1]) if sorted_contours[0][0] < sorted_contours[1][0] else (
            sorted_contours[0][1], sorted_contours[1][1])

        return ref_obj_contour, obj_contour

    def estimate_measurement(self, image_path, ref_obj_width_real):
        processed_image = self.apply_blur_with_boxes(image_path)
        gray_image = cv.cvtColor(processed_image, cv.COLOR_BGR2GRAY)
        blurred_image = cv.GaussianBlur(gray_image, self.blur_size, 0)
        edges_detected = cv.Canny(blurred_image, 10, 120)
        edges_detected = cv.dilate(
            edges_detected, self.canny_kernel, iterations=self.canny_dilate_iterations)
        edges_detected = cv.erode(
            edges_detected, self.canny_kernel, iterations=self.canny_erode_iterations)

        contours_found = cv.findContours(
            edges_detected, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_found = imutils_grab_contours(contours_found)
        contours_found, _ = imutils_sort_contours(contours_found)

        ref_contour, obj_contour = self.get_two_largest_contours(
            contours_found)
        if ref_contour is None or obj_contour is None:
            print("Insufficient contours found.")
            return None

        ref_width_px = cv.minAreaRect(ref_contour)[1][0]
        pixels_per_metric = ref_width_px / ref_obj_width_real
        obj_width_px = cv.minAreaRect(obj_contour)[1][0]
        obj_width_real = obj_width_px / pixels_per_metric

        return {"width": round(obj_width_real, 2)}


if __name__ == "__main__":
    # Set the reference object width (e.g., a card or a coin in cm)
    reference_width = 8.56  # Example: standard card width in cm

    # Initialize Scanner object
    scanner = Scanner()
    IMAGES_DIRECTORY = "test-images"
    for file_name in os.listdir(IMAGES_DIRECTORY):

        # if file_name.lower().startswith("original-"):
        image_path = os.path.join(IMAGES_DIRECTORY, file_name)

        # Run measurement estimation
        results = scanner.estimate_measurement(image_path, reference_width)

        # Print the measured object dimensions
        print(f"Measured Object Dimensions: {results}")

# Example usage

# item_dimensions = estimate_measurement("test-images/card-matchbox-1.jpg", 8.56)
# print(item_dimensions)

# output = apply_blur_with_boxes("test-images/original-laptop.jpg")
# cv.imshow("Blurred Image", output)
# cv.waitKey(0)
# cv.destroyAllWindows()

# for file_name in os.listdir(IMAGES_DIRECTORY):

#     # if file_name.lower().startswith("original-"):
#     image_path = os.path.join(IMAGES_DIRECTORY, file_name)

#     output = estimate_measurement(image_path, 8.56)
