from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "models" / "BiRefNet-DIS5K"

DEVICE = torch.device("cpu")

RESOLUTION = (1024, 1024)


class BiRefNetService:

    def __init__(self):
        self.model = None

        self.preprocess = transforms.Compose([
            transforms.Resize(RESOLUTION),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    def load_model(self):
        if self.model is not None:
            return

        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                f"BiRefNet model directory not found: {MODEL_DIR}"
            )

        print("Loading BiRefNet model...")

        self.model = AutoModelForImageSegmentation.from_pretrained(
            str(MODEL_DIR),
            trust_remote_code=True,
            local_files_only=True,
        )

        self.model.to(DEVICE)
        self.model.eval()

        print("BiRefNet model loaded successfully.")

    def predict(self, image: Image.Image) -> Image.Image:
        if self.model is None:
            raise RuntimeError(
                "BiRefNet model has not been loaded."
            )

        # Convert the image to RGB.
        image = image.convert("RGB")

        # Prepare the image for BiRefNet.
        input_tensor = self.preprocess(image).unsqueeze(0)

        # Run model inference.
        with torch.inference_mode():
            predictions = self.model(input_tensor.to(DEVICE))

            mask = predictions[-1].sigmoid().cpu()

        # Extract the mask for our single input image.
        mask = mask[0].squeeze().float()

        # Convert the mask to a grayscale PIL image.
        mask_image = transforms.ToPILImage()(mask)

        # Resize the mask to the original image dimensions.
        mask_image = mask_image.resize(
            image.size,
            Image.Resampling.BILINEAR,
        )

        return mask_image

    def remove_background(self, image: Image.Image) -> Image.Image:
        """
        Remove the background and return a transparent RGBA image.
        """

        # Preserve the original image's RGB pixels.
        original_image = image.convert("RGB")

        # Predict the foreground mask.
        mask = self.predict(original_image)

        # Apply the mask as the alpha channel.
        result = original_image.copy()
        result.putalpha(mask)

        return result


# Shared storage instance.
birefnet_service = BiRefNetService()