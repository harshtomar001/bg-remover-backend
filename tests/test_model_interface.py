import pytest
from PIL import Image

from app.services.model_interface import ModelInterface


class DummyModel(ModelInterface):

    def __init__(self, mask):
        self.mask = mask

    def load_model(self):
        pass

    def predict_mask(self, image):
        return self.mask


def test_abstract_interface_cannot_be_instantiated():

    with pytest.raises(TypeError):
        ModelInterface()


def test_remove_background_returns_rgba():

    original = Image.new("RGB", (100, 100), (255, 0, 0))
    mask = Image.new("L", (100, 100), 255)

    model = DummyModel(mask)

    result = model.remove_background(original)

    assert result.mode == "RGBA"


def test_output_dimensions_match_original():

    original = Image.new("RGB", (100, 80), (255, 0, 0))
    mask = Image.new("L", (100, 80), 255)

    model = DummyModel(mask)

    result = model.remove_background(original)

    assert result.size == original.size


def test_mask_is_applied_as_alpha_channel():

    original = Image.new("RGB", (100, 100), (255, 0, 0))
    mask = Image.new("L", (100, 100), 128)

    model = DummyModel(mask)

    result = model.remove_background(original)

    alpha = result.getchannel("A")

    assert alpha.getpixel((50, 50)) == 128


def test_original_rgb_pixels_are_preserved():

    original = Image.new("RGB", (100, 100), (255, 0, 0))
    mask = Image.new("L", (100, 100), 255)

    model = DummyModel(mask)

    result = model.remove_background(original)

    assert result.getpixel((50, 50))[:3] == (255, 0, 0)


def test_mask_is_resized_to_original_dimensions():

    original = Image.new("RGB", (100, 100), (255, 0, 0))
    mask = Image.new("L", (50, 50), 255)

    model = DummyModel(mask)

    result = model.remove_background(original)

    assert result.size == original.size
    assert result.mode == "RGBA"


def test_non_grayscale_mask_is_converted():

    original = Image.new("RGB", (100, 100), (255, 0, 0))
    mask = Image.new("RGB", (100, 100), (128, 128, 128))

    model = DummyModel(mask)

    result = model.remove_background(original)

    assert result.mode == "RGBA"
    assert result.getchannel("A").mode == "L"