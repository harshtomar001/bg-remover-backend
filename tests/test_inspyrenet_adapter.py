from unittest.mock import patch
from PIL import Image
from app.services.adapters.inspyrenet_adapter import InSPyReNetAdapter
from app.services.model_interface import ModelInterface


def test_adapter_implements_model_interface():
    adapter = InSPyReNetAdapter()

    assert isinstance(adapter, ModelInterface)


def test_load_model_delegates_to_service():

    adapter = InSPyReNetAdapter()

    with patch(
            "app.services.adapters.inspyrenet_adapter.inspyrenet_service.load_model"
    ) as mock_load:

        adapter.load_model()

        mock_load.assert_called_once()


def test_predict_mask_delegates_to_service():

    adapter = InSPyReNetAdapter()

    image = Image.new("RGB", (100, 100))
    expected_mask = Image.new("L", (100, 100), 128)

    with patch(
            "app.services.adapters.inspyrenet_adapter.inspyrenet_service.predict_mask",
            return_value=expected_mask
    ) as mock_predict:

        result = adapter.predict_mask(image)

        mock_predict.assert_called_once_with(image)

        assert result is expected_mask


def test_inherited_remove_background():

    adapter = InSPyReNetAdapter()

    image = Image.new("RGB", (100, 100), (255, 0, 0))
    expected_mask = Image.new("L", (100, 100), 128)

    with patch.object(
            adapter,
            "predict_mask",
            return_value=expected_mask
    ):

        result = adapter.remove_background(image)

    assert result.mode == "RGBA"
    assert result.size == image.size
    assert result.getpixel((0, 0))[3] == 128
    assert result.getpixel((0, 0))[:3] == (255, 0, 0)