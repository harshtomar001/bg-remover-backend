import time
from pathlib import Path

import pytest
from PIL import Image

from app.services.birefnet_service import birefnet_service


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_IMAGE = Path(__file__).resolve().parents[1] / "mock_images" / "test_input.png"


@pytest.fixture(scope="module")
def inference_result():

    assert INPUT_IMAGE.exists(), f"Image not found: {INPUT_IMAGE}"

    print("\nLoading BiRefNet...")
    birefnet_service.load_model()

    with Image.open(INPUT_IMAGE) as image:
        original = image.copy()

    print("Running actual inference...")

    start = time.perf_counter()

    result = birefnet_service.remove_background(original)

    inference_time = time.perf_counter() - start

    return original, result, inference_time


def test_output_dimensions(inference_result):

    original, result, _ = inference_result

    assert result.size == original.size


def test_output_mode(inference_result):

    _, result, _ = inference_result

    assert result.mode == "RGBA"


def test_alpha_range(inference_result):

    _, result, _ = inference_result

    alpha = result.getchannel("A")

    minimum, maximum = alpha.getextrema()

    assert minimum >= 0
    assert maximum <= 255


def test_foreground_exists(inference_result):

    _, result, _ = inference_result

    alpha = result.getchannel("A")

    histogram = alpha.histogram()

    foreground_pixels = sum(histogram[11:])

    assert foreground_pixels > 0


def test_transparent_background_exists(inference_result):

    _, result, _ = inference_result

    alpha = result.getchannel("A")

    histogram = alpha.histogram()

    transparent_pixels = sum(histogram[:11])

    assert transparent_pixels > 0


def test_inference_time(inference_result):

    _, _, inference_time = inference_result

    print(f"\nCPU inference time: {inference_time:.2f} seconds")

    assert inference_time > 0