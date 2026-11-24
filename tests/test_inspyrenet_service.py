from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
from app.services.inspyrenet_service import InSPyReNetService


@pytest.fixture
def service():
    return InSPyReNetService()


def test_service_initially_has_no_model(service):
    assert service.model is None


def test_load_model_uses_cpu(service):
    mock_remover = MagicMock()

    with patch(
            "app.services.inspyrenet_service.Remover",
            return_value = mock_remover
    ) as mock_constructor:

        with patch(
                "app.services.inspyrenet_service.MODEL_CHECKPOINT"
        ) as mock_checkpoint:

            mock_checkpoint.exists.return_value = True

            service.load_model()

            mock_constructor.assert_called_once_with(
                mode="base",
                device="cpu",
                ckpt=str(mock_checkpoint)
            )

    assert service.model is mock_remover


def test_load_model_does_not_load_twice(service):
    mock_remover = MagicMock()
    service.model = mock_remover

    with patch(
            "app.services.inspyrenet_service.Remover"
    ) as mock_constructor:

        service.load_model()

        mock_constructor.assert_not_called()


def test_load_model_raises_if_checkpoint_missing(service):

    with patch(
            "app.services.inspyrenet_service.MODEL_CHECKPOINT"
    ) as mock_checkpoint:

        mock_checkpoint.exists.return_value = False

        with pytest.raises(FileNotFoundError):
            service.load_model()


def test_predict_mask_requires_loaded_model(service):

    image = Image.new("RGB", (100, 100))

    with pytest.raises(RuntimeError):
        service.predict_mask(image)


def test_predict_mask_returns_grayscale_image(service):

    mock_remover = MagicMock()

    mock_remover.process.return_value = Image.new(
        "L",
        (100, 100),
        color=128
    )

    service.model = mock_remover

    image = Image.new("RGB", (100, 100))

    mask = service.predict_mask(image)

    assert isinstance(mask, Image.Image)
    assert mask.mode == "L"
    assert mask.size == (100, 100)


def test_predict_mask_preserves_continuous_alpha_values(service):

    mock_remover = MagicMock()

    mock_remover.process.return_value = Image.new(
        "L",
        (100, 100),
        color=128
    )

    service.model = mock_remover

    image = Image.new("RGB", (100, 100))

    mask = service.predict_mask(image)

    assert mask.getpixel((0, 0)) == 128


def test_predict_mask_resizes_to_original_dimensions(service):

    mock_remover = MagicMock()

    mock_remover.process.return_value = Image.new(
        "L",
        (50, 50),
        color=200
    )

    service.model = mock_remover

    image = Image.new("RGB", (100, 80))

    mask = service.predict_mask(image)

    assert mask.size == (100, 80)


def test_predict_mask_calls_inspyrenet_process(service):

    mock_remover = MagicMock()

    mock_remover.process.return_value = Image.new(
        "L",
        (100, 100),
        color=180
    )

    service.model = mock_remover

    image = Image.new("RGB", (100, 100))

    service.predict_mask(image)

    mock_remover.process.assert_called_once()

    args, kwargs = mock_remover.process.call_args

    assert args[0].mode == "RGB"
    assert kwargs["type"] == "map"