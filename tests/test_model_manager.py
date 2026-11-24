from unittest.mock import Mock
import pytest
from app.services.model_interface import ModelInterface
from app.services.model_manager import ModelManager


class DummyModel(ModelInterface):

    def __init__(self):
        self.loaded = False

    def load_model(self):
        self.loaded = True

    def predict_mask(self, image):
        pass


def test_register_model_successfully():
    manager = ModelManager()
    model = DummyModel()

    manager.register_model("birefnet", model)

    assert manager.models["birefnet"] is model


def test_register_model_rejects_empty_id():
    manager = ModelManager()
    model = DummyModel()

    with pytest.raises(ValueError):
        manager.register_model("", model)


def test_register_model_rejects_duplicate_id():
    manager = ModelManager()

    first_model = DummyModel()
    second_model = DummyModel()

    manager.register_model("birefnet", first_model)

    with pytest.raises(ValueError):
        manager.register_model("birefnet", second_model)

    assert manager.models["birefnet"] is first_model


def test_get_model_successfully():
    manager = ModelManager()
    model = DummyModel()

    manager.register_model("birefnet", model)

    result = manager.get_model("birefnet")

    assert result is model


def test_get_model_raises_error_for_unknown_id():
    manager = ModelManager()

    with pytest.raises(KeyError):
        manager.get_model("unknown_model")


def test_list_models():
    manager = ModelManager()

    manager.register_model("birefnet", DummyModel())
    manager.register_model("inspyrenet", DummyModel())

    result = manager.list_models()

    assert result == ["birefnet", "inspyrenet"]


def test_registration_does_not_load_model():
    manager = ModelManager()
    model = DummyModel()

    manager.register_model("birefnet", model)

    assert model.loaded is False