from Config import *
from MeasurementSystem import MeasurementSystem
import os


class MeasurementApp:
    """Application class that serves as the entry point."""

    def __init__(self):
        self.measurement_system = MeasurementSystem()

    def run(self):
        """Run the application, processing all images in the directory."""
        for file_name in os.listdir(Config.IMAGES_DIRECTORY):
            image_path = os.path.join(Config.IMAGES_DIRECTORY, file_name)

            print(image_path)
            if image_path.endswith("-1.jpg"):
                item_dimensions = self.measurement_system.measure_3d_item(
                    image_path,
                    image_path.replace("-1", "-2"),
                    "left",
                    8.56
                )
                print(item_dimensions)
