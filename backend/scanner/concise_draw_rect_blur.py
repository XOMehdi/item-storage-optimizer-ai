'''
todo:
- allow user to select position of reference object (top, bottom, left, right)
    - change get_two_largest_contours logic accordingly
'''

import os
import cv2 as cv
import numpy as np
from imutils.perspective import order_points
from imutils import grab_contours
from imutils.contours import sort_contours
from scipy.spatial.distance import euclidean


class Scanner:
    def __init__(self, ref_width_real, measure_unit):
        self.ref_width_real = ref_width_real
        self.measure_unit = measure_unit

        # Drawing variables
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.bounding_boxes = []
        self.temp_box = None
        self.image_copy = None

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
        self.output_window = "Estimated Dimensions"
        self.selection_window = "Select Areas With Items"

    # Private methods
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

    def process_image(self):
        self.image = self.resize_image(self.image)
        bg_blurred_image = self.apply_blur_with_boxes()
        gray_image = cv.cvtColor(bg_blurred_image, cv.COLOR_BGR2GRAY)
        blurred_image = cv.GaussianBlur(gray_image, self.blur_size, 0)

        return blurred_image

    def draw_rectangle(self, event, x, y, flags, param):

        temp_image = self.image.copy()
        if event == cv.EVENT_LBUTTONDOWN:  # Start drawing
            self.drawing = True
            self.start_x, self.start_y = x, y

        elif event == cv.EVENT_MOUSEMOVE and self.drawing:  # Update rectangle while dragging
            self.temp_box = (self.start_x, self.start_y, x, y)
            temp_image = self.image.copy()
            cv.rectangle(temp_image, (self.start_x, self.start_y),
                         (x, y), self.box_color, self.line_thickness)  # Show dynamic box
            cv.imshow(self.selection_window, temp_image)

        elif event == cv.EVENT_LBUTTONUP:  # Finalize selection
            self.drawing = False
            if self.start_x != x and self.start_y != y:  # Avoid zero-size boxes
                self.bounding_boxes.append((self.start_x, self.start_y, x, y))
                cv.rectangle(self.image, (self.start_x, self.start_y),
                             (x, y), self.box_color, self.line_thickness)  # Draw final box
            self.temp_box = None  # Reset temp box
            cv.imshow(self.selection_window, self.image)

    # todo: one difference
    def apply_blur_with_boxes(self, blur_strength=50):

        # Reset drawing variables
        self.bounding_boxes = []
        self.drawing = False
        self.start_x, self.start_y = -1, -1
        self.temp_box = None

        image_copy = self.image.copy()

        cv.namedWindow(self.selection_window)
        cv.setMouseCallback(self.selection_window, self.draw_rectangle)

        print("Draw rectangles over objects to keep. Press 'ENTER' when done. Press 'Z' to undo last selection.")

        while True:
            cv.imshow(self.selection_window, image_copy)
            key = cv.waitKey(1) & 0xFF
            if key == 13:  # Press ENTER to finish selection
                break
            elif key == ord('z') and self.bounding_boxes:  # Press 'Z' to undo last box
                self.bounding_boxes.pop()
                image_copy = self.image.copy()  # Reset image and redraw remaining boxes
                for (x1, y1, x2, y2) in self.bounding_boxes:
                    cv.rectangle(image_copy, (x1, y1), (x2, y2),
                                 self.box_color, self.line_thickness)
                cv.imshow(self.selection_window, image_copy)

        cv.destroyAllWindows()

        # If no bounding boxes were selected, return original image
        if not self.bounding_boxes:
            print("No bounding box selected. Returning original image.")
            return self.image

        # Create mask for selected bounding boxes
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)

        for (x1, y1, x2, y2) in self.bounding_boxes:
            mask[y1:y2, x1:x2] = 255  # Set selected area to white

        # Apply morphological operations to mask to close gaps in selection and smooth edges
        kernel = np.ones((10, 10), np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel)

        blurred_image = cv.GaussianBlur(self.image, (99, 99), blur_strength)

        # Convert mask to 3-channel format for bitwise operations with image (3-channel)
        mask_3ch = cv.merge([mask, mask, mask])

        # Blend images: Keep selected areas sharp, blur the rest
        result = np.where(mask_3ch == 255, self.image, blurred_image)

        return result

    def get_two_largest_contours(self, contours):
        if len(contours) < 2:
            return contours[0], contours[0] if contours else (None, None)

        # Sort contours by area in descending order, maintaining original indices
        sorted_contours = sorted(
            enumerate(contours), key=lambda x: cv.contourArea(x[1]), reverse=True)

        # Extract the two largest contours, ordered by their original indices
        ref_contour, obj_contour = (sorted_contours[1][1], sorted_contours[0][1]) if sorted_contours[0][0] < sorted_contours[1][0] else (
            sorted_contours[0][1], sorted_contours[1][1])

        return ref_contour, obj_contour

    def detect_edges(self, image, threshold=120):
        edges = cv.Canny(image, 10, threshold)
        edges = cv.dilate(edges, self.canny_kernel,
                          iterations=self.canny_dilate_iterations)
        edges = cv.erode(edges, self.canny_kernel,
                         iterations=self.canny_erode_iterations)
        return edges

    def get_contours(self, edges):
        contours_found = cv.findContours(
            edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours_found = grab_contours(contours_found)
        return sort_contours(contours_found)

    def calc_midpoint(self, first_point, second_point):
        midpoint_x = (first_point[0] + second_point[0]) * 0.5
        midpoint_y = (first_point[1] + second_point[1]) * 0.5
        return (midpoint_x, midpoint_y)

    def calc_dimensions_px(self, contour):
        # Calculate Rotated Bounding Box
        bounding_box = cv.minAreaRect(contour)
        bounding_box = cv.boxPoints(bounding_box)
        bounding_box = np.array(bounding_box, dtype="int")
        bounding_box = order_points(bounding_box)
        tl, tr, br, bl = bounding_box

        width_px = euclidean(self.calc_midpoint(
            tl, bl), self.calc_midpoint(tr, br))
        height_px = euclidean(
            self.calc_midpoint(tl, tr), self.calc_midpoint(bl, br))

        return width_px, height_px, bounding_box

    def calc_pixels_per_metric(self, width_px, ref_width_real):
        return width_px / ref_width_real

    def calc_dimensions_real(self, width_px, height_px, pixels_per_metric):
        real_width = round(width_px / pixels_per_metric, 2)
        real_height = round(height_px / pixels_per_metric, 2)

        return real_width, real_height

    def annotate_image(self, image, bounding_box, width_real, height_real):
        top_left, top_right, bottom_right, bottom_left = bounding_box

        # Calculate Midpoints of Edges
        (top_edge_mid_x, top_edge_mid_y) = self.calc_midpoint(
            top_left, top_right)
        (bottom_edge_mid_x, bottom_edge_mid_y) = self.calc_midpoint(
            bottom_left, bottom_right)
        (left_edge_mid_x, left_edge_mid_y) = self.calc_midpoint(
            top_left, bottom_left)
        (right_edge_mid_x, right_edge_mid_y) = self.calc_midpoint(
            top_right, bottom_right)

        cv.drawContours(image, [bounding_box.astype(
            "int")], -1, self.box_color, self.line_thickness)

        cv.line(image, (int(top_edge_mid_x), int(top_edge_mid_y)), (int(
                bottom_edge_mid_x), int(bottom_edge_mid_y)), self.line_color, self.line_thickness)
        cv.line(image, (int(left_edge_mid_x), int(left_edge_mid_y)), (int(
                right_edge_mid_x), int(right_edge_mid_y)), self.line_color, self.line_thickness)

        cv.putText(image, f"{width_real:.1f}{self.measure_unit}", (int(left_edge_mid_x - 50), int(
            left_edge_mid_y)), self.text_font, self.text_scale, self.text_color, self.text_thickness)
        cv.putText(image, f"{height_real:.1f}{self.measure_unit}", (int(top_edge_mid_x - 15), int(
            top_edge_mid_y + 30)), self.text_font, self.text_scale, self.text_color, self.text_thickness)

    def measure_2d_item(self, image_path):
        self.image = cv.imread(image_path)
        processed_image = self.process_image()
        edges_detected = self.detect_edges(processed_image)
        contours_found, _ = self.get_contours(edges_detected)
        if len(contours_found) < 2:
            print("Insufficient contours detected.")
            return None

        ref_contour, obj_contour = self.get_two_largest_contours(
            contours_found)

        if ref_contour is None or obj_contour is None:
            print("Insufficient contours found.")
            return None

        ref_obj_width_px, ref_obj_height_px, ref_obj_bounding_box = self.calc_dimensions_px(
            ref_contour)

        pixels_per_metric = self.calc_pixels_per_metric(
            ref_obj_width_px, ref_width_real)

        _, ref_obj_height_real = self.calc_dimensions_real(
            ref_obj_width_px, ref_obj_height_px, pixels_per_metric)

        obj_width_px, obj_height_px, obj_bounding_box = self.calc_dimensions_px(
            obj_contour)
        obj_width_real, obj_height_real = self.calc_dimensions_real(
            obj_width_px, obj_height_px, pixels_per_metric)

        self.annotate_image(processed_image, ref_obj_bounding_box,
                            ref_width_real, ref_obj_height_real)
        self.annotate_image(processed_image, obj_bounding_box,
                            obj_width_real, obj_height_real)

        cv.imshow(self.output_window, processed_image)
        cv.waitKey(0)
        cv.destroyAllWindows()

        return {"width": obj_width_real, "height": obj_height_real}

    # Public methods
    def measure_3d_item(self, front_image_path, side_image_path):

        front_measurements = self.measure_2d_item(front_image_path)
        side_measurements = self.measure_2d_item(side_image_path)

        width, height = front_measurements["width"], front_measurements["height"]
        side_width, side_height = side_measurements["width"], side_measurements["height"]

        # Determine the depth by picking the side measurement that doesn't match the front dimensions
        if side_width not in (width, height):
            depth = side_width
        elif side_height not in (width, height):
            depth = side_height
        else:
            depth = side_height  # Default fallback

        # Extract the item name from the image path
        item = front_image_path.split("\\")[-1].split(".")[0]

        return {"item": item, "width": width, "height": height, "depth": depth}


if __name__ == "__main__":

    # Set the reference object width (e.g., a card or a coin in cm)
    ref_width_real = 8.56  # Example: standard card width in cm
    measure_unit = "cm"

    # Initialize Scanner object
    scanner = Scanner(ref_width_real, measure_unit)
    images_directory = "test-images"
    for file_name in os.listdir(images_directory):

        # if file_name.lower().startswith("original-"):
        image_path = os.path.join(images_directory, file_name)

        # Run measurement estimation
        results = scanner.measure_3d_item(image_path, image_path)

        # Print the measured object dimensions
        print(f"Measured Object Dimensions: {results}")

# Example usage

# item_dimensions = measure_2d_item("test-images/card-matchbox-1.jpg", 8.56)
# print(item_dimensions)

# output = apply_blur_with_boxes("test-images/original-laptop.jpg")
# cv.imshow("Blurred Image", output)
# cv.waitKey(0)
# cv.destroyAllWindows()

# for file_name in os.listdir(IMAGES_DIRECTORY):

#     # if file_name.lower().startswith("original-"):
#     image_path = os.path.join(IMAGES_DIRECTORY, file_name)

#     output = measure_2d_item(image_path, 8.56)
