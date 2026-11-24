import time
from pathlib import Path

import torch
import numpy as np
from PIL import Image
from transparent_background import Remover


BASE_DIR = Path(__file__).resolve().parent.parent

CHECKPOINT = BASE_DIR / "models" / "InSPyReNet" / "ckpt_base.pth"
INPUT_IMAGE = BASE_DIR / "test_input.png"
OUTPUT_IMAGE = BASE_DIR / "inspyrenet_test_output.png"


def main():

    print("=" * 55)
    print("InSPyReNet CPU SMOKE TEST")
    print("=" * 55)

    assert CHECKPOINT.exists(), "InSPyReNet checkpoint missing"
    assert INPUT_IMAGE.exists(), "Input image missing"

    print("\nInitializing InSPyReNet on CPU...")

    start = time.perf_counter()

    remover = Remover(
        mode="base",
        device="cpu",
        ckpt=str(CHECKPOINT)
    )

    load_time = time.perf_counter() - start

    print(f"Model loaded successfully in {load_time:.2f} seconds")

    with Image.open(INPUT_IMAGE) as image:
        original = image.convert("RGB")

    print("\nRunning inference...")

    start = time.perf_counter()

    with torch.inference_mode():
        pred_map = remover.process(original, type="map")

    inference_time = time.perf_counter() - start

    print(f"Inference completed in {inference_time:.2f} seconds")

    # Convert probability map to grayscale
    probability_map = pred_map.convert("L")

    # Normalize alpha values to [0, 1]
    alpha = np.asarray(probability_map, dtype=np.float32) / 255.0

    # Convert to 8-bit alpha channel
    alpha_image = Image.fromarray(
        (alpha * 255).astype(np.uint8),
        mode="L"
    )

    # Generate transparent output
    result = original.copy()
    result.putalpha(alpha_image)

    result.save(OUTPUT_IMAGE, format="PNG")

    print("\nRESULTS")
    print("-" * 55)
    print("Output mode:", result.mode)
    print("Output dimensions:", result.size)
    print("Alpha range:", alpha_image.getextrema())
    print("Output saved:", OUTPUT_IMAGE)
    print("Model loading time:", round(load_time, 2), "seconds")
    print("Inference time:", round(inference_time, 2), "seconds")

    print("\nInSPyReNet CPU SMOKE TEST PASSED")


if __name__ == "__main__":
    main()