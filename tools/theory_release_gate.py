from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


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


def release_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for number in range(1, 51):
        post_id = f"{number:03d}"
        html = list((root / "posts/theory").glob(f"{post_id}-*.html"))
        if len(html) != 1:
            raise RuntimeError(f"{post_id}: HTML 파일이 정확히 하나가 아님")
        files.extend(html)
        text = html[0].read_text(encoding="utf-8")
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


def snapshot(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)).replace("\\", "/"): digest(path) for path in release_files(root)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--reviewer", default="")
    args = parser.parse_args()
    root = args.root.resolve()
    manifest = root / "qa/theory/visual_approval_001_050.json"
    current = snapshot(root)

    if args.seal:
        if not args.reviewer.strip():
            raise SystemExit("--seal에는 --reviewer가 필요합니다.")
        audits = [
            root / "qa/theory/visual_audit_001_017.md",
            root / "qa/theory/visual_audit_018_034.md",
            root / "qa/theory/visual_audit_035_050.md",
        ]
        for audit in audits:
            if not audit.exists() or "종합 판정: **PASS**" not in audit.read_text(encoding="utf-8"):
                raise SystemExit(f"독립 시각감사 PASS 기록 없음: {audit}")
        payload = {
            "status": "PASS",
            "scope": "001-050",
            "reviewer": args.reviewer.strip(),
            "sealed_at": datetime.now(timezone.utc).isoformat(),
            "files": current,
        }
        manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"SEALED {manifest} ({len(current)} files)")
        return 0

    if not manifest.exists():
        raise SystemExit("FAIL: 독립 시각검수 승인 manifest가 없습니다.")
    approved = json.loads(manifest.read_text(encoding="utf-8"))
    if approved.get("status") != "PASS" or approved.get("scope") != "001-050":
        raise SystemExit("FAIL: 시각검수 승인 상태 또는 범위가 올바르지 않습니다.")
    if approved.get("files") != current:
        raise SystemExit("FAIL: 시각검수 승인 후 HTML/이미지/CSS/메타데이터가 변경되었습니다.")
    print(f"PASS: 독립 시각검수 승인과 {len(current)}개 파일 해시가 일치합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
