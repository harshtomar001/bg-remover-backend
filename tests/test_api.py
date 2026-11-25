from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app
from app.services.birefnet_service import birefnet_service
from app.services.model_registry import model_manager


client = TestClient(app)


def create_test_image(format="PNG"):
    image = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_empty_upload():
    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("empty.png", b"", "image/png")}
    )

    assert response.status_code == 400


def test_invalid_image():
    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("invalid.png", b"not an image", "image/png")}
    )

    assert response.status_code == 400


def test_unsupported_image_format():
    bmp_image = create_test_image("BMP")

    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("image.bmp", bmp_image, "image/bmp")}
    )

    assert response.status_code == 415


def test_file_size_limit():
    
    large_file = b"x" * (15 * 1024 * 1024 + 1)

    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("large.png", large_file, "image/png")}
    )

    assert response.status_code == 413


def test_successful_background_removal(monkeypatch):

    def mock_remove_background(image):
        return image.convert("RGBA")

    model = model_manager.get_model("birefnet")

    monkeypatch.setattr(
        model,
        "remove_background",
        mock_remove_background
    )

    test_image = create_test_image()

    response = client.post(
        "/api/v1/remove-background",
        files={"file": ("test.png", test_image, "image/png")}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    output_image = Image.open(BytesIO(response.content))

    assert output_image.format == "PNG"
    assert output_image.mode == "RGBA"