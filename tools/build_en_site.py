"""Package the English GlobalNuclearNews site into _site/ for GitHub Pages.

Copies only the browser-facing dependency closure of the HTML pages, posts and
assets/app.js (see public_files.collect). A missing linked file aborts the build,
so a broken image or page link can never be deployed.
"""
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_files import collect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"


def main():
    files = collect(ROOT)
    if OUT.is_symlink() or OUT.resolve() != ROOT.resolve() / "_site":
        raise ValueError("Unsafe output path")
    if OUT.exists():
        shutil.rmtree(OUT)
    for p in sorted(files):
        target = OUT / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
    size = sum(p.stat().st_size for p in files) / 2**20
    print(f"Packaged {len(files)} public files, {size:.1f} MiB")
    for p in sorted(files):
        print(" ", p.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
