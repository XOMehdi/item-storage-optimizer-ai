import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Item:
    def __init__(self, id, width, height, depth):
        self.id = id  # Unique identifier
        self.orientations = [
            (width, height, depth),
            (width, depth, height),
            (height, width, depth),
            (height, depth, width),
            (depth, width, height),
            (depth, height, width)
        ]  # All 90° rotations


class Container:
    def __init__(self, width, height, depth):
        self.w, self.h, self.d = width, height, depth
        self.placements = []  # Stores (id, x, y, z, w, h, d)

    def fits(self, x, y, z, w, h, d):
        """Check if an item fits inside the container without overlap"""
        if x + w > self.w or y + h > self.h or z + d > self.d:
            return False  # Out of bounds

        for placed in self.placements:
            _, px, py, pz, pw, ph, pd = placed
            if (x < px + pw and x + w > px and
                y < py + ph and y + h > py and
                    z < pz + pd and z + d > pz):
                return False  # Overlaps with an existing item
        return True

    def place_item(self, item):
        """Try placing an item at the best available spot with all rotations"""
        best_fit = None

        for (w, h, d) in item.orientations:
            for x in range(self.w - w + 1):
                for y in range(self.h - h + 1):
                    for z in range(self.d - d + 1):
                        if self.fits(x, y, z, w, h, d):
                            empty_space = (self.w * self.h *
                                           self.d) - (w * h * d)
                            if best_fit is None or empty_space < best_fit[0]:
                                best_fit = (empty_space, x, y, z, w, h, d)

        if best_fit:
            _, x, y, z, w, h, d = best_fit
            self.placements.append((item.id, x, y, z, w, h, d))
            return True
        return False  # No valid placement found


def pack_items(container, items):
    """Try placing items using greedy heuristic with rotation"""
    items = sorted(items, key=lambda item: max(item.orientations, key=lambda o: o[0] * o[1] * o[2])[0] *
                   max(item.orientations, key=lambda o: o[0] * o[1] * o[2])[1] *
                   max(item.orientations, key=lambda o: o[0] * o[1] * o[2])[2], reverse=True)

    for item in items:
        if not container.place_item(item):
            return {"status": "reduce_items", "message": "Optimal layout not possible"}

    return {"status": "success", "container_size": [container.w, container.h, container.d], "placements": container.placements}


def plot_container(container):
    """Visualize the container with placed items"""
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlim([0, container.w])
    ax.set_ylim([0, container.h])
    ax.set_zlim([0, container.d])

    colors = plt.cm.get_cmap("tab10", len(
        container.placements))  # Generate colors

    for i, (item_id, x, y, z, w, h, d) in enumerate(container.placements):
        color = colors(i)[:3]  # Extract RGB
        draw_box(ax, x, y, z, w, h, d, color, label=f"Item {item_id}")

    ax.set_xlabel('Width')
    ax.set_ylabel('Height')
    ax.set_zlabel('Depth')
    ax.set_title('3D Container Packing Visualization')

    plt.show()


def draw_box(ax, x, y, z, w, h, d, color, label=""):
    """Draw a 3D box for an item"""
    vertices = np.array([
        [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],  # Bottom
        [x, y, z + d], [x + w, y, z + d], [x + w,
                                           y + h, z + d], [x, y + h, z + d]  # Top
    ])

    faces = [
        [vertices[j] for j in [0, 1, 2, 3]],  # Bottom
        [vertices[j] for j in [4, 5, 6, 7]],  # Top
        [vertices[j] for j in [0, 1, 5, 4]],  # Side 1
        [vertices[j] for j in [2, 3, 7, 6]],  # Side 2
        [vertices[j] for j in [0, 3, 7, 4]],  # Side 3
        [vertices[j] for j in [1, 2, 6, 5]]   # Side 4
    ]

    poly = Poly3DCollection(faces, alpha=0.5, edgecolor='k', facecolor=color)
    ax.add_collection3d(poly)

    # Label the center of the box
    cx, cy, cz = x + w / 2, y + h / 2, z + d / 2
    ax.text(cx, cy, cz, label, color='black',
            fontsize=10, ha='center', va='center')


# Example Usage
real_measurements_cm = {
    # Item: Width, Height, Depth
    "Card": [9, 6],
    "Laptop": [33, 22, 2],
    "Matchbox": [6, 6, 2],
    "Mouse": [12, 6, 3],
    "Phone": [16, 8, 1],
    "USB": [4, 2, 1],
    "Tissue Box": [24, 12, 9],
    "Mini Bucket": [16, 16, 15],
    "Milkpack": [9, 25, 7],
    "2 Coin": [2, 2],
    "1 Coin": [1.8, 1.8],
    "5 Coin": [1.6, 1.6],
}


container = Container(30, 38, 30)

laptop = Item(0, *real_measurements_cm["Laptop"])
matchbox = Item(1, *real_measurements_cm["Matchbox"])
phone = Item(2, *real_measurements_cm["Phone"])
usb = Item(3, *real_measurements_cm["USB"])
tissue_box = Item(4, *real_measurements_cm["Tissue Box"])
mini_bucket = Item(5, *real_measurements_cm["Mini Bucket"])
milkpack = Item(6, *real_measurements_cm["Milkpack"])

items = [matchbox, usb, laptop, phone, tissue_box]
random.shuffle(items)

# items = [Item(i, np.random.randint(2, 5), np.random.randint(
#     2, 5), np.random.randint(2, 5)) for i in range(5)]


result = pack_items(container, items)

if result["status"] == "success":
    plot_container(container)
else:
    print(result["message"])
