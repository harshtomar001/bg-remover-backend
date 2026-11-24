import time
from pathlib import Path

from PIL import Image

from app.services.model_registry import create_model_registry


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_IMAGE = BASE_DIR / "test_input.png"
OUTPUT_IMAGE = BASE_DIR / "inspyrenet_adapter_test_output.png"


def test_inspyrenet_real_inference_through_model_manager():

    assert INPUT_IMAGE.exists(), "Input image missing"

    manager = create_model_registry()

    # Retrieve InSPyReNet through ModelManager
    model = manager.get_model("inspyrenet")

    # Load the actual model
    start = time.perf_counter()
    model.load_model()
    load_time = time.perf_counter() - start

    # Read input image
    with Image.open(INPUT_IMAGE) as image:
        original = image.convert("RGB")

    # Run background removal through ModelInterface
    start = time.perf_counter()
    result = model.remove_background(original)
    inference_time = time.perf_counter() - start

    # Validate output
    assert result.mode == "RGBA"
    assert result.size == original.size

    alpha = result.getchannel("A")

    assert alpha.getextrema()[0] < 255
    assert alpha.getextrema()[1] > 0

    result.save(OUTPUT_IMAGE, format="PNG")

    print("\nInSPyReNet Integration Results")
    print("-" * 45)
    print("Output mode:", result.mode)
    print("Output dimensions:", result.size)
    print("Alpha range:", alpha.getextrema())
    print("Model loading time:", round(load_time, 2), "seconds")
    print("Inference time:", round(inference_time, 2), "seconds")
    print("Output saved:", OUTPUT_IMAGE)