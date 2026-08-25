import io
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

WATERMARK_TEXT = "© CCI Fotos"
PREVIEW_MAX_SIZE = (1280, 1280)
PREVIEW_QUALITY = 85


def _load_font(size: int) -> ImageFont.ImageFont:
    for font_name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def apply_watermark(source_path: Path) -> bytes | None:
    """
    Gera uma cópia redimensionada de `source_path` com marca d'água.
    Retorna os bytes JPEG resultantes, ou None em falha (sem lançar exceção).
    """
    try:
        with Image.open(source_path) as img:
            img = img.convert("RGBA")
            img.thumbnail(PREVIEW_MAX_SIZE, Image.LANCZOS)

            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = _load_font(size=max(18, img.width // 28))

            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            margin = 18
            x = img.width - text_w - margin
            y = img.height - text_h - margin

            # sombra + texto principal para legibilidade em fundos claros e escuros
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 140))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 190))

            result = Image.alpha_composite(img, overlay).convert("RGB")
            buf = io.BytesIO()
            result.save(buf, "JPEG", quality=PREVIEW_QUALITY)
            return buf.getvalue()

    except Exception:
        logger.exception("watermark_failed source=%s", source_path)
        return None
