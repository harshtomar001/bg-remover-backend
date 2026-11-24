from pathlib import Path

from PIL import Image

from app.services.birefnet_service import birefnet_service


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_IMAGE = BASE_DIR / "test_input.png"
OUTPUT_IMAGE = BASE_DIR / "service_test_output.png"


def main():
    print("Testing BiRefNet background removal...")

    if not INPUT_IMAGE.exists():
        raise FileNotFoundError(
            f"Input image not found: {INPUT_IMAGE}"
        )

    # Load the model.
    birefnet_service.load_model()

    # Read the input image.
    with Image.open(INPUT_IMAGE) as image:
        original_image = image.copy()

    print("Running background removal...")

    # Generate the transparent image.
    result = birefnet_service.remove_background(original_image)

    # Save the result.
    result.save(OUTPUT_IMAGE, format="PNG")

    print("Background removal successful!")
    print("Output mode:", result.mode)
    print("Output size:", result.size)
    print("Output saved to:", OUTPUT_IMAGE)


if __name__ == "__main__":
    main()