from pathlib import Path
import re, shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
GEN = Path(r"C:\Users\nucle\.codex\generated_images\01a0c8e8-9805-7182-9801-c2c20e061247")
FILES = {
    6: "exec-0a607f61-6b31-414b-a98b-0d8a6b5fbe27.png",
    7: "exec-b43381d6-887d-4bf3-b625-a77fa2afab73.png",
    8: "exec-c16cc50b-7826-427a-a113-0896ecdaac35.png",
    9: "exec-22fcac56-22fc-4b50-9a82-b56c4534640f.png",
    10: "exec-69f6f22e-841a-4f1a-8e97-dca49bd4a64b.png",
}
OUT = ROOT / "assets/images/theory/series-01/pilot-v6"
OUT.mkdir(parents=True, exist_ok=True)
for number, filename in FILES.items():
    post_id = f"{number:03d}"
    source = Image.open(GEN / filename).convert("RGB")
    source.resize((1600, 900), Image.Resampling.LANCZOS).save(OUT / f"{post_id}-thumbnail.png", quality=95)
    post = next((ROOT / "posts/theory").glob(f"{post_id}-*.html"))
    text = post.read_text(encoding="utf-8")
    text = re.sub(rf'../../assets/images/theory/series-01/[^"/]+/{post_id}-thumbnail\.png', f'../../assets/images/theory/series-01/pilot-v6/{post_id}-thumbnail.png', text)
    post.write_text(text, encoding="utf-8")
app = ROOT / "assets/app.js"
text = app.read_text(encoding="utf-8")
for number in FILES:
    post_id = f"{number:03d}"
    text = re.sub(rf'assets/images/theory/series-01/[^"/]+/{post_id}-thumbnail\.png', f'assets/images/theory/series-01/pilot-v6/{post_id}-thumbnail.png', text)
app.write_text(text, encoding="utf-8")
