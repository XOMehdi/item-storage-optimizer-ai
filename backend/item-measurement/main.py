# # Create a window
# cv.namedWindow('Canny Edge Detection')

# # Create trackbars for threshold adjustment
# cv.createTrackbar('Lower Threshold', 'Canny Edge Detection',
#                    10, 255, lambda v: v)
# cv.createTrackbar('Upper Threshold',
#                    'Canny Edge Detection', 20, 255, lambda v: v)

# while True:
#     # Get current positions of trackbars
#     lower_thresh = cv.getTrackbarPos(
#         'Lower Threshold', 'Canny Edge Detection')
#     upper_thresh = cv.getTrackbarPos(
#         'Upper Threshold', 'Canny Edge Detection')

#     edged = cv.Canny(gray, lower_thresh, upper_thresh)
#     edged = cv.dilate(edged, None, iterations=1)
#     edged = cv.erode(edged, None, iterations=1)

#     cv.imshow('Canny Edge Detection', resize(edged))

#     # Break the loop when 'q' is pressed
#     if cv.waitKey(1) & 0xFF == ord('q'):
#         break


import cv2 as cv
import numpy as np
from imutils import perspective
from imutils import contours
import imutils
from scipy.spatial import distance as dist
import argparse
import os


def midpoint(ptA, ptB):
    return ((ptA[0] + ptB[0]) * 0.5, (ptA[1] + ptB[1]) * 0.5)


def resize(img):
    width = img.shape[1]
    height = img.shape[0]
    ratio = width / height
    if width > 1600 or height > 900:
        width = 1600
        height = int(width / ratio)
        img = cv.resize(img, (width, height))
    return img


# Construct argument parser
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="Path to the input image")
ap.add_argument("-w", "--width", type=float, required=True,
                help="Width of the left-most object in the image (in inches)")
args = vars(ap.parse_args())

# Input validation
if not os.path.exists(args["image"]):
    raise FileNotFoundError(f"Image path '{args['image']}' does not exist.")

if args["width"] <= 0:
    raise ValueError("Width must be a positive value.")

# Load and preprocess the image
image = cv.imread(args["image"])
gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
gray = cv.GaussianBlur(gray, (7, 7), 0)
edged = cv.Canny(gray, 0, 138)
edged = cv.dilate(edged, None, iterations=1)
edged = cv.erode(edged, None, iterations=1)

# Find and sort contours
contours = cv.findContours(
    edged.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)

# Using imutils.countours
# (contours, _) = contours.sort_contours(contours)
contours = sorted(contours, key=lambda c: cv.boundingRect(c)[0])


pixels_per_metric = None

# Process each contour
for contour in contours:
    if cv.contourArea(contour) < 100:
        continue

    # Rotated bounding box
    img_copy = image.copy()
    box = cv.minAreaRect(contour)
    box = cv.boxPoints(box)
    box = np.array(box, dtype="int")

    # Using imutils.perspective
    box = perspective.order_points(box)
    cv.drawContours(img_copy, [box.astype("int")], -1, (0, 255, 0), 2)

    # Draw midpoints and lines
    (tl, tr, br, bl) = box
    (tltrX, tltrY) = midpoint(tl, tr)
    (blbrX, blbrY) = midpoint(bl, br)
    (tlblX, tlblY) = midpoint(tl, bl)
    (trbrX, trbrY) = midpoint(tr, br)

    cv.circle(img_copy, (int(tltrX), int(tltrY)), 5, (255, 0, 0), -1)
    cv.circle(img_copy, (int(blbrX), int(blbrY)), 5, (255, 0, 0), -1)
    cv.circle(img_copy, (int(tlblX), int(tlblY)), 5, (255, 0, 0), -1)
    cv.circle(img_copy, (int(trbrX), int(trbrY)), 5, (255, 0, 0), -1)
    cv.line(img_copy, (int(tltrX), int(tltrY)),
            (int(blbrX), int(blbrY)), (255, 0, 255), 2)
    cv.line(img_copy, (int(tlblX), int(tlblY)),
            (int(trbrX), int(trbrY)), (255, 0, 255), 2)

    # Compute distances and dimensions
    dA = dist.euclidean((tltrX, tltrY), (blbrX, blbrY))
    dB = dist.euclidean((tlblX, tlblY), (trbrX, trbrY))

    if pixels_per_metric is None:
        pixels_per_metric = dB / args["width"]

    dimA = dA / pixels_per_metric
    dimB = dB / pixels_per_metric

    cv.putText(img_copy, "{:.1f}in".format(dimA),
               (int(tltrX - 15), int(tltrY - 10)), cv.FONT_HERSHEY_SIMPLEX,
               0.65, (255, 255, 255), 2)
    cv.putText(img_copy, "{:.1f}in".format(dimB),
               (int(trbrX + 10), int(trbrY)), cv.FONT_HERSHEY_SIMPLEX,
               0.65, (255, 255, 255), 2)

    # Show output
    cv.imshow("Image", resize(img_copy))
    cv.waitKey(0)

cv.destroyAllWindows()
