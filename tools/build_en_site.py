"""Package the English GlobalNuclearNews site into _site/ for GitHub Pages.

Copies only the browser-facing dependency closure of the HTML pages, posts and
assets/app.js (see public_files.collect). A missing linked file aborts the build,
so a broken image or page link can never be deployed.
"""
from pathlib import Path
import json
import shutil
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from public_files import collect
from storage_budget import check_site
from search_discovery import enrich
from advertising import install as install_advertising
from build_reactor_pages import main as build_reactor_pages
from build_bilingual import install as install_bilingual

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"


def main():
    build_reactor_pages()
    files = collect(ROOT)
    allowed = OUT.resolve() == ROOT.resolve() / "_site" or OUT.resolve().is_relative_to((ROOT.parent / 'temp').resolve())
    if OUT.is_symlink() or not allowed:
        raise ValueError("Unsafe output path")
    if OUT.exists():
        shutil.rmtree(OUT)
    def copy_public(p):
        target = OUT / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(copy_public, sorted(files)))
    discovery = enrich(OUT, json.loads((ROOT / 'tools/search_config.json').read_text(encoding='utf-8')))
    print('Bilingual edition:', json.dumps(install_bilingual(ROOT, OUT)))
    print('AdSense:', json.dumps(install_advertising(OUT)))
    print('Search discovery:', json.dumps(discovery))
    if not check_site(OUT):
        raise SystemExit(1)
    size = sum(p.stat().st_size for p in files) / 2**20
    print(f"Packaged {len(files)} public files, {size:.1f} MiB")
    for p in sorted(files):
        print(" ", p.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,help='Optional local preview output under workspace temp; CI defaults to _site.')
    args=parser.parse_args()
    if args.output:OUT=args.output.resolve()
    main()
