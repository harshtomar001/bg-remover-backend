from abc import ABC, abstractmethod
from PIL import Image


class ModelInterface(ABC):
    """
    Common interface for all background removal models.
    """

    @abstractmethod
    def load_model(self) -> None:
        """
        Load model weights and initialize the model.
        """
        pass

    @abstractmethod
    def predict_mask(self, image: Image.Image) -> Image.Image:
        """
        Generate a foreground alpha mask.

        Expected output:
        - PIL Image
        - Grayscale (L) mode
        - Same dimensions as the input image
        - Pixel values between 0 and 255
        """
        pass

    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Generate a transparent RGBA image using the predicted mask.
        """

        # Preserve the original RGB image.
        original_image = image.convert("RGB")

        # Generate the foreground mask.
        mask = self.predict_mask(original_image)

        # Ensure grayscale mask.
        if mask.mode != "L":
            mask = mask.convert("L")

        # Ensure mask dimensions match the original image.
        if mask.size != original_image.size:
            mask = mask.resize(
                original_image.size,
                Image.Resampling.BILINEAR
            )

        # Apply the mask as the alpha channel.
        result = original_image.copy()
        result.putalpha(mask)

        return result