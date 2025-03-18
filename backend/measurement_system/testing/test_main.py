import unittest
from MeasurementSystem import MeasurementSystem
import cv2 as cv


IMAGES_DIRECTORY = "testing/images"
measurement_system = MeasurementSystem("left", 8.56, [None, None])


class TestMeasure3DItem(unittest.TestCase):

    def test_measure_2d_item(self):
        test_cases = [
            {'item': 'card-laptop', 'width': 32.24, 'height': 21.29},
            {'item': 'card-matchbox-1', 'width': 6.94, 'height': 5.39},
            {'item': 'card-matchbox-2', 'width': 10.5, 'height': 2.79},
            {'item': 'card-phone', 'width': 8.39, 'height': 17.26},
            {'item': 'card-usb-1', 'width': 4.5, 'height': 1.58},
            {'item': 'card-usb-2', 'width': 4.66, 'height': 1.46}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                image_path = f"{IMAGES_DIRECTORY}/{case['item']}.jpg"
                image = cv.imread(image_path)

                result = measurement_system.measure_2d_item(image, None)

                self.assertEqual(
                    result['width'], case['width'], f"Failed on {case['item']} - Expected width: {case['width']}, Got: {result['width']}")
                self.assertEqual(result['height'], case['height'],
                                 f"Failed on {case['item']} - Expected height: {case['height']}, Got: {result['height']}")

    def test_measure_3d_item(self):
        test_cases = [
            {'item': 'card-matchbox', 'width': 10.5, 'height': 5.39, 'depth': 2.79},
            {'item': 'card-usb', 'width': 4.66, 'height': 1.58, 'depth': 1.46}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                front_image_path = f"{IMAGES_DIRECTORY}/{case['item']}-1.jpg"
                side_image_path = f"{IMAGES_DIRECTORY}/{case['item']}-2.jpg"

                front_image = cv.imread(front_image_path)
                side_image = cv.imread(side_image_path)

                result = measurement_system.measure_3d_item(
                    front_image, side_image)

                self.assertEqual(
                    result['width'], case['width'], f"Failed on {case['item']} - Expected width: {case['width']}, Got: {result['width']}")
                self.assertEqual(result['height'], case['height'],
                                 f"Failed on {case['item']} - Expected height: {case['height']}, Got: {result['height']}")
                self.assertEqual(
                    result['depth'], case['depth'], f"Failed on {case['item']} - Expected depth: {case['depth']}, Got: {result['depth']}")


if __name__ == '__main__':
    unittest.main()
