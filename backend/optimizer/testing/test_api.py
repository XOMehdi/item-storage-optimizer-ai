import time
import requests
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def visualize_packing(dimensions, placements, title_suffix=""):
    """Visualize the packed container using Matplotlib 3D"""
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    width, height, depth = dimensions
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_zlim(0, depth)

    # Set labels
    ax.set_xlabel('Width')
    ax.set_ylabel('Height')
    ax.set_zlabel('Depth')
    ax.set_title(f'3D Bin Packing Visualization {title_suffix}')

    # More diverse color palette
    colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33',
              '#a65628', '#f781bf', '#999999', '#66c2a5', '#fc8d62', '#8da0cb']

    for i, (item_id, x, y, z, w, h, d) in enumerate(placements):
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

        poly = Poly3DCollection(faces, facecolors=color,
                                linewidths=1, edgecolors='k', alpha=0.7)
        ax.add_collection3d(poly)

        center_x, center_y, center_z = x + w/2, y + h/2, z + d/2
        ax.text(center_x, center_y, center_z, str(item_id),
                color='black', fontsize=9, ha='center')

    plt.tight_layout()
    plt.show()


# API_URL = "https://optimizer.up.railway.app/optimize"
API_URL = "http://127.0.0.1:5000/optimize"

# API request payload
payload = {
    "container": {
        "width": 30,
        "height": 20,
        "depth": 10
    },
    "items": [
        {"id": 1, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 2, "dimensions": {"width": 4, "height": 2, "depth": 1}},
        {"id": 3, "dimensions": {"width": 4, "height": 2, "depth": 1}},
        {"id": 4, "dimensions": {"width": 4, "height": 2, "depth": 1}},
        {"id": 5, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 6, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 7, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 8, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 9, "dimensions": {"width": 6, "height": 6, "depth": 2}},
        {"id": 10, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 11, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 12, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 13, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 14, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 15, "dimensions": {"width": 16, "height": 8, "depth": 1}},
        {"id": 16, "dimensions": {"width": 24, "height": 12, "depth": 9}},
        {"id": 17, "dimensions": {"width": 9, "height": 25, "depth": 7}},
    ],
    "config": {
        "population_size": 100,
        "generations": 50
    }
}

try:
    start_time = time.time()
    response = requests.post(API_URL, json=payload)

    if response.status_code == 200:
        result = response.json()
        dimensions = (
            payload["container"]["width"],
            payload["container"]["height"],
            payload["container"]["depth"]
        )

        if result.get("status") == "success":
            print("✅ Full packing successful!")
            print("Space Utilization:", result["space_utilization"], "%")
            visualize_packing(dimensions, result["placements"], "(Full)")

        elif result.get("status") == "failure":
            print("⚠️ Partial packing completed.")
            print("Space Utilization:", result["space_utilization"], "%")
            print("Message:", result.get(
                "message", "Some items could not be placed."))
            visualize_packing(dimensions, result["placements"], "(Partial)")
            
        else:
            print("❌ Unexpected response format:", result)

        print(
            f"\nTotal execution time: {time.time() - start_time:.2f} seconds")

    else:
        print(f"❌ HTTP Error {response.status_code}: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"❌ Request failed: {e}")
