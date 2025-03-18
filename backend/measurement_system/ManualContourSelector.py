import cv2 as cv
import numpy as np

class ManualContourSelector:
    """Handles manual selection of contours from Flutter app."""

    def __init__(self):
        self.manual_polygons = []

    def set_polygons_from_flutter(self, polygons):
        """
        Set polygons from Flutter app data.
        
        Args:
            polygons: List of polygons, where each polygon is a list of points [x, y]
        """
        self.manual_polygons = []
        for polygon in polygons:
            points = np.array(polygon, dtype=np.int32)
            self.manual_polygons.append(points)
        
        return self.manual_polygons