import cv2
import numpy as np


def load_image(image_path):
    """Loads an image from the given path."""
    return cv2.imread(image_path)


def preprocess_image(image):
    """Converts the image to grayscale and applies thresholding."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresholded = cv2.threshold(blurred, 60, 255, cv2.THRESH_BINARY)
    return thresholded


def extract_features(image):
    """Extracts keypoints and descriptors using ORB."""
    orb = cv2.ORB_create()
    keypoints, descriptors = orb.detectAndCompute(image, None)
    return keypoints, descriptors


def match_features(descriptors_ref, descriptors_item):
    """Matches features using FLANN-based matcher."""
    index_params = dict(algorithm=6,  # FLANN_INDEX_LSH
                        table_number=6,
                        key_size=12,
                        multi_probe_level=1)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(descriptors_ref, descriptors_item, k=2)

    # Apply ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)
    return good_matches


def identify_reference_object(ref_image, contours, item_image):
    """Identifies the reference object using feature matching."""
    ref_gray = cv2.cvtColor(ref_image, cv2.COLOR_BGR2GRAY)
    keypoints_ref, descriptors_ref = extract_features(ref_gray)

    for contour in contours:
        # Get bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)
        roi = item_image[y:y+h, x:x+w]

        # Extract features of the ROI
        roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        keypoints_item, descriptors_item = extract_features(roi_gray)

        # Match features
        matches = match_features(descriptors_ref, descriptors_item)
        if len(matches) > 10:  # Threshold for good matches
            return x, y, w, h  # Return reference object's bounding box

    raise ValueError("Reference object not found.")


def calculate_pixels_per_metric(ref_box, ref_width_cm):
    """Calculates the pixel-to-metric ratio."""
    _, _, ref_width_pixels, _ = ref_box
    ppm = ref_width_pixels / ref_width_cm
    return ppm


def calculate_real_dimensions(box, ppm):
    """Converts dimensions from pixels to centimeters."""
    _, _, width_pixels, height_pixels = box
    width_cm = width_pixels / ppm
    height_cm = height_pixels / ppm
    return width_cm, height_cm


def main(reference_image_path, measurement_image_path, ref_width_cm, ref_height_cm):
    # Load images
    ref_image = load_image(reference_image_path)
    measurement_image = load_image(measurement_image_path)

    # Preprocess the measurement image
    preprocessed = preprocess_image(measurement_image)

    # Find contours of objects in the image
    contours, _ = cv2.findContours(
        preprocessed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Identify the reference object
    ref_box = identify_reference_object(ref_image, contours, measurement_image)

    # Calculate pixels-per-metric (PPM)
    ppm = calculate_pixels_per_metric(ref_box, ref_width_cm)

    # Find the item to be measured (assume largest contour is the item)
    largest_contour = max(contours, key=cv2.contourArea)
    item_box = cv2.boundingRect(largest_contour)

    # Calculate real dimensions of the item
    item_width_cm, item_height_cm = calculate_real_dimensions(item_box, ppm)

    print(f"Reference Object: {ref_box}")
    print(f"Item to be Measured: {item_box}")
    print(
        f"Item Dimensions (in cm): Width = {item_width_cm:.2f}, Height = {item_height_cm:.2f}")
    return item_width_cm, item_height_cm


# Example Usage
if __name__ == "__main__":
    reference_image_path = "./test-images/card.jpg"
    measurement_image_path = "./test-images/laptop.jpg"
    ref_width_cm = 8.56  # Example: Width of a credit card
    ref_height_cm = 5.40  # Example: Height of a credit card

    main(reference_image_path, measurement_image_path, ref_width_cm, ref_height_cm)
