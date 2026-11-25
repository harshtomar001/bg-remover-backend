import numpy as np

from PIL import Image, ImageFilter


class ImageAnalyzer:

    def __init__(self, analysis_size=(256, 256)):
        self.analysis_size = analysis_size

    def analyze(self, image: Image.Image) -> dict:

        if not isinstance(image, Image.Image):
            raise TypeError("Input must be a PIL Image.")

        image = image.convert("RGB")

        original_width, original_height = image.size

        if original_width <= 0 or original_height <= 0:
            raise ValueError("Image dimensions must be positive.")

        resized = image.resize(
            self.analysis_size,
            Image.Resampling.LANCZOS
        )

        rgb = np.asarray(resized, dtype=np.float32) / 255.0

        grayscale_image = resized.convert("L")

        grayscale = np.asarray(
            grayscale_image,
            dtype=np.float32
        ) / 255.0

        # Image dimensions

        aspect_ratio = original_width / original_height

        total_pixels = original_width * original_height

        # Brightness

        brightness = float(np.mean(grayscale))

        # Contrast

        contrast = float(np.std(grayscale))

        # Color variance

        color_variance = float(
            np.mean(np.var(rgb, axis=(0, 1)))
        )

        # Image entropy

        histogram, _ = np.histogram(
            grayscale,
            bins=256,
            range=(0.0, 1.0)
        )

        probabilities = histogram / histogram.sum()

        probabilities = probabilities[probabilities > 0]

        entropy = float(
            -np.sum(probabilities * np.log2(probabilities))
        )

        # Edge density

        edges = grayscale_image.filter(
            ImageFilter.FIND_EDGES
        )

        edge_array = np.asarray(
            edges,
            dtype=np.float32
        ) / 255.0

        edge_density = float(
            np.mean(edge_array > 0.1)
        )

        return {
            "width": original_width,
            "height": original_height,
            "aspect_ratio": float(aspect_ratio),
            "total_pixels": total_pixels,
            "brightness": brightness,
            "contrast": contrast,
            "color_variance": color_variance,
            "entropy": entropy,
            "edge_density": edge_density,
        }


image_analyzer = ImageAnalyzer()