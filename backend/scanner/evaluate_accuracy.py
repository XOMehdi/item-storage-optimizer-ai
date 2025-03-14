import os
from main import measure_2d_item


def calculate_accuracy(measured_values, real_measurements_list):
    """
    Calculate accuracy of measured 3D dimensions compared to real values.

    :param measured_values: Dictionary with measured dimensions {'item_name': (width, height)}
    :param real_measurements_list: List of dictionaries [{'item': 'name', 'width': W, 'height': H, 'depth': D}]
    :return: Dictionary with accuracy results
    """
    real_measurements = {
        item["item"].lower(): (item["width"], item["height"])
        for item in real_measurements_list
    }

    accuracies = {}

    for item_name, measured_dims in measured_values.items():
        if item_name in real_measurements:
            real_dims = real_measurements[item_name]

            if len(real_dims) != len(measured_dims):
                print(
                    f"Dimension mismatch for {item_name}: Expected {len(real_dims)} values, Got {len(measured_dims)}")
                continue

            accuracy_scores = [
                (1 - abs(measured - real) / real) * 100
                for measured, real in zip(measured_dims, real_dims)
            ]

            accuracies[item_name] = {
                'measured': measured_dims,
                'real': real_dims,
                'accuracy': accuracy_scores,
                'average_accuracy': sum(accuracy_scores) / len(accuracy_scores)
            }
        else:
            print(f"No real measurements found for {item_name}")

    return accuracies


# Example usage:
real_measurements_cm = [
    {'item': 'card', 'width': 8.5, 'height': 5.3, 'depth': 0.5},
    {'item': 'card-laptop', 'width': 32.5, 'height': 21.5, 'depth': 21.5},
    {'item': 'card-matchbox-1', 'width': 5.8, 'height': 4.52, 'depth': 1.5},
    {'item': 'card-matchbox-2', 'width': 5.8, 'height': 4.52, 'depth': 1.5},
    {'item': 'card-phone', 'width': 7.5, 'height': 15.5, 'depth': 7.5},
    {'item': 'card-usb-1', 'width': 4.0, 'height': 1.2, 'depth': 0.3},
    {'item': 'card-usb-2', 'width': 4.0, 'height': 1.2, 'depth': 0.3},
    {'item': 'card-tissuebox', 'width': 24.0, 'height': 12.0, 'depth': 8.5},
    {'item': 'card-mini-bucket', 'width': 16.0, 'height': 16.0, 'depth': 16.0},
    {'item': 'card-milkpack', 'width': 9.0, 'height': 25.0, 'depth': 25.0},
    {'item': 'coin-2', 'width': 2.0, 'height': 2.0, 'depth': 2.0},
    {'item': 'coin-1', 'width': 1.8, 'height': 1.8, 'depth': 1.8},
    {'item': 'coin-5', 'width': 1.6, 'height': 1.6, 'depth': 1.6}
]

IMAGES_DIRECTORY = "test-images"
measured_values = {}

for file_name in os.listdir(IMAGES_DIRECTORY):
    if not file_name.endswith(('.jpg', '.png', '.jpeg')):  # Ensure it's an image file
        continue

    image_path = os.path.join(IMAGES_DIRECTORY, file_name)
    # Extract item name from file name
    item_name = file_name.split('.')[0].lower()

    measurements = measure_2d_item(image_path, "left", 8.56)

    measured_values[item_name] = (
        measurements["width"], measurements["height"]
    )

accuracy_results = calculate_accuracy(measured_values, real_measurements_cm)

for item, result in accuracy_results.items():
    print(f"{item}: {result['average_accuracy']:.2f}% accuracy")
