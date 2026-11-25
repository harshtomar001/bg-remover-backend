from unittest.mock import patch

from app.services.adapters.birefnet_adapter import BiRefNetAdapter
from app.services.adapters.birefnet_hr_adapter import BiRefNetHRAdapter
from app.services.model_manager import ModelManager
from app.services.model_registry import create_model_registry


def test_registry_returns_model_manager():
    manager = create_model_registry()

    assert isinstance(manager, ModelManager)


def test_birefnet_is_registered():
    manager = create_model_registry()

    assert "birefnet" in manager.list_models()


def test_registered_birefnet_is_correct_adapter():
    manager = create_model_registry()

    adapter = manager.get_model("birefnet")

    assert isinstance(adapter, BiRefNetAdapter)


from app.services.adapters.inspyrenet_adapter import InSPyReNetAdapter


def test_inspyrenet_is_registered():
    manager = create_model_registry()

    assert "inspyrenet" in manager.list_models()


def test_inspyrenet_adapter_type():
    manager = create_model_registry()

    model = manager.get_model("inspyrenet")

    assert isinstance(model, InSPyReNetAdapter)


def test_registering_inspyrenet_does_not_load_weights():
    with patch.object(
            InSPyReNetAdapter,
            "load_model"
    ) as mock_load:

        manager = create_model_registry()

        assert "inspyrenet" in manager.list_models()

        mock_load.assert_not_called()


def test_birefnet_hr_is_registered():
    manager = create_model_registry()

    assert "birefnet_hr" in manager.list_models()


def test_birefnet_hr_adapter_type():
    manager = create_model_registry()

    model = manager.get_model("birefnet_hr")

    assert isinstance(model, BiRefNetHRAdapter)


def test_registering_birefnet_hr_does_not_load_weights():
    with patch.object(
            InSPyReNetAdapter,
            "load_model"
    ) as mock_load:

        manager = create_model_registry()

        assert "birefnet_hr" in manager.list_models()

        mock_load.assert_not_called()