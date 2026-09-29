"""Package only verified browser-facing files into a fresh output directory."""
from pathlib import Path
import shutil
from public_files import collect
from project_quality_gate import site_errors

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_site'

def main():
    errors=site_errors(ROOT)
    if errors:
        raise ValueError('Publication blocked; rework and recheck: '+repr(errors))
    seen=collect(ROOT)
    # Generated output only. Resolve and verify the exact workspace child before removal.
    if OUT.is_symlink() or OUT.resolve()!=ROOT.resolve()/'_site':
        raise ValueError('Unsafe generated output path')
    if OUT.exists():
        shutil.rmtree(OUT)
    for p in sorted(seen):
        target=OUT/p.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,target)
    print(f'Packaged {len(seen)} verified public files, {sum(p.stat().st_size for p in seen)/2**20:.1f} MiB')

if __name__=='__main__': main()
