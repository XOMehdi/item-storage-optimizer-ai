import os
from main import measure_3d_item


# def calculate_accuracy(measured_values, real_measurements):
#     accuracies = {}

#     for item, real_dims in real_measurements.items():
#         if item.lower() in measured_values:
#             measured_dims = measured_values[item.lower()]

#             if len(real_dims) != len(measured_dims):
#                 print(
#                     f"Dimension mismatch for {item}: Expected {len(real_dims)} values, Got {len(measured_dims)}")
#                 continue

#             accuracy_scores = []
#             for measured, real in zip(measured_dims, real_dims):
#                 accuracy = (1 - abs(measured - real) / real) * 100
#                 accuracy_scores.append(accuracy)

#             accuracies[item] = {
#                 'measured': measured_dims,
#                 'real': real_dims,
#                 'accuracy': accuracy_scores,
#                 'average_accuracy': sum(accuracy_scores) / len(accuracy_scores)
#             }
#         else:
#             print(f"No measured values found for {item}")

#     return accuracies


# # Example usage:


# IMAGES_DIRECTORY = "test-images"
# for file_name in os.listdir(IMAGES_DIRECTORY):
#     image_path = os.path.join(IMAGES_DIRECTORY, file_name)

#     measured_values = measure_3d_item(image_path, image_path, "card", "left")

# accuracy_results = calculate_accuracy(measured_values, real_measurements_cm)
# for item, result in accuracy_results.items():
#     print(f"{item}: {result['average_accuracy']:.2f}% accuracy")


def calculate_accuracy(measured_values, real_measurements_list):
    """
    Calculate accuracy of measured 3D dimensions compared to real values.

    :param measured_values: Dictionary with measured dimensions {'item_name': (width, height, depth)}
    :param real_measurements_list: List of dictionaries [{'item': 'name', 'width': W, 'height': H, 'depth': D}]
    :return: Dictionary with accuracy results
    """
    real_measurements = {
        item["item"].lower(): (item["width"], item["height"], item["depth"])
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
    {'item': 'card-matchbox-1', 'width': 5.8, 'height': 4.5, 'depth': 4.5},
    {'item': 'card-matchbox-2', 'width': 5.8, 'height': 4.5, 'depth': 4.5},
    {'item': 'card-mouse', 'width': 11.8, 'height': 5.8, 'depth': 5.8},
    {'item': 'card-phone', 'width': 7.5, 'height': 15.5, 'depth': 7.5},
    {'item': 'card-usb-1', 'width': 4.0, 'height': 1.2, 'depth': 1.2},
    {'item': 'card-usb-2', 'width': 4.0, 'height': 1.2, 'depth': 1.2},
    {'item': 'card-tissue-box', 'width': 24.0, 'height': 12.0, 'depth': 12.0},
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

    side_image_path = image_path.replace(
        "front", "side")  # Assuming naming convention

    if not os.path.exists(side_image_path):
        print(f"Skipping {file_name}: No side view found.")
        continue

    measurements = measure_3d_item(image_path, side_image_path, "card", "left")

    measured_values[item_name] = (
        measurements["width"], measurements["height"], measurements["depth"]
    )

accuracy_results = calculate_accuracy(measured_values, real_measurements_cm)

for item, result in accuracy_results.items():
    print(f"{item}: {result['average_accuracy']:.2f}% accuracy")
