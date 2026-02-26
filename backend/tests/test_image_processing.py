"""Tests for image processing service (line-art conversion)."""

import io
from PIL import Image
import pytest

from app.services.image_processing import image_processing_service


@pytest.fixture
def sample_image_bytes():
    """Create a sample test image."""
    # Create a simple RGB image with some shapes
    img = Image.new("RGB", (200, 200), color="white")
    # Draw a simple black square
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill="black", outline="red", width=3)
    draw.ellipse([75, 75, 125, 125], fill="blue")
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_convert_to_line_art_canny(sample_image_bytes):
    """Test Canny edge detection method."""
    result = await image_processing_service.convert_to_line_art(
        sample_image_bytes,
        method="canny",
        threshold_low=50,
        threshold_high=150,
    )
    
    # Check that we got bytes back
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Check that result is valid PNG
    result_img = Image.open(io.BytesIO(result))
    assert result_img.format == "PNG"
    assert result_img.size == (200, 200)


@pytest.mark.asyncio
async def test_convert_to_line_art_simple(sample_image_bytes):
    """Test simplified line-art for kid-friendly coloring (new defaults)."""
    result = await image_processing_service.convert_to_line_art(
        sample_image_bytes,
        method="canny",
        threshold_low=80,  # Higher = simpler
        threshold_high=200,  # Higher = fewer details
    )
    
    # Check that we got bytes back
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Check that result is valid PNG
    result_img = Image.open(io.BytesIO(result))
    assert result_img.format == "PNG"
    assert result_img.size == (200, 200)
    
    # Simplified version should have less variation (fewer edges)
    # Convert to grayscale for analysis
    pixels = list(result_img.convert("L").getdata())
    black_pixels = sum(1 for p in pixels if p < 128)
    
    # Simplified should have fewer black pixels (less detail)
    assert black_pixels < len(pixels) * 0.3  # Less than 30% black


@pytest.mark.asyncio
async def test_convert_to_line_art_pil_edge(sample_image_bytes):
    """Test PIL edge detection method."""
    result = await image_processing_service.convert_to_line_art(
        sample_image_bytes,
        method="pil_edge",
    )
    
    # Check that we got bytes back
    assert isinstance(result, bytes)
    assert len(result) > 0
    
    # Check that result is valid PNG
    result_img = Image.open(io.BytesIO(result))
    assert result_img.format == "PNG"
    assert result_img.size == (200, 200)


@pytest.mark.asyncio
async def test_convert_to_line_art_invalid_method(sample_image_bytes):
    """Test that invalid method raises error."""
    with pytest.raises(ValueError, match="Unknown line-art method"):
        await image_processing_service.convert_to_line_art(
            sample_image_bytes,
            method="invalid_method",
        )


@pytest.mark.asyncio
async def test_convert_to_line_art_invalid_image():
    """Test that invalid image data raises error."""
    with pytest.raises(Exception):
        await image_processing_service.convert_to_line_art(
            b"not an image",
            method="canny",
        )
