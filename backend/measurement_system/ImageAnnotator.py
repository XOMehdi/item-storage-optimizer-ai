import cv2 as cv
from Config import *
from GeometryCalculator import *


class ImageAnnotator:
    """Handles image annotation with measurements and visual indicators."""

    @staticmethod
    def annotate_image(image, bounding_box, width_real, height_real):
        top_left, top_right, bottom_right, bottom_left = bounding_box

        # Calculate Midpoints of Edges
        top_edge_mid = GeometryCalculator.calc_midpoint(top_left, top_right)
        bottom_edge_mid = GeometryCalculator.calc_midpoint(
            bottom_left, bottom_right)
        left_edge_mid = GeometryCalculator.calc_midpoint(top_left, bottom_left)
        right_edge_mid = GeometryCalculator.calc_midpoint(
            top_right, bottom_right)

        cv.drawContours(image, [bounding_box.astype(
            "int")], -1, (0, 255, 0), Config.LINE_THICKNESS)

        # Draw cross lines
        cv.line(image,
                (int(top_edge_mid[0]), int(top_edge_mid[1])),
                (int(bottom_edge_mid[0]), int(bottom_edge_mid[1])),
                Config.LINE_COLOR, Config.LINE_THICKNESS)
        cv.line(image,
                (int(left_edge_mid[0]), int(left_edge_mid[1])),
                (int(right_edge_mid[0]), int(right_edge_mid[1])),
                Config.LINE_COLOR, Config.LINE_THICKNESS)

        # Get text sizes
        (width_text, height_text), _ = cv.getTextSize(
            f"{width_real}{Config.MEASURE_UNIT}", Config.TEXT_FONT, Config.TEXT_SCALE, Config.TEXT_THICKNESS)
        (height_text_h, width_text_h), _ = cv.getTextSize(
            f"{height_real}{Config.MEASURE_UNIT}", Config.TEXT_FONT, Config.TEXT_SCALE, Config.TEXT_THICKNESS)

        # Positioning for width text
        width_text_x = int(left_edge_mid[0] - 50)
        width_text_y = int(left_edge_mid[1])

        # Positioning for height text
        height_text_x = int(top_edge_mid[0] - 15)
        height_text_y = int(top_edge_mid[1] + 30)

        # Draw black rectangle for width text
        cv.rectangle(image,
                     (width_text_x - Config.BOX_PADDING,
                      width_text_y - height_text - Config.BOX_PADDING),
                     (width_text_x + width_text + Config.BOX_PADDING,
                      width_text_y + Config.BOX_PADDING),
                     Config.BOX_COLOR, cv.FILLED)

        # Draw black rectangle for height text
        cv.rectangle(image,
                     (height_text_x - Config.BOX_PADDING,
                      height_text_y - width_text_h - Config.BOX_PADDING),
                     (height_text_x + height_text_h + Config.BOX_PADDING,
                      height_text_y + Config.BOX_PADDING),
                     Config.BOX_COLOR, cv.FILLED)

        # Put text on top of black rectangles
        cv.putText(image, f"{width_real}{Config.MEASURE_UNIT}",
                   (width_text_x, width_text_y),
                   Config.TEXT_FONT, Config.TEXT_SCALE, Config.TEXT_COLOR, Config.TEXT_THICKNESS)
        cv.putText(image, f"{height_real}{Config.MEASURE_UNIT}",
                   (height_text_x, height_text_y),
                   Config.TEXT_FONT, Config.TEXT_SCALE, Config.TEXT_COLOR, Config.TEXT_THICKNESS)
