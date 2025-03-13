import unittest
from main import measure_2d_item, measure_3d_item


class TestMeasure3DItem(unittest.TestCase):

    def test_measure_2d_item(self):
        test_cases = [
            {'item': 'card-charging-brick', 'width': 5.03, 'height': 10.3},
            {'item': 'card-laptop', 'width': 32.24, 'height': 21.29},
            {'item': 'card-matchbox-1', 'width': 6.94, 'height': 5.39},
            {'item': 'card-matchbox-2', 'width': 10.5, 'height': 2.79},
            {'item': 'card-mouse', 'width': 7.03, 'height': 11.67},
            {'item': 'card-phone', 'width': 8.39, 'height': 17.26},
            {'item': 'card-usb-1', 'width': 4.5, 'height': 1.58},
            {'item': 'card-usb-2', 'width': 4.66, 'height': 1.46}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                image_path = f"test-images/{case['item']}.jpg"
                result = measure_2d_item(image_path, "left", 8.56)

                self.assertEqual(
                    result['width'], case['width'], f"Failed on {case['item']} - Expected width: {case['width']}, Got: {result['width']}")
                self.assertEqual(result['height'], case['height'],
                                 f"Failed on {case['item']} - Expected height: {case['height']}, Got: {result['height']}")

    def test_measure_3d_item(self):
        test_cases = [
            {'item': 'card-matchbox', 'width': 10.5, 'height': 6.94, 'depth': 2.79},
            {'item': 'card-usb', 'width': 4.66, 'height': 4.5, 'depth': 1.46}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                front_image_path = f"test-images/{case['item']}-1.jpg"
                side_image_path = f"test-images/{case['item']}-2.jpg"
                result = measure_3d_item(
                    front_image_path, side_image_path, "card", "left")

                self.assertEqual(
                    result['width'], case['width'], f"Failed on {case['item']} - Expected width: {case['width']}, Got: {result['width']}")
                self.assertEqual(result['height'], case['height'],
                                 f"Failed on {case['item']} - Expected height: {case['height']}, Got: {result['height']}")
                self.assertEqual(
                    result['depth'], case['depth'], f"Failed on {case['item']} - Expected depth: {case['depth']}, Got: {result['depth']}")


if __name__ == '__main__':
    unittest.main()
