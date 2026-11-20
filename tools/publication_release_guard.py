"""Portable CI guard for exact reviewed publication changes, no private paths."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path


def digest(data, name):
    if Path(name).suffix in {'.html','.css','.js','.json','.md','.txt','.xml','.py','.yml'}:
        data = data.replace(b'\r\n', b'\n')
    return hashlib.sha256(data).hexdigest()


def scope_digest(manifest):
    value={'base_commit':manifest['base_commit'],'release_files':manifest['release_files']}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def verify(root, manifest='qa/deployments/publication.json', latest=False):
    def git(*args): return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
    m = json.loads((root/manifest).read_text(encoding='utf-8-sig'))
    base = m['base_commit']
    if not re.fullmatch('[0-9a-f]{40}',base): raise ValueError('Invalid baseline')
    head = git('rev-parse','HEAD')
    parents=[line.split()[1] for line in git('cat-file','-p','HEAD').split('\n\n',1)[0].splitlines() if line.startswith('parent ')]
    if parents != [base]:
        raise ValueError('Release parent differs from reviewed baseline')
    if latest and git('ls-remote','origin','refs/heads/main').split()[0] != head:
        raise ValueError('Newer main exists; do not deploy an obsolete release')
    actual = set(git('diff','--name-only',base,'HEAD').splitlines())
    if actual != set(m['release_files']) | {manifest}:
        raise ValueError('Missing or unreviewed changed files')
    for name, expected in m['release_files'].items():
        p = root/name
        if not name or '\\' in name or ':' in name or name.startswith('/') or '..' in name.split('/') or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):
            raise ValueError('Invalid release path')
        if digest(p.read_bytes(),name) != expected: raise ValueError('Release hash drift: '+name)
    proofs = m.get('verification',{})
    for name in ['local_publish_gate_sha256','independent_review_sha256']:
        if not re.fullmatch('[0-9a-f]{64}',proofs.get(name,'')): raise ValueError('Missing local verification proof')
    if proofs.get('reviewed_release_sha256') != scope_digest(m):raise ValueError('Reviewed scope commitment differs')
    return {'status':'PASS','commit':head,'files':len(m['release_files'])}


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--manifest',default='qa/deployments/publication.json');p.add_argument('--require-latest',action='store_true');a=p.parse_args()
    try: print(json.dumps(verify(a.root,a.manifest,a.require_latest)))
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as e:
        print(json.dumps({'status':'FAIL','reason':str(e)}));raise SystemExit(1)
