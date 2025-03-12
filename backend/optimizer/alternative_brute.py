from itertools import permutations, product
import copy
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Container:
    def __init__(self, w, h, d):
        self.w, self.h, self.d = w, h, d
        self.placements = []  # Store placed item positions
        self.space = [[[0] * d for _ in range(h)] for _ in range(w)]  # 3D grid

    def fits(self, x, y, z, w, h, d):
        """Check if an item fits at (x, y, z)"""
        if x + w > self.w or y + h > self.h or z + d > self.d:
            return False
        for i in range(x, x + w):
            for j in range(y, y + h):
                for k in range(z, z + d):
                    if self.space[i][j][k] == 1:
                        return False  # Space already occupied
        return True

    def place_item(self, item, x, y, z, w, h, d):
        """Place an item and update space"""
        for i in range(x, x + w):
            for j in range(y, y + h):
                for k in range(z, z + d):
                    self.space[i][j][k] = 1
        self.placements.append((item.id, x, y, z, w, h, d))

    def get_utilization(self):
        total_volume = self.w * self.h * self.d
        used_volume = sum(sum(sum(row) for row in layer)
                          for layer in self.space)
        return (used_volume / total_volume) * 100


class Item:
    def __init__(self, id, w, h, d):
        self.id = id
        self.orientations = [(w, h, d), (w, d, h), (h, w, d),
                             (h, d, w), (d, w, h), (d, h, w)]


def brute_force_packing(container, items):
    """Try all item permutations and orientations to find the best packing"""
    best_solution = None
    best_utilization = 0

    for item_order in permutations(items):
        for orientations in product(*[item.orientations for item in item_order]):
            temp_container = copy.deepcopy(container)  # Reset container
            success = True

            for item, (w, h, d) in zip(item_order, orientations):
                placed = False
                for x in range(container.w - w + 1):
                    for y in range(container.h - h + 1):
                        for z in range(container.d - d + 1):
                            if temp_container.fits(x, y, z, w, h, d):
                                temp_container.place_item(
                                    item, x, y, z, w, h, d)
                                placed = True
                                break
                        if placed:
                            break
                    if placed:
                        break
                if not placed:
                    success = False
                    break

            if success:
                utilization = temp_container.get_utilization()
                if utilization > best_utilization:
                    best_utilization = utilization
                    best_solution = temp_container.placements

    if best_solution:
        return {"status": "success", "placements": best_solution, "space_utilization": round(best_utilization, 2)}
    else:
        return {"status": "reduce_items", "message": "No valid packing found."}


def visualize_packing(container, placements):
    """Visualize the packed container using Matplotlib 3D"""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot the container
    ax.set_xlim([0, container.w])
    ax.set_ylim([0, container.h])
    ax.set_zlim([0, container.d])

    colors = ['r', 'g', 'b', 'y', 'c', 'm']

    for i, (item_id, x, y, z, w, h, d) in enumerate(placements):
        color = colors[i % len(colors)]

        vertices = [
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x +
                                               w, y + h, z + d], [x, y + h, z + d]
        ]

        faces = [
            [vertices[j] for j in [0, 1, 2, 3]],
            [vertices[j] for j in [4, 5, 6, 7]],
            [vertices[j] for j in [0, 1, 5, 4]],
            [vertices[j] for j in [2, 3, 7, 6]],
            [vertices[j] for j in [1, 2, 6, 5]],
            [vertices[j] for j in [4, 7, 3, 0]]
        ]

        ax.add_collection3d(Poly3DCollection(
            faces, facecolors=color, linewidths=1, edgecolors='k', alpha=0.5))

    plt.show()


# Example usage
container = Container(8, 8, 8)
items = [Item(i, 4, 4, 4) for i in range(3)]  # Example items


# real_measurements_cm = {
#     # Item: Width, Height, Depth
#     "Card": [9, 6],
#     "Laptop": [33, 22, 2],
#     "Matchbox": [6, 6, 2],
#     "Mouse": [12, 6, 3],
#     "Phone": [16, 8, 1],
#     "USB": [4, 2, 1],
#     "Tissue Box": [24, 12, 9],
#     "Mini Bucket": [16, 16, 15],
#     "Milkpack": [9, 25, 7],
#     "2 Coin": [2, 2],
#     "1 Coin": [1.8, 1.8],
#     "5 Coin": [1.6, 1.6],
# }

# container = Container(30, 38, 30)

# laptop = Item(0, *real_measurements_cm["Laptop"])
# matchbox = Item(1, *real_measurements_cm["Matchbox"])
# phone = Item(2, *real_measurements_cm["Phone"])
# usb = Item(3, *real_measurements_cm["USB"])
# tissue_box = Item(4, *real_measurements_cm["Tissue Box"])
# mini_bucket = Item(5, *real_measurements_cm["Mini Bucket"])
# milkpack = Item(6, *real_measurements_cm["Milkpack"])

# items = [matchbox, usb, laptop, phone, tissue_box]
# random.shuffle(items)

result = brute_force_packing(container, items)

if result["status"] == "success":
    print("Best Packing Solution:")
    print("Space Utilization:", result["space_utilization"], "%")
    visualize_packing(container, result["placements"])
