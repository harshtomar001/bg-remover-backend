import io
import uuid
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from app.api.routes import remove_background as route_module
from app.api.dependencies import get_optional_current_user
from app.db.database import get_db


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def create_image_bytes(image_format="PNG"):
    buffer = io.BytesIO()

    image = Image.new(
        "RGB",
        (32, 32),
        color=(120, 150, 200),
    )

    image.save(buffer, format=image_format)

    return buffer.getvalue()


class FakeModel:

    def remove_background(self, image):

        return Image.new(
            "RGBA",
            image.size,
            color=(255, 0, 0, 128),
        )


# --------------------------------------------------
# Fixtures
# --------------------------------------------------

@pytest.fixture
def test_app():

    app = FastAPI()

    app.include_router(
        route_module.router,
        prefix="/api/v1",
    )

    # Default: guest user
    app.dependency_overrides[get_optional_current_user] = (
        lambda: None
    )

    # Avoid connecting to the real database
    app.dependency_overrides[get_db] = (
        lambda: object()
    )

    yield app

    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app):

    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture
def fake_model(monkeypatch):

    model = FakeModel()

    monkeypatch.setattr(
        route_module.model_manager,
        "get_model",
        lambda name: model,
    )

    return model


@pytest.fixture
def fake_user():

    return SimpleNamespace(
        id=uuid.uuid4(),
        is_active=True,
    )


# --------------------------------------------------
# 1. Guest Processing Tests
# --------------------------------------------------

@pytest.mark.parametrize(
    "image_format,filename,content_type",
    [
        ("PNG", "input.png", "image/png"),
        ("JPEG", "input.jpg", "image/jpeg"),
        ("WEBP", "input.webp", "image/webp"),
    ],
)
def test_guest_can_process_supported_images(
        client,
        fake_model,
        monkeypatch,
        image_format,
        filename,
        content_type,
):

    persistence_mock = Mock()

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        persistence_mock,
    )

    image_bytes = create_image_bytes(image_format)

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                filename,
                image_bytes,
                content_type,
            )
        },
    )

    assert response.status_code == 200

    assert response.headers["content-type"] == "image/png"

    assert "X-Image-ID" not in response.headers

    # Guest images must not be permanently saved.
    persistence_mock.assert_not_called()

    # Verify that the returned content is a valid PNG.
    result = Image.open(
        io.BytesIO(response.content)
    )

    assert result.format == "PNG"
    assert result.mode == "RGBA"


# --------------------------------------------------
# 2. Authenticated Processing Tests
# --------------------------------------------------

def test_authenticated_user_can_process_image(
        client,
        test_app,
        fake_model,
        fake_user,
        monkeypatch,
):

    test_app.dependency_overrides[
        get_optional_current_user
    ] = lambda: fake_user

    saved_image_id = uuid.uuid4()

    saved_image = SimpleNamespace(
        id=saved_image_id,
    )

    persistence_mock = Mock(
        return_value=saved_image
    )

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        persistence_mock,
    )

    original_bytes = create_image_bytes("PNG")

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "original.png",
                original_bytes,
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    assert response.headers["content-type"] == "image/png"

    assert response.headers["X-Image-ID"] == str(
        saved_image_id
    )

    persistence_mock.assert_called_once()

    args = persistence_mock.call_args.args

    # Verify persistence arguments.
    assert args[1] == fake_user.id
    assert args[2] == "original.png"
    assert args[3] == original_bytes
    assert args[5] == "image/png"
    assert args[6] == "birefnet"

    # Verify processed output is valid PNG.
    processed_image = Image.open(
        io.BytesIO(args[4])
    )

    assert processed_image.format == "PNG"
    assert processed_image.mode == "RGBA"


def test_authenticated_user_receives_image_id(
        client,
        test_app,
        fake_model,
        fake_user,
        monkeypatch,
):

    test_app.dependency_overrides[
        get_optional_current_user
    ] = lambda: fake_user

    image_id = uuid.uuid4()

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        Mock(
            return_value=SimpleNamespace(id=image_id)
        ),
    )

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "input.png",
                create_image_bytes(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Image-ID"] == str(image_id)


# --------------------------------------------------
# 3. Input Validation Tests
# --------------------------------------------------

def test_empty_file_returns_400(client, fake_model):

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "empty.png",
                b"",
                "image/png",
            )
        },
    )

    assert response.status_code == 400


def test_invalid_image_returns_400(client, fake_model):

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "invalid.png",
                b"this is not an image",
                "image/png",
            )
        },
    )

    assert response.status_code == 400


def test_unsupported_image_format_returns_415(
        client,
        fake_model,
):

    bmp_bytes = create_image_bytes("BMP")

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "input.bmp",
                bmp_bytes,
                "image/bmp",
            )
        },
    )

    assert response.status_code == 415


def test_file_exceeding_15mb_returns_413(
        client,
        fake_model,
):

    oversized_data = b"x" * (
            route_module.MAX_FILE_SIZE + 1
    )

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "large.png",
                oversized_data,
                "image/png",
            )
        },
    )

    assert response.status_code == 413


def test_corrupted_image_returns_400(
        client,
        fake_model,
):

    valid_image = create_image_bytes("PNG")

    # Truncate the PNG data.
    corrupted_image = valid_image[:30]

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "corrupted.png",
                corrupted_image,
                "image/png",
            )
        },
    )

    assert response.status_code == 400


# --------------------------------------------------
# 4. Inference Failure Tests
# --------------------------------------------------

def test_inference_failure_returns_500(
        client,
        monkeypatch,
):

    class BrokenModel:

        def remove_background(self, image):
            raise RuntimeError("Inference failed")

    monkeypatch.setattr(
        route_module.model_manager,
        "get_model",
        lambda name: BrokenModel(),
    )

    persistence_mock = Mock()

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        persistence_mock,
    )

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "input.png",
                create_image_bytes(),
                "image/png",
            )
        },
    )

    assert response.status_code == 500

    persistence_mock.assert_not_called()


# --------------------------------------------------
# 5. Persistence Failure Tests
# --------------------------------------------------

def test_persistence_failure_returns_500(
        client,
        test_app,
        fake_model,
        fake_user,
        monkeypatch,
):

    test_app.dependency_overrides[
        get_optional_current_user
    ] = lambda: fake_user

    persistence_mock = Mock(
        side_effect=RuntimeError(
            "Database persistence failed"
        )
    )

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        persistence_mock,
    )

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "input.png",
                create_image_bytes(),
                "image/png",
            )
        },
    )

    assert response.status_code == 500

    persistence_mock.assert_called_once()


# --------------------------------------------------
# 6. Guest Persistence Isolation
# --------------------------------------------------

def test_guest_processing_never_persists_image(
        client,
        fake_model,
        monkeypatch,
):

    persistence_mock = Mock()

    monkeypatch.setattr(
        route_module,
        "save_completed_image",
        persistence_mock,
    )

    response = client.post(
        "/api/v1/remove-background",
        files={
            "file": (
                "guest.png",
                create_image_bytes(),
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    persistence_mock.assert_not_called()

    assert "X-Image-ID" not in response.headers