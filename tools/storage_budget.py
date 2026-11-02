"""Non-destructive storage reporting and Pages budget enforcement (decimal bytes)."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import subprocess

SITE_WARN = 750_000_000
SITE_LIMIT = 900_000_000  # headroom below GitHub's documented 1 GB site limit
GROWTH_WARN = 25_000_000
GROWTH_LIMIT = 100_000_000


def notice(level, message):
    print(f'::{level}::{message}' if os.environ.get('GITHUB_ACTIONS') else f'{level.upper()}: {message}')


def check_budget(size, warn, limit, label):
    if not 0 < warn < limit:
        raise ValueError('Expected 0 < warning threshold < failure threshold')
    print(f'{label}: {size:,} bytes (warn {warn:,}; fail {limit:,})')
    if size >= limit:
        notice('error', f'{label} reached the storage failure threshold. Upload/push blocked; no files deleted.')
        return False
    if size >= warn:
        notice('warning', f'{label} reached the storage warning threshold; plan capacity before adding more assets.')
    return True


def check_site(out):
    # Measure after discovery/advertising generation, including files absent from collect().
    files = [p for p in out.rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in out.rglob('*')):
        raise ValueError('Pages output must not contain symlinks')
    size = sum(p.stat().st_size for p in files)
    ok = check_budget(size, SITE_WARN, SITE_LIMIT, 'Final Pages output')
    print(f'Final Pages output: {len(files)} files; {size / 2**20:.1f} MiB')
    for p in sorted(files, key=lambda p: p.stat().st_size, reverse=True)[:10]:
        print(f'  {p.stat().st_size:>10,} {p.relative_to(out)}')
    return ok


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root)


def tree(root, ref):
    result = []
    for record in git(root, 'ls-tree', '-rlz', ref).split(b'\0'):
        if not record:
            continue
        metadata, name = record.split(b'\t', 1)
        mode, kind, oid, size = metadata.split()
        if kind == b'blob':
            result.append((os.fsdecode(name), int(size), oid.decode()))
    return result


def report(root, history=False, base=None, staged=False):
    rows = tree(root, 'HEAD')
    duplicates = defaultdict(list)
    directories = Counter()
    for name, size, oid in rows:
        directories[name.split('/')[0]] += size
        duplicates[oid].append((name, size))
    result = {'head': git(root, 'rev-parse', 'HEAD').decode().strip(),
              'tracked_files': len(rows), 'tracked_bytes': sum(s for _, s, _ in rows),
              'directories': dict(directories.most_common()),
              'duplicate_path_bytes': sum(v[0][1] * (len(v)-1) for v in duplicates.values()),
              'largest_files': sorted(rows, key=lambda r: r[1], reverse=True)[:20]}
    if history:
        # Full clone required. Unique reachable blobs, not the sum of every revision's tree.
        if git(root, 'rev-parse', '--is-shallow-repository').strip() == b'true':
            raise ValueError('History audit requires a full clone (fetch-depth: 0)')
        objects = git(root, 'rev-list', '--objects', '--all')
        proc = subprocess.run(['git', 'cat-file', '--batch-check=%(objectname) %(objecttype) %(objectsize) %(objectsize:disk) %(rest)'],
                              cwd=root, input=objects, capture_output=True, check=True)
        current = {oid for _, _, oid in rows}
        count = total = old = disk = 0
        extensions = Counter()
        for line in proc.stdout.decode(errors='surrogateescape').splitlines():
            fields = line.split(' ', 4)
            if fields[1] != 'blob':
                continue
            count += 1
            total += int(fields[2])
            disk += int(fields[3])
            if fields[0] not in current:
                old += int(fields[2])
                extensions[Path(fields[4]).suffix if len(fields) > 4 else ''] += int(fields[2])
        result.update(reachable_blobs=count, unique_blob_bytes=total,
                      blob_disk_bytes=disk, history_only_blob_bytes=old,
                      history_only_extensions=dict(extensions.most_common()),
                      git_objects=git(root, 'count-objects', '-v').decode())
    ok = True
    if base or staged:
        before = {oid for _, _, oid in tree(root, base or 'HEAD')}
        after = tree(root, 'HEAD') if not staged else []
        if staged:
            for record in git(root, 'ls-files', '--stage', '-z').split(b'\0'):
                if not record:
                    continue
                metadata, name = record.split(b'\t', 1)
                mode, oid, stage = metadata.split()
                if stage != b'0':
                    raise ValueError('Resolve staged conflicts before publishing')
                if mode == b'160000':
                    continue
                size = int(git(root, 'cat-file', '-s', oid.decode()))
                after.append((os.fsdecode(name), size, oid.decode()))
        added = {oid: size for _, size, oid in after if oid not in before}
        growth = sum(added.values())
        result['new_unique_blob_bytes'] = growth
        ok = check_budget(growth, GROWTH_WARN, GROWTH_LIMIT, 'New Git blobs (gross, before compression)')
        for name, size, oid in after:
            if oid not in before and size >= 5_000_000:
                notice('warning', f'Large new asset: {name} ({size:,} bytes); review compression and archival location.')
    print(json.dumps(result, indent=2, ensure_ascii=True))
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a') as f:
            f.write('### Storage audit\n\n```json\n' + json.dumps(result, indent=2) + '\n```\n')
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--base', help='compare newly introduced blob content with this ref')
    parser.add_argument('--staged', action='store_true', help='check index against HEAD before a publishing commit')
    args = parser.parse_args()
    return 0 if report(Path(__file__).resolve().parents[1], args.history, args.base, args.staged) else 1


if __name__ == '__main__':
    raise SystemExit(main())
