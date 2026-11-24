from typing import Dict
from app.services.model_interface import ModelInterface


class ModelManager:

    def __init__(self):
        self.models: Dict[str, ModelInterface] = {}

    def register_model(self, model_id: str, model: ModelInterface) -> None:

        if not model_id:
            raise ValueError("Model ID cannot be empty.")

        if model_id in self.models:
            raise ValueError(f"Model '{model_id}' is already registered.")

        self.models[model_id] = model

    def get_model(self, model_id: str) -> ModelInterface:

        if model_id not in self.models:
            raise KeyError(f"Model '{model_id}' is not registered.")

        return self.models[model_id]

    def list_models(self) -> list[str]:
        
        return list(self.models.keys())