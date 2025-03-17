import uuid
from ImageProcessor import *


class Dimension:
    def __init__(self):
        self.width = None
        self.height = None
        self.depth = None

    def set_width(self, width):
        self.width = width

    def set_height(self, height):
        self.height = height

    def set_depth(self, depth):
        self.depth = depth

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_depth(self):
        return self.depth


class Position:
    def __init__(self):
        self.x = None
        self.y = None
        self.z = None

    def set_x(self, x):
        self.x = x

    def set_y(self, y):
        self.y = y

    def set_z(self, z):
        self.z = z

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def get_z(self):
        return self.z


class Item:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.front_image = None
        self.side_image = None
        self.dimension = Dimension()
        self.position = Position()

    def set_front_image_path(self, front_image_path):
        self.front_image_path = front_image_path

    def set_side_image_path(self, side_image_path):
        self.side_image_path = side_image_path

    def set_dimension(self, width, height, depth):
        self.dimension.set_width(width)
        self.dimension.set_height(height)
        self.dimension.set_depth(depth)

    def set_position(self, x, y, z):
        self.position.set_x(x)
        self.position.set_y(y)
        self.position.set_z(z)

    def get_id(self):
        return self.id

    def get_front_image(self):
        return self.front_image

    def get_side_image(self):
        return self.side_image

    def get_dimension(self):
        return self.dimension

    def get_position(self):
        return self.position


class Scanner:
    def __init__(self, images_path, ref_obj_width_real, ref_obj_pos):
        self.item = Item()
        self.images_path = images_path
        self.ref_obj_width_real = ref_obj_width_real
        self.ref_obj_pos = ref_obj_pos
        self.process_and_store_image(images_path[0], images_path[1])

    def process_and_store_image(self, front_image_path, side_image_path):

        item_id = self.item.get_id()

        # Resize and store images
        front_image_processor = ImageProcessor(
            front_image_path, item_id, "front")
        side_image_processor = ImageProcessor(
            side_image_path, item_id, "side")

        front_image_path = front_image_processor.retrieve_image(
            item_id, "front")
        side_image_path = side_image_processor.retrieve_image(
            item_id, "side")

        # Set image path with resized images for errorless processing later
        self.item.set_front_image_path(front_image_path)
        self.item.set_side_image_path(side_image_path)

    def measure_item_2d(self, image):

        # All image processing done with this line
        # Find Contours
        contour_list = ImageProcessor.get_contours(image)

        contour_list, _ = imutils_sort_contours(
            contour_list, method=self.get_sorting_order())
#
        # ref_obj_contour, obj_contour = get_two_largest_contours(contour_list)

    def get_sorting_order(self):
        if (self.ref_obj_pos == "left"):
            return "left-to-right"
        elif (self.ref_obj_pos == "right"):
            return "right-to-left"
        elif (self.ref_obj_pos == "top"):
            return "top-to-bottom"
        elif (self.ref_obj_pos == "bottom"):
            return "bottom-to-top"

        return "left-to-right"

    def measure_item_3d(self):
        front_measurements = self.measure_item_2d(self.item.get_front_image())
        side_measurements = self.measure_item_2d(self.item.get_side_image())

        front_width, front_height = front_measurements["width"], front_measurements["height"]
        side_width, side_height = side_measurements["width"], side_measurements["height"]

        # Store in a sorted list from largest to smallest
        dimensions = [front_width, front_height, side_width, side_height]
        dimensions.sort(reverse=True)

        # The smallest value is the depth
        width, height, depth = dimensions[0], dimensions[1], dimensions[3]

        # Check if the two largest values come from the same image
        if (dimensions[0] == front_width and dimensions[1] == front_height) or \
                (dimensions[0] == side_width and dimensions[1] == side_height):
            pass
        else:
            width, height = dimensions[0], dimensions[2]

        item_name = self.images_path[0].split(
            "/")[-1].split(".")[0].rsplit("-", 1)[0]

        return {"item": item_name, "width": width, "height": height, "depth": depth}
