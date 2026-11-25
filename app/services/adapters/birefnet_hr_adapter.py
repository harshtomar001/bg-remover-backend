from PIL import Image

from app.services.model_interface import ModelInterface
from app.services.birefnet_hr_service import birefnet_hr_service


class BiRefNetHRAdapter(ModelInterface):

    def load_model(self):
        birefnet_hr_service.load_model()

    def predict_mask(self, image: Image.Image) -> Image.Image:
        return birefnet_hr_service.predict_mask(image)