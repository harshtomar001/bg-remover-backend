import uuid
import pytest

from unittest.mock import MagicMock, patch

from app.services.image_service import get_user_image_file


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def user_id():
    return uuid.uuid4()


@pytest.fixture
def image_id():
    return uuid.uuid4()


@pytest.fixture
def mock_image(user_id, image_id):
    image = MagicMock()

    image.id = image_id
    image.user_id = user_id

    image.original_storage_key = (
        f"users/{user_id}/originals/{image_id}.jpg"
    )

    image.processed_storage_key = (
        f"users/{user_id}/processed/{image_id}.png"
    )

    image.content_type = "image/jpeg"

    return image


class TestGetUserImageFile:

    @patch("app.services.image_service.read_image")
    @patch("app.services.image_service.get_user_image")
    def test_get_original_image_success(
            self,
            mock_get_user_image,
            mock_read_image,
            mock_db,
            user_id,
            image_id,
            mock_image,
    ):

        mock_get_user_image.return_value = mock_image
        mock_read_image.return_value = b"original-image-data"

        result = get_user_image_file(
            db=mock_db,
            user_id=user_id,
            image_id=image_id,
            variant="original",
        )

        assert result == (
            b"original-image-data",
            "image/jpeg",
        )

        mock_get_user_image.assert_called_once_with(
            mock_db,
            user_id,
            image_id,
        )

        mock_read_image.assert_called_once_with(
            mock_image.original_storage_key
        )

    @patch("app.services.image_service.read_image")
    @patch("app.services.image_service.get_user_image")
    def test_get_processed_image_success(
            self,
            mock_get_user_image,
            mock_read_image,
            mock_db,
            user_id,
            image_id,
            mock_image,
    ):

        mock_get_user_image.return_value = mock_image
        mock_read_image.return_value = b"processed-image-data"

        result = get_user_image_file(
            db=mock_db,
            user_id=user_id,
            image_id=image_id,
            variant="processed",
        )

        assert result == (
            b"processed-image-data",
            "image/png",
        )

        mock_read_image.assert_called_once_with(
            mock_image.processed_storage_key
        )

    @patch("app.services.image_service.read_image")
    @patch("app.services.image_service.get_user_image")
    def test_image_not_owned_or_not_found(
            self,
            mock_get_user_image,
            mock_read_image,
            mock_db,
            user_id,
            image_id,
    ):

        mock_get_user_image.return_value = None

        result = get_user_image_file(
            db=mock_db,
            user_id=user_id,
            image_id=image_id,
            variant="original",
        )

        assert result is None

        mock_read_image.assert_not_called()

    @patch("app.services.image_service.get_user_image")
    def test_invalid_variant(
            self,
            mock_get_user_image,
            mock_db,
            user_id,
            image_id,
    ):

        with pytest.raises(ValueError):
            get_user_image_file(
                db=mock_db,
                user_id=user_id,
                image_id=image_id,
                variant="thumbnail",
            )

        mock_get_user_image.assert_not_called()

    @patch("app.services.image_service.read_image")
    @patch("app.services.image_service.get_user_image")
    def test_processed_image_missing_storage_key(
            self,
            mock_get_user_image,
            mock_read_image,
            mock_db,
            user_id,
            image_id,
            mock_image,
    ):

        mock_image.processed_storage_key = None
        mock_get_user_image.return_value = mock_image

        with pytest.raises(FileNotFoundError):
            get_user_image_file(
                db=mock_db,
                user_id=user_id,
                image_id=image_id,
                variant="processed",
            )

        mock_read_image.assert_not_called()

    @patch("app.services.image_service.read_image")
    @patch("app.services.image_service.get_user_image")
    def test_storage_file_missing(
            self,
            mock_get_user_image,
            mock_read_image,
            mock_db,
            user_id,
            image_id,
            mock_image,
    ):

        mock_get_user_image.return_value = mock_image
        mock_read_image.side_effect = FileNotFoundError

        with pytest.raises(FileNotFoundError):
            get_user_image_file(
                db=mock_db,
                user_id=user_id,
                image_id=image_id,
                variant="original",
            )