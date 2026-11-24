import torch
from pathlib import Path
from PIL import Image
from transparent_background import Remover


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_CHECKPOINT = (
        BASE_DIR / "models" / "InSPyReNet" / "ckpt_base.pth"
)


class InSPyReNetService:

    def __init__(self):
        self.model = None
        self.device = "cpu"

    def load_model(self) -> None:

        if self.model is not None:
            return

        if not MODEL_CHECKPOINT.exists():
            raise FileNotFoundError(
                f"InSPyReNet checkpoint not found: {MODEL_CHECKPOINT}"
            )

        self.model = Remover(
            mode="base",
            device=self.device,
            ckpt=str(MODEL_CHECKPOINT)
        )

    def predict_mask(self, image: Image.Image) -> Image.Image:

        if self.model is None:
            raise RuntimeError(
                "InSPyReNet model has not been loaded."
            )

        original = image.convert("RGB")

        with torch.inference_mode():
            pred_map = self.model.process(
                original,
                type="map"
            )

        mask = pred_map.convert("L")

        if mask.size != original.size:
            mask = mask.resize(
                original.size,
                Image.Resampling.BILINEAR
            )

        return mask


# Shared service instance
inspyrenet_service = InSPyReNetService()