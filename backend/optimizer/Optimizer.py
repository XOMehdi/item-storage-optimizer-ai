import random
import time
from Container import *
from Item import *


class Optimizer:
    def __init__(self, container_data, items_data):
        # Convert to Container and Item objects
        w, h, d = container_data["width"], container_data["height"], container_data["depth"]
        self.container = Container(w, h, d)

        self.items = []
        for item_data in items_data:
            item_id = item_data.get("id")
            w, h, d = item_data["dimensions"]["width"], item_data["dimensions"]["height"], item_data["dimensions"]["depth"]

            self.items.append(Item(item_id, w, h, d))
        
    def initialize_population(self, size, items):
        """Generate an initial population of random solutions with smarter initialization."""
        population = []

        # Sort items by volume for better initial packing (largest first)
        sorted_items = sorted(
            items, key=lambda item: item.volume, reverse=True)

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

            orientations = [random.choice(item.orientations)
                            for item in item_list]
            population.append(list(zip(item_list, orientations)))

        return population

    def fitness(self, container, arrangement):
        """Evaluate the fitness of a packing arrangement with early stopping."""

        all_placed = False
        temp_container = Container(container.w, container.h, container.d)
        total_volume = container.w * container.h * container.d
        total_items_volume = sum(item.volume for item, _ in arrangement)

        # If total items volume is too large, fail early
        if total_items_volume > total_volume:
            return 0, [], all_placed

        placements = []
        total_placed_volume = 0

        for item, (w, h, d) in arrangement:
            placed = False

            # Try to place the item at lowest coordinates first (bottom-left-front strategy)
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
                    total_placed_volume += item.volume
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
                                total_placed_volume += item.volume
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
                                    temp_container.place_item(item, x, y, z, w, h, d)
                                    placements.append((item.id, x, y, z, w, h, d))
                                    placed = True
                                    total_placed_volume += item.volume
                                    break
                            if placed:
                                break
                        if placed:
                            break

            # If still not placed, return failure
            if not placed:
                utilization = (total_placed_volume / total_volume) * 100
                return utilization, placements, all_placed

        all_placed = True
        utilization = (total_placed_volume / total_volume) * 100
        return utilization, placements, all_placed


    def tournament_selection(self, evaluated_population, tournament_size=3):
        """Select parents using tournament selection."""
        selected = []
        for _ in range(2):
            tournament = random.sample(evaluated_population, tournament_size)
            winner = max(tournament, key=lambda x: x[0][0])
            selected.append(winner[1])
        return selected

    def crossover(self, parent1, parent2):
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

        child = remaining_items[:start] + \
            child_segment + remaining_items[start:]

        return child

    def mutate(self, arrangement):
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
                end = random.randint(
                    start + 2, min(len(arrangement), start + 5))
                segment = arrangement[start:end]
                segment.reverse()
                arrangement[start:end] = segment

        return arrangement

    def genetic_algorithm(self, population_size, generations):
        """Run the genetic algorithm with early stopping and adaptive parameters."""
        start_time = time.time()

        population = self.initialize_population(population_size, self.items)
        best_solution = None
        best_utilization = 0
        best_placements = []
        best_all_placed = False

        # Track progress to detect stagnation
        stagnation_counter = 0
        last_best = 0

        # Store all results for statistical analysis
        all_results = []

        for gen in range(generations):
            # Evaluate population in parallel if possible
            evaluated_population = []
            for individual in population:
                fitness_value, placement, all_placed = self.fitness(
                    self.container, individual)
                evaluated_population.append(
                    ((fitness_value, placement, all_placed), individual))

                # Store results
                all_results.append(fitness_value)

                # Update best solution
                if fitness_value > best_utilization:
                    best_all_placed = True if all_placed else False
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
                parent1, parent2 = self.tournament_selection(
                    evaluated_population, tournament_size=3)

                # Crossover
                if random.random() < 0.7:  # 70% chance of crossover
                    child = self.crossover(parent1, parent2)
                else:
                    child = random.choice([parent1, parent2])

                # Mutation (adaptive rate)
                # Increase mutation as stagnation increases
                mutation_rate = 0.2 + (stagnation_counter / 20)
                if random.random() < mutation_rate:
                    child = self.mutate(child)

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

        if best_solution and best_all_placed:
            return {
                "status": "success",
                "placements": best_placements,
                "space_utilization": round(best_utilization, 2)
            }
        else:
            return {
                "status": "failure",
                "placements": best_placements,
                "space_utilization": round(best_utilization, 2),
                "message": "Not all items could be placed."
            }
