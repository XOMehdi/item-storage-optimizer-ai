import requests
import base64
import cv2 as cv
import numpy as np


# Global variables for manual selection
manual_polygons = []
current_polygon = []
polygon_complete = False


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


def get_manual_contours(image_path):

    image = cv.imread(image_path)
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

    # Convert NumPy arrays to Python lists
    return [poly.tolist() for poly in manual_polygons[:2]]


# Your Railway API URL (replace with actual deployed URL)
# API_URL = "http://13.60.238.130:5000/measure"
API_URL = "https://measurementsystemapi.up.railway.app/measure"
API_URL = "https://measurementsystem.up.railway.app/measure"



# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


# Function to decode base64 image and display it
def decode_and_display_image(image_b64, window_name):
    image_data = base64.b64decode(image_b64)
    np_arr = np.frombuffer(image_data, np.uint8)
    image = cv.imdecode(np_arr, cv.IMREAD_COLOR)

    if image is not None:
        cv.imshow(window_name, image)
        cv.waitKey(0)  # Wait for key press
        cv.destroyAllWindows()  # Close window after key press
    else:
        print(f"❌ Error displaying {window_name}")


# Example image paths (update with actual paths)
front_image_path = "images/card-matchbox-1.jpg"
side_image_path = "images/card-matchbox-2.jpg"
polygon1 = get_manual_contours("images/card-matchbox-1.jpg")
polygon2 = get_manual_contours("images/card-matchbox-2.jpg")


# Convert images to base64
front_image_b64 = encode_image(front_image_path)
side_image_b64 = encode_image(side_image_path)

# API request payload
payload = {
    "front_image": front_image_b64,
    "side_image": side_image_b64,
    "ref_obj_pos": "left",
    "ref_obj_width_real": 8.56,
    "polygons_front_image": polygon1,
    "polygons_side_image": polygon2
}

try:
    # Send POST request
    response = requests.post(API_URL, json=payload)

    # Check response status
    if response.status_code == 200:
        result = response.json()
        if "error" in result:
            print(f"❌ API Error: {result['error']}")
        else:
            print("✅ Measurement Successful!")
            print(f"Width: {result['width']} cm")
            print(f"Height: {result['height']} cm")
            print(f"Depth: {result['depth']} cm")

            # Display annotated images
            decode_and_display_image(
                result["front_annotated_image"], "Front View (Annotated)")
            decode_and_display_image(
                result["side_annotated_image"], "Side View (Annotated)")

    else:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
