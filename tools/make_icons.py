"""앱 설치용 아이콘(icons/*.png)을 만든다: 주황 바탕에 흰 P, 아래에 찾기 돋보기. Pillow 필요."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent.parent / "icons"
ORANGE, DARK, WHITE = (232, 103, 60), (31, 34, 39), (255, 255, 255)


def draw(size: int, maskable: bool) -> Image.Image:
    im = Image.new("RGBA", (size, size), DARK if maskable else (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = int(size * (0.16 if maskable else 0.04))           # maskable 은 가운데 80% 안전 영역에 맞춤
    box = (pad, pad, size - pad, size - pad)
    d.rounded_rectangle(box, radius=int((size - 2 * pad) * 0.22), fill=ORANGE)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", int((size - 2 * pad) * 0.62))
    w = box[2] - box[0]
    d.text((box[0] + w * 0.44, box[1] + w * 0.47), "P", font=font, fill=WHITE, anchor="mm")
    # 돋보기 (오른쪽 아래)
    r = w * 0.13; cx, cy = box[0] + w * 0.70, box[1] + w * 0.70; lw = max(2, int(w * 0.05))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=WHITE, width=lw)
    d.line((cx + r * 0.7, cy + r * 0.7, cx + r * 1.7, cy + r * 1.7), fill=WHITE, width=lw)
    return im


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for name, size, mask in [("icon-192.png", 192, False), ("icon-512.png", 512, False),
                             ("icon-maskable-512.png", 512, True), ("apple-touch-icon.png", 180, True)]:
        draw(size, mask).convert("RGBA").save(OUT / name)
        print(name)


if __name__ == "__main__":
    main()
