from flask import Flask, request, jsonify
import numpy as np
import random
import time
import threading
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# Store ongoing and completed optimizations
optimization_tasks = {}


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

        # Check if space is already occupied using numpy's any()
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
    def __init__(self, id, w, h, d, name=None):
        self.id = id
        self.name = name if name else f"Item_{id}"
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


def genetic_algorithm(container, items, task_id, population_size=30, generations=50):
    """Run the genetic algorithm with early stopping and adaptive parameters."""
    start_time = time.time()

    # Update task status
    optimization_tasks[task_id]["status"] = "running"
    optimization_tasks[task_id]["progress"] = 0

    population = initialize_population(population_size, items)
    best_solution = None
    best_utilization = 0
    best_placements = []

    # Track progress to detect stagnation
    stagnation_counter = 0
    last_best = 0

    for gen in range(generations):
        # Update progress
        optimization_tasks[task_id]["progress"] = (gen / generations) * 100

        # Check if the task was cancelled
        if optimization_tasks[task_id]["status"] == "cancelled":
            optimization_tasks[task_id]["end_time"] = datetime.now(
            ).isoformat()
            return {"status": "cancelled", "message": "Optimization was cancelled"}

        # Evaluate population
        evaluated_population = []
        for individual in population:
            fitness_value, placement = fitness(container, individual)
            evaluated_population.append(
                ((fitness_value, placement), individual))

            # Update best solution
            if fitness_value > best_utilization:
                best_utilization = fitness_value
                best_solution = individual
                best_placements = placement
                stagnation_counter = 0

                # Update task with intermediate results
                optimization_tasks[task_id]["intermediate_result"] = {
                    "utilization": round(best_utilization, 2),
                    "placements": format_placements(best_placements, items)
                }

        # Sort by fitness
        evaluated_population.sort(reverse=True, key=lambda x: x[0][0])

        # Check if we found a perfect solution
        if best_utilization > 99.9:
            break

        # Early stopping if no improvement
        if abs(last_best - best_utilization) < 0.1:
            stagnation_counter += 1
        else:
            stagnation_counter = 0
            last_best = best_utilization

        if stagnation_counter >= 10:
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

    # Prepare result
    elapsed_time = time.time() - start_time

    # Update task status
    optimization_tasks[task_id]["progress"] = 100
    optimization_tasks[task_id]["end_time"] = datetime.now().isoformat()
    optimization_tasks[task_id]["execution_time"] = elapsed_time

    if best_utilization > 0:
        result = {
            "status": "success",
            "placements": format_placements(best_placements, items),
            "space_utilization": round(best_utilization, 2),
            "execution_time": elapsed_time
        }
        optimization_tasks[task_id]["status"] = "completed"
        optimization_tasks[task_id]["result"] = result
        return result
    else:
        result = {
            "status": "failed",
            "message": "No valid packing found. Not all items could be placed in the container.",
            "execution_time": elapsed_time
        }
        optimization_tasks[task_id]["status"] = "failed"
        optimization_tasks[task_id]["result"] = result
        return result


def format_placements(placements, items):
    """Format placements to include item details for API response"""
    formatted = []

    # Create a map of item ids to names
    item_map = {item.id: item.name for item in items}

    for placement in placements:
        item_id, x, y, z, w, h, d = placement
        formatted.append({
            "item_id": item_id,
            "item_name": item_map.get(item_id, f"Item_{item_id}"),
            "position": {
                "x": int(x),
                "y": int(y),
                "z": int(z)
            },
            "dimensions": {
                "width": int(w),
                "height": int(h),
                "depth": int(d)
            }
        })

    return formatted


def run_optimization(container_dims, items_data, task_id, config=None):
    """Run the optimization in a separate thread"""
    # Convert to Container and Item objects
    w, h, d = container_dims
    container = Container(w, h, d)

    items = []
    for i, item_data in enumerate(items_data):
        item_id = item_data.get("id", i)
        name = item_data.get("name", f"Item_{item_id}")
        w, h, d = item_data["dimensions"]["width"], item_data["dimensions"]["height"], item_data["dimensions"]["depth"]
        items.append(Item(item_id, w, h, d, name))

    # Set default config if none provided
    if config is None:
        config = {
            "population_size": 30,
            "generations": 50
        }

    # Run genetic algorithm
    result = genetic_algorithm(
        container,
        items,
        task_id,
        population_size=config.get("population_size", 30),
        generations=config.get("generations", 50)
    )

    return result


# API Routes
@app.route('/api/optimize', methods=['POST'])
def optimize():
    """Start a new optimization task"""
    try:
        data = request.json

        # Validate request
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        # Check required fields
        if "container" not in data or "items" not in data:
            return jsonify({"status": "error", "message": "Missing container or items data"}), 400

        # Validate container dimensions
        container = data["container"]
        if "width" not in container or "height" not in container or "depth" not in container:
            return jsonify({"status": "error", "message": "Container dimensions not specified"}), 400

        # Validate items
        items = data["items"]
        if not items or not isinstance(items, list):
            return jsonify({"status": "error", "message": "No items provided or invalid items format"}), 400

        for item in items:
            if "dimensions" not in item:
                return jsonify({"status": "error", "message": "Item missing dimensions"}), 400
            dim = item["dimensions"]
            if "width" not in dim or "height" not in dim or "depth" not in dim:
                return jsonify({"status": "error", "message": "Item dimensions incomplete"}), 400

        # Create a new task ID
        task_id = str(uuid.uuid4())

        # Optional configuration
        config = data.get("config", None)

        # Store task info
        optimization_tasks[task_id] = {
            "id": task_id,
            "status": "pending",
            "progress": 0,
            "start_time": datetime.now().isoformat(),
            "container": container,
            "item_count": len(items)
        }

        # Start optimization in background thread
        container_dims = (container["width"],
                          container["height"], container["depth"])
        thread = threading.Thread(
            target=run_optimization,
            args=(container_dims, items, task_id, config)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            "status": "accepted",
            "task_id": task_id,
            "message": "Optimization started"
        }), 202

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of an optimization task"""
    if task_id not in optimization_tasks:
        return jsonify({"status": "error", "message": "Task not found"}), 404

    task = optimization_tasks[task_id]
    response = {
        "id": task["id"],
        "status": task["status"],
        "progress": task["progress"],
        "start_time": task["start_time"]
    }

    # Include results if available
    if task["status"] in ["completed", "failed"] and "result" in task:
        response["result"] = task["result"]

    # Include intermediate results if available
    if "intermediate_result" in task:
        response["intermediate_result"] = task["intermediate_result"]

    # Include end time if finished
    if "end_time" in task:
        response["end_time"] = task["end_time"]

    # Include execution time if available
    if "execution_time" in task:
        response["execution_time"] = task["execution_time"]

    return jsonify(response)


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """Cancel a running optimization task"""
    if task_id not in optimization_tasks:
        return jsonify({"status": "error", "message": "Task not found"}), 404

    task = optimization_tasks[task_id]

    if task["status"] not in ["pending", "running"]:
        return jsonify({"status": "error", "message": f"Task is {task['status']}, cannot cancel"}), 400

    # Mark as cancelled - the task thread will check this status
    task["status"] = "cancelled"

    return jsonify({
        "status": "success",
        "message": "Task cancellation requested"
    })


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """List all optimization tasks"""
    tasks = []
    for task_id, task in optimization_tasks.items():
        # Create a simplified version of the task
        task_info = {
            "id": task_id,
            "status": task["status"],
            "progress": task["progress"],
            "start_time": task["start_time"],
            "item_count": task.get("item_count", 0)
        }

        if "end_time" in task:
            task_info["end_time"] = task["end_time"]

        tasks.append(task_info)

    return jsonify({
        "status": "success",
        "tasks": tasks
    })


# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Service is running"})


# Example API usage for documentation
@app.route('/', methods=['GET'])
def api_docs():
    docs = {
        "name": "3D Bin Packing API",
        "description": "API for optimizing 3D bin packing problems",
        "endpoints": [
            {
                "path": "/api/optimize",
                "method": "POST",
                "description": "Start a new optimization task",
                "request_example": {
                    "container": {
                        "width": 25,
                        "height": 25,
                        "depth": 25
                    },
                    "items": [
                        {
                            "id": 1,
                            "name": "Laptop",
                            "dimensions": {
                                "width": 33,
                                "height": 22,
                                "depth": 2
                            }
                        },
                        {
                            "id": 2,
                            "name": "Box",
                            "dimensions": {
                                "width": 10,
                                "height": 10,
                                "depth": 10
                            }
                        }
                    ],
                    "config": {
                        "population_size": 30,
                        "generations": 50
                    }
                }
            },
            {
                "path": "/api/tasks/{task_id}",
                "method": "GET",
                "description": "Get status of an optimization task"
            },
            {
                "path": "/api/tasks/{task_id}/cancel",
                "method": "POST",
                "description": "Cancel a running optimization task"
            },
            {
                "path": "/api/tasks",
                "method": "GET",
                "description": "List all optimization tasks"
            }
        ]
    }
    return jsonify(docs)


if __name__ == '__main__':
    app.run(debug=False)
