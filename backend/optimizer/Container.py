import numpy as np


class Container:
    def __init__(self, w, h, d):
        self.w, self.h, self.d = w, h, d
        self.placements = []  # Store placed item positions
        # Using numpy array instead of nested lists for better performance
        self.space = np.zeros((w, h, d), dtype=np.int8)

    def fits(self, x, y, z, w, h, d):
        """Check if an item fits at (x, y, z) using array slicing"""
        # Check boundaries
        if x + w > self.w or y + h > self.h or z + d > self.d:
            return False

        # Check if space is already occupied using numpy's any() - much faster than nested loops
        return not np.any(self.space[x:x+w, y:y+h, z:z+d])

    def place_item(self, item, x, y, z, w, h, d):
        """Place an item and update space using array slicing"""
        self.space[x:x+w, y:y+h, z:z+d] = 1
        self.placements.append((item.id, x, y, z, w, h, d))

    def get_utilization(self):
        total_volume = self.w * self.h * self.d
        used_volume = np.sum(self.space)
        return (used_volume / total_volume) * 100
