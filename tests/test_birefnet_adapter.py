from unittest.mock import Mock
from PIL import Image
from app.services.adapters.birefnet_adapter import BiRefNetAdapter
from app.services.model_interface import ModelInterface


def test_birefnet_adapter_implements_model_interface():

    adapter = BiRefNetAdapter()
    assert isinstance(adapter, ModelInterface)


def test_load_model_delegates_to_birefnet_service(monkeypatch):
    adapter = BiRefNetAdapter()

    mock_load = Mock()

    monkeypatch.setattr(
        "app.services.adapters.birefnet_adapter.birefnet_service.load_model",
        mock_load,
    )

    adapter.load_model()

    mock_load.assert_called_once()


def test_predict_mask_delegates_to_birefnet_service(monkeypatch):
    adapter = BiRefNetAdapter()

    input_image = Image.new("RGB", (100, 100))
    expected_mask = Image.new("L", (100, 100), 128)

    mock_predict = Mock(return_value = expected_mask)

    monkeypatch.setattr(
        "app.services.adapters.birefnet_adapter.birefnet_service.predict",
        mock_predict,
    )

    result = adapter.predict_mask(input_image)

    mock_predict.assert_called_once_with(input_image)
    assert result is expected_mask


def test_remove_background_uses_inherited_implementation(monkeypatch):
    adapter = BiRefNetAdapter()

    input_image = Image.new("RGB", (100, 100), (255, 0, 0))
    expected_mask = Image.new("L", (100, 100), 128)

    mock_predict = Mock(return_value = expected_mask)

    monkeypatch.setattr(
        "app.services.adapters.birefnet_adapter.birefnet_service.predict",
        mock_predict,
    )

    result = adapter.remove_background(input_image)

    assert result.mode == "RGBA"
    assert result.size == input_image.size
    assert result.getchannel("A").getpixel((50, 50)) == 128
    assert result.getpixel((50, 50))[:3] == (255, 0, 0)
    mock_predict.assert_called_once_with(input_image)