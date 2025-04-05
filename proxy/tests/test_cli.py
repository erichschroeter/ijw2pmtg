import os
import shutil
import tempfile
import unittest
from PIL import Image

from proxy.cli import rotate_image

TOP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_image = os.path.join(
            TOP_DIR,
            "scryfall/tests/cache/images/Skullclamp.MOC.png",
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_rotate_image(self):
        # Copy test image to temp directory
        temp_image = os.path.join(self.test_dir, "test_image.png")
        shutil.copy2(self.test_image, temp_image)

        # Get original dimensions
        with Image.open(temp_image) as img:
            original_width, original_height = img.size

        # Rotate image 90 degrees
        rotate_image(temp_image, 90)

        # Verify dimensions are swapped (90 degree rotation)
        with Image.open(temp_image) as img:
            rotated_width, rotated_height = img.size
            self.assertEqual(original_width, rotated_height)
            self.assertEqual(original_height, rotated_width)

    def test_rotate_image_negative(self):
        # Copy test image to temp directory
        temp_image = os.path.join(self.test_dir, "test_image.png")
        shutil.copy2(self.test_image, temp_image)

        # Get original dimensions
        with Image.open(temp_image) as img:
            original_width, original_height = img.size

        # Rotate image 90 degrees
        rotate_image(temp_image, -90)

        # Verify dimensions are swapped (90 degree rotation)
        with Image.open(temp_image) as img:
            rotated_width, rotated_height = img.size
            self.assertEqual(original_width, rotated_height)
            self.assertEqual(original_height, rotated_width)


if __name__ == "__main__":
    unittest.main()
