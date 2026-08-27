import io
from pathlib import Path

import pytest
from PIL import Image

from core.watermark import apply_watermark, PREVIEW_MAX_SIZE


def _make_jpeg(path: Path, width: int = 200, height: int = 150) -> None:
    Image.new("RGB", (width, height), color=(100, 150, 200)).save(path, "JPEG")


def test_returns_bytes_for_valid_image(tmp_path):
    photo = tmp_path / "photo.jpg"
    _make_jpeg(photo)
    result = apply_watermark(photo)
    assert result is not None
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_result_is_valid_jpeg(tmp_path):
    photo = tmp_path / "photo.jpg"
    _make_jpeg(photo)
    result = apply_watermark(photo)
    assert result is not None
    img = Image.open(io.BytesIO(result))
    assert img.format == "JPEG"


def test_resizes_large_image(tmp_path):
    photo = tmp_path / "big.jpg"
    _make_jpeg(photo, width=3000, height=2000)
    result = apply_watermark(photo)
    assert result is not None
    img = Image.open(io.BytesIO(result))
    assert img.width <= PREVIEW_MAX_SIZE[0]
    assert img.height <= PREVIEW_MAX_SIZE[1]


def test_preserves_small_image_dimensions(tmp_path):
    photo = tmp_path / "small.jpg"
    _make_jpeg(photo, width=100, height=80)
    result = apply_watermark(photo)
    assert result is not None
    img = Image.open(io.BytesIO(result))
    assert img.width == 100
    assert img.height == 80


def test_nonexistent_file_returns_none():
    result = apply_watermark(Path("/nonexistent/photo.jpg"))
    assert result is None
