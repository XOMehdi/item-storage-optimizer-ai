import cv2 as cv
from Config import *


class ImageProcessor:
    """Handles image processing operations like resizing and edge detection."""

    @staticmethod
    def resize_image(image, max_width=1920, max_height=1080):
        h, w = image.shape[:2]
        aspect_ratio = w / h

        while w > max_width or h > max_height:
            if w > max_width:
                w = max_width
                h = int(w / aspect_ratio)

            if h > max_height:
                h = max_height
                w = int(h * aspect_ratio)

        return cv.resize(image, (w, h), interpolation=cv.INTER_LANCZOS4)

    @staticmethod
    def detect_edges(image, upper_threshold=None):
        edges = cv.Canny(image, 10, upper_threshold)
        edges = cv.dilate(edges, Config.CANNY_KERNEL,
                          iterations=Config.CANNY_DILATE_ITERATIONS)
        edges = cv.erode(edges, Config.CANNY_KERNEL,
                         iterations=Config.CANNY_ERODE_ITERATIONS)

        return edges

    @staticmethod
    def decode_base64_image(base64_string):
        """Decode base64 string to OpenCV image."""
        # Decode the base64 string
        img_data = base64.b64decode(base64_string)
        # Convert to numpy array
        nparr = np.frombuffer(img_data, np.uint8)
        # Decode image
        img = cv.imdecode(nparr, cv.IMREAD_COLOR)
        return img

    @staticmethod
    def encode_image_to_base64(image):
        """Encode OpenCV image to base64 string."""
        # Convert image to PIL format
        img_pil = Image.fromarray(cv.cvtColor(image, cv.COLOR_BGR2RGB))
        # Save to buffer
        buffer = io.BytesIO()
        img_pil.save(buffer, format="JPEG")
        # Encode to base64
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return img_str
