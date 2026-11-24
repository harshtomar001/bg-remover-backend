from PIL import Image
from app.services.model_interface import ModelInterface
from app.services.inspyrenet_service import inspyrenet_service


class InSPyReNetAdapter(ModelInterface):

    def load_model(self) -> None:
        inspyrenet_service.load_model()

    def predict_mask(self, image: Image.Image) -> Image.Image:
        return inspyrenet_service.predict_mask(image)