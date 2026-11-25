from unittest.mock import MagicMock

import pytest
import torch
from PIL import Image

from app.services.birefnet_hr_service import (
    BiRefNetHRService,
    birefnet_hr_service,
)


def test_service_initially_has_no_model():
    service = BiRefNetHRService()

    assert service.model is None


def test_load_model_uses_cpu(monkeypatch):
    service = BiRefNetHRService()

    mock_model = MagicMock()

    def mock_from_pretrained(*args, **kwargs):
        return mock_model

    monkeypatch.setattr(
        "app.services.birefnet_hr_service.AutoModelForImageSegmentation.from_pretrained",
        mock_from_pretrained,
    )

    service.load_model()

    assert service.model is mock_model

    mock_model.to.assert_called_once_with(torch.device("cpu"))
    mock_model.eval.assert_called_once()


def test_load_model_does_not_load_twice(monkeypatch):
    service = BiRefNetHRService()

    mock_model = MagicMock()

    mock_loader = MagicMock(return_value=mock_model)

    monkeypatch.setattr(
        "app.services.birefnet_hr_service.AutoModelForImageSegmentation.from_pretrained",
        mock_loader,
    )

    service.load_model()
    service.load_model()

    assert mock_loader.call_count == 1


def test_load_model_raises_if_checkpoint_missing(monkeypatch, tmp_path):
    service = BiRefNetHRService()

    missing_directory = tmp_path / "missing_model"

    monkeypatch.setattr(
        "app.services.birefnet_hr_service.MODEL_DIR",
        missing_directory,
    )

    with pytest.raises(FileNotFoundError):
        service.load_model()


def test_predict_mask_requires_loaded_model():
    service = BiRefNetHRService()

    image = Image.new("RGB", (100, 100))

    with pytest.raises(RuntimeError):
        service.predict_mask(image)


def test_predict_mask_returns_grayscale_image():
    service = BiRefNetHRService()

    mock_model = MagicMock()

    mock_model.return_value = [
        torch.zeros((1, 1, 2, 2))
    ]

    service.model = mock_model

    image = Image.new("RGB", (100, 80), "red")

    result = service.predict_mask(image)

    assert isinstance(result, Image.Image)
    assert result.mode == "L"


def test_predict_mask_resizes_to_original_dimensions():
    service = BiRefNetHRService()

    mock_model = MagicMock()

    mock_model.return_value = [
        torch.zeros((1, 1, 2, 2))
    ]

    service.model = mock_model

    image = Image.new("RGB", (320, 240))

    result = service.predict_mask(image)

    assert result.size == (320, 240)


def test_predict_mask_preserves_continuous_alpha_values():
    service = BiRefNetHRService()

    mock_model = MagicMock()

    mock_model.return_value = [
        torch.tensor(
            [[[
                [-2.0, -1.0],
                [1.0, 2.0]
            ]]]
        )
    ]

    service.model = mock_model

    image = Image.new("RGB", (100, 100))

    result = service.predict_mask(image)

    assert result.mode == "L"

    minimum, maximum = result.getextrema()

    assert minimum < maximum