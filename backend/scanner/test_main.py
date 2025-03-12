import unittest
from main import measure_3d_object


class TestMeasure3DObject(unittest.TestCase):
    def test_measure_3d_object(self):
        test_cases = [
            {'item': 'card-1', 'width': 8.56, 'height': 5.28, 'depth': 5.28},
            {'item': 'card-2', 'width': 8.56, 'height': 5.39, 'depth': 5.39},
            {'item': 'card-charging-brick', 'width': 5.03,
                'height': 10.3, 'depth': 10.3},
            {'item': 'card-laptop', 'width': 32.24,
                'height': 21.29, 'depth': 21.29},
            {'item': 'card-matchbox-1', 'width': 6.94,
                'height': 5.39, 'depth': 5.39},
            {'item': 'card-matchbox-2', 'width': 10.5,
                'height': 2.79, 'depth': 2.79},
            {'item': 'card-mouse', 'width': 7.03, 'height': 11.67, 'depth': 11.67},
            {'item': 'card-phone', 'width': 8.39, 'height': 17.26, 'depth': 17.26},
            {'item': 'card-usb-1', 'width': 4.5, 'height': 1.58, 'depth': 1.58},
            {'item': 'card-usb-2', 'width': 4.66, 'height': 1.46, 'depth': 1.46}
        ]

        for case in test_cases:
            with self.subTest(case=case):
                print(f"Testing {case['item']}")
                front_image_path = f"test-images/{case['item']}.jpg"
                side_image_path = f"test-images/{case['item']}.jpg"
                result = measure_3d_object(
                    front_image_path, side_image_path, "card")
                self.assertEqual(result['width'], case['width'])
                self.assertEqual(result['height'], case['height'])
                self.assertEqual(result['depth'], case['depth'])


if __name__ == '__main__':
    unittest.main()
