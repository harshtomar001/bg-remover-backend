import pytest

from PIL import Image

from app.services.image_analyzer import ImageAnalyzer


@pytest.fixture
def analyzer():
    return ImageAnalyzer()


def test_analyzer_returns_expected_features(analyzer):

    image = Image.new("RGB", (400, 300), color="red")

    result = analyzer.analyze(image)

    expected_keys = {
        "width",
        "height",
        "aspect_ratio",
        "total_pixels",
        "brightness",
        "contrast",
        "color_variance",
        "entropy",
        "edge_density",
    }

    assert set(result.keys()) == expected_keys


def test_image_dimensions(analyzer):

    image = Image.new("RGB", (800, 600), color="blue")

    result = analyzer.analyze(image)

    assert result["width"] == 800
    assert result["height"] == 600
    assert result["total_pixels"] == 480000


def test_aspect_ratio(analyzer):

    image = Image.new("RGB", (800, 400), color="white")

    result = analyzer.analyze(image)

    assert result["aspect_ratio"] == 2.0


def test_uniform_image_has_zero_contrast(analyzer):

    image = Image.new("RGB", (256, 256), color="white")

    result = analyzer.analyze(image)

    assert result["contrast"] == 0.0
    assert result["entropy"] == 0.0


def test_brightness_range(analyzer):

    image = Image.new("RGB", (256, 256), color="white")

    result = analyzer.analyze(image)

    assert 0.0 <= result["brightness"] <= 1.0


def test_edge_density_range(analyzer):

    image = Image.new("RGB", (256, 256), color="red")

    result = analyzer.analyze(image)

    assert 0.0 <= result["edge_density"] <= 1.0


def test_invalid_input(analyzer):

    with pytest.raises(TypeError):

        analyzer.analyze("not an image")


def test_color_image(analyzer):

    image = Image.new("RGB", (256, 256), color=(255, 0, 0))

    result = analyzer.analyze(image)

    assert result["color_variance"] >= 0.0