import uuid

import pytest

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from app.api.dependencies import get_current_user


@pytest.fixture
def user():
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.is_active = True
    return mock_user


@pytest.fixture
def mock_image(user):
    image = MagicMock()

    image.id = uuid.uuid4()
    image.user_id = user.id

    image.original_storage_key = (
        f"users/{user.id}/originals/{image.id}.jpg"
    )

    image.processed_storage_key = (
        f"users/{user.id}/processed/{image.id}.png"
    )

    image.content_type = "image/jpeg"

    return image


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def client(db, user):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestImageRetrievalRoutes:

    @patch("app.services.image_service.read_image")
    def test_get_original_image_success(
            self,
            mock_read_image,
            client,
            db,
            mock_image,
    ):
        db.scalar.return_value = mock_image
        mock_read_image.return_value = b"original-image-data"

        response = client.get(
            f"/images/{mock_image.id}/original"
        )

        assert response.status_code == 200
        assert response.content == b"original-image-data"
        assert response.headers["content-type"] == "image/jpeg"

    @patch("app.services.image_service.read_image")
    def test_get_processed_image_success(
            self,
            mock_read_image,
            client,
            db,
            mock_image,
    ):
        db.scalar.return_value = mock_image
        mock_read_image.return_value = b"processed-image-data"

        response = client.get(
            f"/images/{mock_image.id}/processed"
        )

        assert response.status_code == 200
        assert response.content == b"processed-image-data"
        assert response.headers["content-type"] == "image/png"

    def test_image_not_found(
            self,
            client,
            db,
    ):
        db.scalar.return_value = None

        image_id = uuid.uuid4()

        response = client.get(
            f"/images/{image_id}/original"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Image not found."

    def test_invalid_image_uuid(self, client):
        response = client.get(
            "/images/invalid-uuid/original"
        )

        assert response.status_code == 422

    @patch("app.services.image_service.read_image")
    def test_original_file_missing(
            self,
            mock_read_image,
            client,
            db,
            mock_image,
    ):
        db.scalar.return_value = mock_image
        mock_read_image.side_effect = FileNotFoundError

        response = client.get(
            f"/images/{mock_image.id}/original"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Image file not found."

    @patch("app.services.image_service.read_image")
    def test_processed_file_missing(
            self,
            mock_read_image,
            client,
            db,
            mock_image,
    ):
        db.scalar.return_value = mock_image
        mock_read_image.side_effect = FileNotFoundError

        response = client.get(
            f"/images/{mock_image.id}/processed"
        )

        assert response.status_code == 404

    def test_missing_authentication(self, db):
        app.dependency_overrides[get_db] = lambda: db

        try:
            with TestClient(app) as unauthenticated_client:

                response = unauthenticated_client.get(
                    f"/images/{uuid.uuid4()}/original"
                )

            assert response.status_code == 401

        finally:
            app.dependency_overrides.clear()

    @patch("app.services.image_service.read_image")
    def test_another_users_image_returns_404(
            self,
            mock_read_image,
            client,
            db,
            mock_image,
    ):
        # The database query returns no image belonging
        # to the currently authenticated user.
        db.scalar.return_value = None

        response = client.get(
            f"/images/{mock_image.id}/original"
        )

        assert response.status_code == 404
        mock_read_image.assert_not_called()