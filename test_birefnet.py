from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation


# Configuration
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models" / "BiRefNet-DIS5K"
INPUT_IMAGE = BASE_DIR / "test_input.png"
OUTPUT_IMAGE = BASE_DIR / "test_output.png"

RESOLUTION = (1024, 1024)
DEVICE = torch.device("cpu")


def main():
    if not INPUT_IMAGE.exists():
        raise FileNotFoundError(f"Input image not found: {INPUT_IMAGE}")

    print("Loading BiRefNet from the local checkpoint...")

    model = AutoModelForImageSegmentation.from_pretrained(
        str(MODEL_DIR),
        trust_remote_code=True,
        local_files_only=True,
    )

    model.to(DEVICE)
    model.eval()

    print("Model loaded successfully.")

    with Image.open(INPUT_IMAGE) as source:
        original_image = source.convert("RGB")

    print(f"Original image size: {original_image.size}")

    preprocess = transforms.Compose([
        transforms.Resize(RESOLUTION),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    input_tensor = preprocess(original_image).unsqueeze(0)

    print(f"Input tensor shape: {tuple(input_tensor.shape)}")
    print("Running inference on CPU. This may take a while...")

    with torch.inference_mode():
        predictions = model(input_tensor)
        prediction = predictions[-1].sigmoid().cpu()

    mask = prediction[0].squeeze().float()

    print(f"Prediction shape: {tuple(mask.shape)}")
    print(f"Prediction minimum: {mask.min().item():.6f}")
    print(f"Prediction maximum: {mask.max().item():.6f}")



    RAW_MASK_IMAGE = BASE_DIR / "test_mask.png"

    mask_image = transforms.ToPILImage()(mask)
    mask_image.save(RAW_MASK_IMAGE)

    print(f"Raw mask saved to: {RAW_MASK_IMAGE}")

    mask_image = mask_image.resize(
        original_image.size,
        Image.Resampling.BILINEAR,
    )

    result = original_image.copy()
    result.putalpha(mask_image)
    result.save(OUTPUT_IMAGE, format="PNG")

    print(f"Transparent PNG saved to: {OUTPUT_IMAGE}")
    print("Inference test completed successfully.")


if __name__ == "__main__":
    main()