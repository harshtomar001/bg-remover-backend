from PIL import Image

from app.services.model_interface import ModelInterface
from app.services.birefnet_service import birefnet_service


class BiRefNetAdapter(ModelInterface):

    def load_model(self) -> None:
        birefnet_service.load_model()

    def predict_mask(self, image: Image.Image) -> Image.Image:
        return birefnet_service.predict(image)