from app.services.adapters.birefnet_adapter import BiRefNetAdapter
from app.services.adapters.inspyrenet_adapter import InSPyReNetAdapter
from app.services.model_manager import ModelManager


def create_model_registry() -> ModelManager:
    """
    Create and configure the application's model registry.

    Model adapters are registered here, but their weights
    are not loaded.
    
    """

    manager = ModelManager()

    # Register BiRefNet
    birefnet_adapter = BiRefNetAdapter()
    manager.register_model("birefnet", birefnet_adapter)

    # Register InSPyReNet
    inspyrenet_adapter = InSPyReNetAdapter()
    manager.register_model("inspyrenet", inspyrenet_adapter)

    return manager


# Shared application-level model manager.
model_manager = create_model_registry()