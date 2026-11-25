import pytest
from PIL import Image

from app.services.model_interface import ModelInterface
from app.services.adapters.birefnet_hr_adapter import BiRefNetHRAdapter
from app.services.birefnet_hr_service import birefnet_hr_service


def test_adapter_implements_model_interface():
    adapter = BiRefNetHRAdapter()

    assert isinstance(adapter, ModelInterface)


def test_load_model_delegates_to_service(monkeypatch):
    adapter = BiRefNetHRAdapter()

    called = {"value": False}

    def mock_load_model():
        called["value"] = True

    monkeypatch.setattr(
        birefnet_hr_service,
        "load_model",
        mock_load_model
    )

    adapter.load_model()

    assert called["value"] is True


def test_predict_mask_delegates_to_service(monkeypatch):
    adapter = BiRefNetHRAdapter()

    expected_mask = Image.new("L", (100, 100), 255)

    def mock_predict_mask(image):
        return expected_mask

    monkeypatch.setattr(
        birefnet_hr_service,
        "predict_mask",
        mock_predict_mask
    )

    input_image = Image.new("RGB", (100, 100))

    result = adapter.predict_mask(input_image)

    assert result is expected_mask


def test_inherited_remove_background(monkeypatch):
    adapter = BiRefNetHRAdapter()

    expected_mask = Image.new("L", (100, 100), 128)

    monkeypatch.setattr(
        birefnet_hr_service,
        "predict_mask",
        lambda image: expected_mask
    )

    input_image = Image.new("RGB", (100, 100), "red")

    result = adapter.remove_background(input_image)

    assert result.mode == "RGBA"
    assert result.size == input_image.size
    assert result.getchannel("A").getpixel((0, 0)) == 128