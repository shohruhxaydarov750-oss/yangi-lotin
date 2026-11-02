"""Regenerate the bundled Windows icon with Pillow (build-time only)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    # Supersampling keeps the two dots and the ring clear at 16–32 pixels.
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (16, 16, 1008, 1008), radius=224, fill=(36, 107, 254, 255)
    )
    draw.ellipse((279, 344, 745, 842), outline=(255, 255, 255, 255), width=112)
    draw.ellipse((344, 177, 456, 289), fill=(173, 246, 224, 255))
    draw.ellipse((568, 177, 680, 289), fill=(173, 246, 224, 255))

    icon = canvas.resize((256, 256), Image.Resampling.LANCZOS)
    destination = Path(__file__).with_name("YangiLotin.ico")
    icon.save(
        destination,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(destination)


if __name__ == "__main__":
    main()
