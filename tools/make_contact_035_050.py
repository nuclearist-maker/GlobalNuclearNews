from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "qa" / "theory" / "contact_035_050_v2.jpg"
thumb = (400, 225)
canvas = Image.new("RGB", (thumb[0] * 3, thumb[1] * 16), "#071728")
draw = ImageDraw.Draw(canvas)

for row, n in enumerate(range(35, 51)):
    num = f"{n:03d}"
    series = "series-02" if n <= 40 else "series-03"
    base = ROOT / "assets" / "images" / "theory" / series
    paths = [
        base / f"{num}-thumbnail-v2.png",
        base / "hybrid-v2" / f"{num}-body-01.png",
        base / "hybrid-v2" / f"{num}-body-02.png",
    ]
    for col, path in enumerate(paths):
        image = Image.open(path).convert("RGB").resize(thumb, Image.Resampling.LANCZOS)
        canvas.paste(image, (col * thumb[0], row * thumb[1]))
    draw.rectangle((0, row * thumb[1], 58, row * thumb[1] + 28), fill="#071728")
    draw.text((8, row * thumb[1] + 5), num, fill="white")

OUT.parent.mkdir(parents=True, exist_ok=True)
canvas.save(OUT, quality=91, optimize=True)
print(OUT)
