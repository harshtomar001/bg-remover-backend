from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from torchvision.transforms import InterpolationMode
from transformers import AutoModelForImageSegmentation


# Configuration

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "models" / "BiRefNet-HR"

DEVICE = torch.device("cpu")

RESOLUTION = (1024, 1024)


class BiRefNetHRService:

    def __init__(self):
        self.model = None

        self.preprocess = transforms.Compose([
            transforms.Resize(
                RESOLUTION,
                interpolation=InterpolationMode.BILINEAR
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])

    def load_model(self):

        if self.model is not None:
            return

        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                f"BiRefNet-HR model directory not found: {MODEL_DIR}"
            )

        print("Loading BiRefNet-HR model...")

        self.model = AutoModelForImageSegmentation.from_pretrained(
            str(MODEL_DIR),
            trust_remote_code=True,
            local_files_only=True
        )

        self.model.to(DEVICE)
        self.model.eval()

        print("BiRefNet-HR model loaded successfully.")

    def predict_mask(self, image: Image.Image) -> Image.Image:

        if self.model is None:
            raise RuntimeError(
                "BiRefNet-HR model has not been loaded."
            )

        image = image.convert("RGB")

        input_tensor = self.preprocess(image).unsqueeze(0)

        with torch.inference_mode():

            predictions = self.model(input_tensor.to(DEVICE))

            mask = predictions[-1].sigmoid().cpu()

        mask = mask[0].squeeze().float()

        mask_image = transforms.ToPILImage()(mask)

        mask_image = mask_image.resize(
            image.size,
            Image.Resampling.BILINEAR
        )

        return mask_image


# Shared storage instance

birefnet_hr_service = BiRefNetHRService()