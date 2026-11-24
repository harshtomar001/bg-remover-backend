import time
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from torchvision.transforms import InterpolationMode
from transformers import AutoModelForImageSegmentation


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "models" / "BiRefNet-HR"
INPUT_PATH = BASE_DIR / "test_input.png"
OUTPUT_PATH = BASE_DIR / "birefnet_hr_test_output.png"

DEVICE = torch.device("cpu")
RESOLUTION = (1024, 1024)


# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------

preprocess = transforms.Compose([
    transforms.Resize(
        RESOLUTION,
        interpolation=InterpolationMode.BILINEAR
    ),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# Converts the input image into 1024 × 1024.
# Bilinear interpolation calculates new pixel values using neighbouring pixels.

def main():

    print("=" * 55)
    print("BiRefNet-HR CPU SMOKE TEST")
    print("=" * 55)

    # Validate paths
    if not MODEL_DIR.exists():
        raise FileNotFoundError(
            f"Model directory not found: {MODEL_DIR}"
        )

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input image not found: {INPUT_PATH}"
        )

    # Load model
    print("\nInitializing BiRefNet-HR on CPU...")

    start_time = time.perf_counter()

    model = AutoModelForImageSegmentation.from_pretrained(
        str(MODEL_DIR),
        trust_remote_code=True,
        local_files_only=True
    )

    model.to(DEVICE)
    model.eval()

    load_time = time.perf_counter() - start_time

    print(f"Model loaded successfully in {load_time:.2f} seconds")

    # Load original image
    original_image = Image.open(INPUT_PATH).convert("RGB")

    original_size = original_image.size

    # Preprocess
    input_tensor = preprocess(original_image).unsqueeze(0)

    # Inference
    print("\nRunning inference...")

    inference_start = time.perf_counter()

    with torch.inference_mode():

        predictions = model(input_tensor.to(DEVICE))

        prediction = predictions[-1].sigmoid()

    inference_time = time.perf_counter() - inference_start

    print(f"Inference completed in {inference_time:.2f} seconds")

    # Convert prediction into alpha mask
    mask = prediction[0].squeeze().cpu()

    mask_image = transforms.ToPILImage()(mask)

    mask_image = mask_image.resize(
        original_size,
        Image.Resampling.BILINEAR
    )

    # Apply alpha mask
    result = original_image.copy()
    result.putalpha(mask_image)

    # Save output
    result.save(OUTPUT_PATH, format="PNG")

    # Collect statistics
    alpha_min, alpha_max = mask_image.getextrema()

    print("\nRESULTS")
    print("-" * 55)

    print("Model: BiRefNet-HR")
    print("Device: CPU")
    print(f"Output mode: {result.mode}")
    print(f"Output dimensions: {result.size}")
    print(f"Alpha range: ({alpha_min}, {alpha_max})")

    print(f"Model loading time: {load_time:.2f} seconds")
    print(f"Inference time: {inference_time:.2f} seconds")

    print(f"Output saved: {OUTPUT_PATH}")

    print("\nBiRefNet-HR CPU SMOKE TEST PASSED")


if __name__ == "__main__":
    main()