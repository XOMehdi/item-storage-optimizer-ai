import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class Container:
    def __init__(self, w, h, d):
        self.w, self.h, self.d = w, h, d
        self.placements = []  # Store placed item positions
        self.space = np.zeros((w, h, d), dtype=int)  # 3D grid

    def fits(self, x, y, z, w, h, d):
        """Check if an item fits at (x, y, z)"""
        if x + w > self.w or y + h > self.h or z + d > self.d:
            return False
        return np.all(self.space[x:x+w, y:y+h, z:z+d] == 0)

    def place_item(self, item, x, y, z, w, h, d):
        """Place an item and update space"""
        self.space[x:x+w, y:y+h, z:z+d] = 1
        self.placements.append((item.id, x, y, z, w, h, d))

    def get_utilization(self):
        total_volume = self.w * self.h * self.d
        used_volume = np.sum(self.space)
        return (used_volume / total_volume) * 100


class Item:
    def __init__(self, id, w, h, d):
        self.id = id
        self.orientations = [(w, h, d), (w, d, h), (h, w, d),
                             (h, d, w), (d, w, h), (d, h, w)]  # 90-degree rotations


def initialize_population(size, items):
    """Generate an initial population of random solutions."""
    population = []
    for _ in range(size):
        random.shuffle(items)
        orientations = [random.choice(item.orientations) for item in items]
        population.append(list(zip(items, orientations)))
    return population


def fitness(container, arrangement):
    """Evaluate the fitness of a packing arrangement."""
    temp_container = Container(container.w, container.h, container.d)
    success = True

    for item, (w, h, d) in arrangement:
        placed = False
        for x in range(container.w - w + 1):
            for y in range(container.h - h + 1):
                for z in range(container.d - d + 1):
                    if temp_container.fits(x, y, z, w, h, d):
                        temp_container.place_item(item, x, y, z, w, h, d)
                        placed = True
                        break
                if placed:
                    break
            if placed:
                break
        if not placed:
            success = False
            break

    return temp_container.get_utilization() if success else 0


def crossover(parent1, parent2):
    """Perform crossover between two parents."""
    split = len(parent1) // 2
    child = parent1[:split] + parent2[split:]
    return child


def mutate(arrangement):
    """Apply mutation by swapping two items or changing an orientation."""
    if random.random() < 0.2:  # 20% mutation rate
        i, j = random.sample(range(len(arrangement)), 2)
        arrangement[i], arrangement[j] = arrangement[j], arrangement[i]
    if random.random() < 0.2:
        i = random.randint(0, len(arrangement) - 1)
        arrangement[i] = (arrangement[i][0], random.choice(
            arrangement[i][0].orientations))
    return arrangement


def genetic_algorithm(container, items, population_size=50, generations=100, early_stop=10):
    """Run the genetic algorithm with optimized performance."""
    population = initialize_population(population_size, items)
    best_solution = None
    best_utilization = 0
    stagnant_generations = 0

    for _ in range(generations):
        population = sorted(population, key=lambda x: fitness(
            container, x), reverse=True)
        new_population = population[:10]  # Keep top 10

        while len(new_population) < population_size:
            parent1, parent2 = random.sample(population[:20], 2)
            child = crossover(parent1, parent2)
            child = mutate(child)
            new_population.append(child)

        population = new_population

        current_best = fitness(container, population[0])
        if current_best > best_utilization:
            best_solution = population[0]
            best_utilization = current_best
            stagnant_generations = 0
        else:
            stagnant_generations += 1
            if stagnant_generations >= early_stop:
                break  # Stop early if no improvement

    if best_utilization > 0:
        return {"status": "success", "placements": best_solution, "space_utilization": round(best_utilization, 2)}
    else:
        return {"status": "reduce_items", "message": "No valid packing found."}


def visualize_packing(container, placements):
    """Visualize the packed container using Matplotlib 3D"""
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlim([0, container.w])
    ax.set_ylim([0, container.h])
    ax.set_zlim([0, container.d])

    colors = ['r', 'g', 'b', 'y', 'c', 'm']

    for i, (item, x, y, z, w, h, d) in enumerate(placements):
        color = colors[i % len(colors)]

        vertices = [
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x + w, y + h, z + d], [x, y + h, z + d]
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

container = Container(25, 25, 25)

laptop = Item(0, *real_measurements_cm["Laptop"])
matchbox = Item(1, *real_measurements_cm["Matchbox"])
phone = Item(2, *real_measurements_cm["Phone"])
usb = Item(3, *real_measurements_cm["USB"])
tissue_box = Item(4, *real_measurements_cm["Tissue Box"])
mini_bucket = Item(5, *real_measurements_cm["Mini Bucket"])
milkpack = Item(6, *real_measurements_cm["Milkpack"])

items = [matchbox, usb, laptop, phone, phone, phone,
         tissue_box, tissue_box, milkpack, laptop, mini_bucket]
result = genetic_algorithm(container, items)

if result["status"] == "success":
    print("Best Packing Solution:")
    print("Space Utilization:", result["space_utilization"], "%")
    visualize_packing(container, result["placements"])
