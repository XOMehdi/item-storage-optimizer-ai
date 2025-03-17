import cv2 as cv
import numpy as np


class ManualContourSelector:
    """Handles manual selection of contours by user interaction."""

    def __init__(self):
        self.manual_polygons = []
        self.current_polygon = []
        self.polygon_complete = False

    def draw_polygon(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            # Add a new point to the current polygon
            self.current_polygon.append((x, y))

        elif event == cv.EVENT_RBUTTONDOWN and len(self.current_polygon) >= 3:
            # Close the current polygon if it has at least 3 points
            self.manual_polygons.append(
                np.array(self.current_polygon, dtype=np.int32))
            self.current_polygon = []  # Reset for the next polygon
            # Stop when two polygons are drawn
            self.polygon_complete = len(self.manual_polygons) >= 2

    def get_manual_contours(self, image):
        self.manual_polygons = []
        self.current_polygon = []
        self.polygon_complete = False
        clone = image.copy()

        window_name = "Draw Polygons (Left-click: Add Point, Right-click: Close Polygon, 'Z' to Undo)"
        cv.namedWindow(window_name)
        cv.setMouseCallback(window_name, self.draw_polygon)

        while True:
            temp = clone.copy()

            # Draw all completed polygons
            for poly in self.manual_polygons:
                cv.polylines(temp, [poly], isClosed=True,
                             color=(0, 255, 0), thickness=2)

            # Draw the current polygon
            if len(self.current_polygon) > 1:
                cv.polylines(temp, [np.array(self.current_polygon, dtype=np.int32)],
                             isClosed=False, color=(0, 255, 255), thickness=2)

            cv.imshow(window_name, temp)

            key = cv.waitKey(1) & 0xFF

            if key == ord('z'):  # Undo feature
                if self.current_polygon:
                    self.current_polygon.pop()  # Remove last point if still drawing
                elif self.manual_polygons:
                    self.manual_polygons.pop()  # Remove last completed polygon

            if self.polygon_complete:
                break

        cv.destroyAllWindows()

        return self.manual_polygons[:2]  # Return the first two closed polygons
