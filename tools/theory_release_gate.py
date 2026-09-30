from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


def digest(path: Path) -> str:
    text_extensions = {".html", ".css", ".js", ".json", ".md", ".py", ".yml", ".yaml"}
    if path.suffix.lower() in text_extensions:
        data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(data).hexdigest()
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def article_dependencies(root: Path, article: Path, text: str) -> list[Path]:
    """Collect local rendering resources, including responsive and CSS images."""
    resources = []
    def css_refs(css):
        return re.findall(r'url\(\s*[\"\']?([^\)\"\']+)', css) + re.findall(r'@import\s+[\"\']([^\"\']+)', css)
    class Parser(HTMLParser):
        in_style = False
        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == 'style': self.in_style = True
            for key in ('src', 'poster'):
                if attrs.get(key): resources.append(attrs[key])
            if attrs.get('srcset'):
                resources.extend(x.strip().split()[0] for x in attrs['srcset'].split(',') if x.strip())
            if tag == 'link' and 'stylesheet' in attrs.get('rel', '').split() and attrs.get('href'):
                resources.append(attrs['href'])
            if tag == 'image' and attrs.get('href'): resources.append(attrs['href'])
            resources.extend(css_refs(attrs.get('style', '')))
        def handle_endtag(self, tag):
            if tag == 'style': self.in_style = False
        def handle_data(self, data):
            if self.in_style: resources.extend(css_refs(data))
    Parser().feed(text)
    pending = [(article, ref) for ref in resources]
    seen = set()
    while pending:
        base, ref = pending.pop()
        url = urlsplit(ref.strip())
        if url.scheme == 'data' or not url.path: continue
        if url.scheme or url.netloc:
            raise ValueError('Unsealable external rendering resource: ' + ref)
        path = (root / unquote(url.path).lstrip('/') if url.path.startswith('/') else base.parent / unquote(url.path)).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError('Invalid rendering resource: ' + ref)
        if path in seen: continue
        seen.add(path)
        if path.suffix.lower() == '.css':
            pending.extend((path, ref) for ref in css_refs(path.read_text(encoding='utf-8')))
    return sorted(seen)


def release_files(root: Path, first: int = 1, last: int = 50) -> list[Path]:
    if not 1 <= first <= last <= 300:
        raise ValueError("Invalid curriculum range")
    files: list[Path] = []
    for number in range(first, last + 1):
        post_id = f"{number:03d}"
        html = list((root / "posts/theory").glob(f"{post_id}-*.html"))
        if len(html) != 1:
            raise RuntimeError(f"{post_id}: HTML 파일이 정확히 하나가 아님")
        files.extend(html)
        text = html[0].read_text(encoding="utf-8")
        if (first, last) != (1, 50):
            files.extend(article_dependencies(root, html[0], text))
            continue
        for marker in ('src="../../assets/images/theory/',):
            start = 0
            while True:
                index = text.find(marker, start)
                if index < 0:
                    break
                begin = index + len('src="../../')
                end = text.find('"', begin)
                files.append(root / text[begin:end])
                start = end + 1
    files.extend([root / "assets/app.js", root / "assets/article.css"])
    unique = sorted({path.resolve() for path in files})
    missing = [str(path) for path in unique if not path.exists()]
    if missing:
        raise RuntimeError("누락 파일: " + ", ".join(missing))
    return unique


def snapshot(root: Path, first: int = 1, last: int = 50) -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): digest(path) for path in release_files(root, first, last)}



def audit_bindings(root: Path, names: list[str], current: dict[str,str]) -> dict[str,str]:
    if not names:
        raise ValueError("Extended range requires independent JSON audits")
    covered={}; bindings={}
    for name in names:
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError("Invalid audit path: "+name)
        data=json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("status")!="PASS" or data.get("independent") is not True:
            raise ValueError("Independent audit not PASS: "+name)
        reviewer = data.get('reviewer')
        author = data.get('author')
        if not isinstance(reviewer, str) or not reviewer.strip() or not isinstance(author, str) or not author.strip() or reviewer.strip() == author.strip():
            raise ValueError('Distinct author/reviewer identities required: ' + name)
        checked_at = data.get('checked_at')
        if not isinstance(checked_at, str):
            raise ValueError('Audit timestamp required: ' + name)
        when = datetime.fromisoformat(checked_at.replace('Z', '+00:00'))
        if when.tzinfo is None or when.utcoffset() is None:
            raise ValueError('Audit timestamp requires timezone: ' + name)
        files=data.get("files",{})
        if not isinstance(files,dict) or not files:
            raise ValueError("Audit has no reviewed file bindings: "+name)
        for item,sha in files.items():
            if item not in current or current[item]!=sha:
                raise ValueError("Audit refers to changed or out-of-scope file: "+item)
        covered.update(files)
        bindings[path.relative_to(root).as_posix()]=digest(path)
    if covered!=current:
        raise ValueError("Independent audit coverage is incomplete")
    return bindings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int, default=50)
    parser.add_argument("--audit", action="append", default=[])
    parser.add_argument("--reviewer", default="")
    args = parser.parse_args()
    if args.audit and not args.seal:
        raise SystemExit("FAIL: --audit is accepted only with --seal")
    root = args.root.resolve()
    scope = f"{args.first:03d}-{args.last:03d}"
    legacy = (args.first, args.last) == (1, 50)
    if legacy and args.audit:
        raise SystemExit('FAIL: legacy 001-050 uses its existing MD audits; --audit is not accepted')
    manifest = root / f"qa/theory/visual_approval_{args.first:03d}_{args.last:03d}.json"
    current = snapshot(root, args.first, args.last)

    if args.seal:
        if not args.reviewer.strip():
            raise SystemExit("--seal에는 --reviewer가 필요합니다.")
        bindings = {}
        if not legacy:
            bindings = audit_bindings(root, args.audit, current)
        audits = [
            root / "qa/theory/visual_audit_001_017.md",
            root / "qa/theory/visual_audit_018_034.md",
            root / "qa/theory/visual_audit_035_050.md",
        ]
        for audit in audits if legacy else []:
            if not audit.exists() or "종합 판정: **PASS**" not in audit.read_text(encoding="utf-8"):
                raise SystemExit(f"독립 시각감사 PASS 기록 없음: {audit}")
        payload = {
            "status": "PASS",
            "scope": scope,
            "reviewer": args.reviewer.strip(),
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "files": current,
        }
        if not legacy:
            payload["audits"] = bindings
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"SEALED {manifest} ({len(current)} files)")
        return 0

    if not manifest.exists():
        raise SystemExit("FAIL: 독립 시각검수 승인 manifest가 없습니다.")
    approved = json.loads(manifest.read_text(encoding="utf-8"))
    if approved.get("status") != "PASS" or approved.get("scope") != scope:
        raise SystemExit("FAIL: 시각검수 승인 상태 또는 범위가 올바르지 않습니다.")
    if approved.get("files") != current:
        raise SystemExit("FAIL: 시각검수 승인 후 HTML/이미지/CSS/메타데이터가 변경되었습니다.")
    if not legacy:
        bindings = approved.get("audits", {})
        if not isinstance(bindings, dict) or not bindings:
            raise SystemExit('FAIL: independent audit bindings missing')
        if audit_bindings(root, list(bindings), current) != bindings:
            raise SystemExit("FAIL: independent audit evidence changed")
    print(f"PASS: 독립 시각검수 승인과 {len(current)}개 파일 해시가 일치합니다.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, TypeError) as exc:
        raise SystemExit("FAIL: " + str(exc))
