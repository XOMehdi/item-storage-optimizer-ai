import random
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import time


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


class Item:
    def __init__(self, id, w, h, d):
        self.id = id
        # Use only unique orientations
        self.orientations = list(set([(w, h, d), (w, d, h), (h, w, d),
                                      (h, d, w), (d, w, h), (d, h, w)]))
        self.volume = w * h * d  # Pre-calculate volume for sorting


def initialize_population(size, items):
    """Generate an initial population of random solutions with smarter initialization."""
    population = []

    # Sort items by volume for better initial packing (largest first)
    sorted_items = sorted(items, key=lambda item: item.volume, reverse=True)

    for _ in range(size):
        # Create different permutations - some ordered by size, some random
        if random.random() < 0.3:  # 30% completely random
            random.shuffle(items)
            item_list = items
        elif random.random() < 0.7:  # 40% sorted by volume
            item_list = sorted_items.copy()
        else:  # 30% slightly shuffled sorted
            item_list = sorted_items.copy()
            # Swap a few items to introduce variety
            for _ in range(len(item_list) // 3):
                i, j = random.sample(range(len(item_list)), 2)
                item_list[i], item_list[j] = item_list[j], item_list[i]

        orientations = [random.choice(item.orientations) for item in item_list]
        population.append(list(zip(item_list, orientations)))

    return population


def fitness(container, arrangement):
    """Evaluate the fitness of a packing arrangement with early stopping."""
    # We'll reuse a container object instead of deep copying each time
    temp_container = Container(container.w, container.h, container.d)
    total_volume = container.w * container.h * container.d
    total_items_volume = sum(item.volume for item, _ in arrangement)

    # If total items volume is too large, fail early
    if total_items_volume > total_volume:
        return 0, []

    placements = []

    for item, (w, h, d) in arrangement:
        placed = False

        # Try to place the item at lowest coordinates first (bottom-left-front strategy)
        # This is a common heuristic in bin packing
        candidates = []

        # First try corners and edges where items are already placed
        # Start with (0,0,0) as the first candidate
        candidates.append((0, 0, 0))

        # Add positions that are adjacent to already placed items
        for _, px, py, pz, pw, ph, pd in placements:
            # Add positions adjacent to placed items (6 surfaces)
            candidates.extend([
                (px + pw, py, pz),  # Right surface
                (px, py + ph, pz),  # Back surface
                (px, py, pz + pd),  # Top surface
            ])

        # Remove duplicates and out-of-bounds positions
        candidates = [(x, y, z) for x, y, z in candidates if
                      x < container.w - w + 1 and
                      y < container.h - h + 1 and
                      z < container.d - d + 1]

        # Try candidate positions first (much fewer than all positions)
        for x, y, z in candidates:
            if temp_container.fits(x, y, z, w, h, d):
                temp_container.place_item(item, x, y, z, w, h, d)
                placements.append((item.id, x, y, z, w, h, d))
                placed = True
                break

        # If no candidate positions work, try a subset of all positions
        if not placed:
            # Sample a subset of positions for efficiency
            step = max(1, min(container.w, container.h, container.d) // 4)
            for x in range(0, container.w - w + 1, step):
                for y in range(0, container.h - h + 1, step):
                    for z in range(0, container.d - d + 1, step):
                        if temp_container.fits(x, y, z, w, h, d):
                            temp_container.place_item(item, x, y, z, w, h, d)
                            placements.append((item.id, x, y, z, w, h, d))
                            placed = True
                            break
                    if placed:
                        break
                if placed:
                    break

            # If step sampling didn't work, try all positions
            if not placed and step > 1:
                for x in range(0, container.w - w + 1):
                    for y in range(0, container.h - h + 1):
                        for z in range(0, container.d - d + 1):
                            if temp_container.fits(x, y, z, w, h, d):
                                temp_container.place_item(
                                    item, x, y, z, w, h, d)
                                placements.append((item.id, x, y, z, w, h, d))
                                placed = True
                                break
                        if placed:
                            break
                    if placed:
                        break

        # If still not placed, return failure - ALL items must be placed
        if not placed:
            return 0, []  # Zero fitness if ANY item can't be placed

    # Only calculate actual utilization if ALL items were successfully placed
    utilization = temp_container.get_utilization()
    return utilization, placements


def tournament_selection(evaluated_population, tournament_size=3):
    """Select parents using tournament selection."""
    selected = []
    for _ in range(2):
        tournament = random.sample(evaluated_population, tournament_size)
        winner = max(tournament, key=lambda x: x[0][0])
        selected.append(winner[1])
    return selected


def crossover(parent1, parent2):
    """Perform order-based crossover between two parents."""
    # Choose a random segment to preserve from parent1
    start = random.randint(0, len(parent1) - 1)
    end = random.randint(start + 1, len(parent1))

    # Create a mapping of items from parent2 to their indices
    parent2_items = {item[0].id: i for i, item in enumerate(parent2)}

    # Create child with segment from parent1
    child_segment = parent1[start:end]

    # Fill the rest of the child with items from parent2 in their original order
    remaining_items = [item for item in parent2 if item[0]
                       not in [seg[0] for seg in child_segment]]

    child = remaining_items[:start] + child_segment + remaining_items[start:]

    return child


def mutate(arrangement):
    """Apply multiple types of mutations."""
    if random.random() < 0.3:  # Swap mutation
        i, j = random.sample(range(len(arrangement)), 2)
        arrangement[i], arrangement[j] = arrangement[j], arrangement[i]

    if random.random() < 0.3:  # Orientation mutation
        i = random.randint(0, len(arrangement) - 1)
        item, _ = arrangement[i]
        arrangement[i] = (item, random.choice(item.orientations))

    if random.random() < 0.2:  # Rotation mutation - rotate a random segment
        if len(arrangement) > 3:
            start = random.randint(0, len(arrangement) - 3)
            end = random.randint(start + 2, min(len(arrangement), start + 5))
            segment = arrangement[start:end]
            segment.reverse()
            arrangement[start:end] = segment

    return arrangement


def genetic_algorithm(container, items, population_size=100, generations=200):
    """Run the genetic algorithm with early stopping and adaptive parameters."""
    start_time = time.time()

    population = initialize_population(population_size, items)
    best_solution = None
    best_utilization = 0
    best_placements = []

    # Track progress to detect stagnation
    stagnation_counter = 0
    last_best = 0

    # Store all results for statistical analysis
    all_results = []

    for gen in range(generations):
        # Evaluate population in parallel if possible
        evaluated_population = []
        for individual in population:
            fitness_value, placement = fitness(container, individual)
            evaluated_population.append(
                ((fitness_value, placement), individual))

            # Store results
            all_results.append(fitness_value)

            # Update best solution
            if fitness_value > best_utilization:
                best_utilization = fitness_value
                best_solution = individual
                best_placements = placement
                stagnation_counter = 0
                print(
                    f"Generation {gen}: New best utilization: {best_utilization:.2f}%")

        # Sort by fitness
        evaluated_population.sort(reverse=True, key=lambda x: x[0][0])

        # Check if we found a perfect solution
        if best_utilization > 99.9:
            print(f"Perfect solution found at generation {gen}")
            break

        # Early stopping if no improvement
        if abs(last_best - best_utilization) < 0.1:
            stagnation_counter += 1
        else:
            stagnation_counter = 0
            last_best = best_utilization

        if stagnation_counter >= 10:
            print(f"Stopping early at generation {gen} due to stagnation")
            break

        # Elitism - keep top solutions
        elite_count = max(1, population_size // 10)
        new_population = [individual for _,
                          individual in evaluated_population[:elite_count]]

        # Create new population
        while len(new_population) < population_size:
            # Tournament selection
            parent1, parent2 = tournament_selection(
                evaluated_population, tournament_size=3)

            # Crossover
            if random.random() < 0.7:  # 70% chance of crossover
                child = crossover(parent1, parent2)
            else:
                child = random.choice([parent1, parent2])

            # Mutation (adaptive rate)
            # Increase mutation as stagnation increases
            mutation_rate = 0.2 + (stagnation_counter / 20)
            if random.random() < mutation_rate:
                child = mutate(child)

            new_population.append(child)

        population = new_population

        # Optionally print progress
        if gen % 5 == 0:
            elapsed = time.time() - start_time
            print(
                f"Generation {gen}, Best: {best_utilization:.2f}%, Time: {elapsed:.2f}s")

    # Calculate final statistics
    print("\nOptimization completed:")
    print(f"Best utilization: {best_utilization:.2f}%")
    print(f"Time taken: {time.time() - start_time:.2f} seconds")

    if best_utilization > 0:
        return {"status": "success", "placements": best_placements, "space_utilization": round(best_utilization, 2)}
    else:
        return {"status": "reduce_items", "message": "No valid packing found."}


def visualize_packing(container, placements):
    """Visualize the packed container using Matplotlib 3D"""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlim([0, container.w])
    ax.set_ylim([0, container.h])
    ax.set_zlim([0, container.d])

    # Set labels
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')
    ax.set_zlabel('Depth')
    ax.set_title('3D Bin Packing Visualization')

    # More diverse color palette
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33',
              '#a65628', '#f781bf', '#999999', '#66c2a5', '#fc8d62', '#8da0cb']

    for i, (item_id, x, y, z, w, h, d) in enumerate(placements):
        # Use item_id for consistent colors
        color = colors[item_id % len(colors)]

        vertices = [
            [x, y, z], [x + w, y, z], [x + w, y + h, z], [x, y + h, z],
            [x, y, z + d], [x + w, y, z + d], [x +
                                               w, y + h, z + d], [x, y + h, z + d]
        ]

        faces = [
            [vertices[j] for j in [0, 1, 2, 3]],  # bottom
            [vertices[j] for j in [4, 5, 6, 7]],  # top
            [vertices[j] for j in [0, 1, 5, 4]],  # front
            [vertices[j] for j in [2, 3, 7, 6]],  # back
            [vertices[j] for j in [1, 2, 6, 5]],  # right
            [vertices[j] for j in [0, 3, 7, 4]]   # left
        ]

        # Create 3D polygons
        poly = Poly3DCollection(faces, facecolors=color,
                                linewidths=1, edgecolors='k', alpha=0.7)
        ax.add_collection3d(poly)

        # Optionally add item labels at the center of each item
        center_x, center_y, center_z = x + w/2, y + h/2, z + d/2
        ax.text(center_x, center_y, center_z, str(item_id),
                color='black', fontsize=9, ha='center')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Example usage with timing
    start_time = time.time()

    real_measurements_cm = {
        # Item: Width, Height, Depth
        "Card": [9, 6, 0.1],  # Added missing depth
        "Laptop": [33, 22, 2],
        "Matchbox": [6, 6, 2],
        "Mouse": [12, 6, 3],
        "Phone": [16, 8, 1],
        "USB": [4, 2, 1],
        "Tissue Box": [24, 12, 9],
        "Mini Bucket": [16, 16, 15],
        "Milkpack": [9, 25, 7],
        "2 Coin": [2, 2, 0.2],  # Added missing depth
        "1 Coin": [1.8, 1.8, 0.2],  # Added missing depth
        "5 Coin": [1.6, 1.6, 0.2],  # Added missing depth
    }

    container = Container(30, 20, 10)

    laptop = Item(0, *real_measurements_cm["Laptop"])
    matchbox = Item(1, *real_measurements_cm["Matchbox"])
    phone = Item(2, *real_measurements_cm["Phone"])
    usb = Item(3, *real_measurements_cm["USB"])
    tissue_box = Item(4, *real_measurements_cm["Tissue Box"])
    mini_bucket = Item(5, *real_measurements_cm["Mini Bucket"])
    milkpack = Item(6, *real_measurements_cm["Milkpack"])

    items = [matchbox, usb, laptop, phone, phone,
             tissue_box, milkpack, laptop, mini_bucket, matchbox]

    items = [matchbox, usb, usb, usb, matchbox, matchbox, matchbox, matchbox,
             matchbox, phone, phone, phone, phone, phone, phone, tissue_box, milkpack]

    print(f"Starting optimization with {len(items)} items...")
    result = genetic_algorithm(container, items)

    if result["status"] == "success":
        print("\nBest Packing Solution:")
        print("Space Utilization:", result["space_utilization"], "%")
        visualize_packing(container, result["placements"])
    else:
        print(result["message"])

    print(f"\nTotal execution time: {time.time() - start_time:.2f} seconds")
