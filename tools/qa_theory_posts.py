from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image


@dataclass
class Finding:
    post: str
    severity: str
    code: str
    detail: str


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dhash(path: Path, size: int = 16) -> int:
    with Image.open(path) as image:
        gray = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
    value = 0
    for y in range(size):
        row = y * (size + 1)
        for x in range(size):
            value = (value << 1) | int(pixels[row + x] > pixels[row + x + 1])
    return value


def distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def resolve_image(root: Path, html_file: Path, src: str) -> Path:
    return (html_file.parent / src.split("?", 1)[0]).resolve()


def audit(root: Path, first: int, last: int) -> dict:
    findings: list[Finding] = []
    summaries = []
    global_hashes: dict[str, list[str]] = {}

    for number in range(first, last + 1):
        post_id = f"{number:03d}"
        matches = sorted((root / "posts" / "theory").glob(f"{post_id}-*.html"))
        if len(matches) != 1:
            findings.append(Finding(post_id, "FAIL", "HTML_COUNT", f"HTML 파일 수 {len(matches)}"))
            continue
        html_file = matches[0]
        soup = BeautifulSoup(html_file.read_text(encoding="utf-8"), "html.parser")
        h1 = soup.select_one("article > header h1")
        sections = soup.select("article > section")
        figures = soup.select("article figure.article-image")
        body_text = " ".join(node.get_text(" ", strip=True) for node in sections)
        compact = re.sub(r"\s+", "", body_text)
        numeric_examples = re.findall(r"(?:\d[\d,.]*\s*(?:배|개|m|cm|mm|fm|kg|g|s|초|분|시간|일|년|MeV|keV|eV|MW|%)|예를\s*들면|예시)", body_text)

        if not h1 or not h1.get_text(strip=True):
            findings.append(Finding(post_id, "FAIL", "TITLE_MISSING", "게시물 제목 없음"))
        if len(compact) < 1400:
            findings.append(Finding(post_id, "FAIL", "BODY_TOO_SHORT", f"본문 유효문자 {len(compact)}자"))
        if len(sections) < 6:
            findings.append(Finding(post_id, "FAIL", "LEARNING_FLOW", f"본문 절 {len(sections)}개"))
        if len(numeric_examples) < 2:
            findings.append(Finding(post_id, "FAIL", "EXAMPLE_DEPTH", f"구체적 예시 신호 {len(numeric_examples)}개"))
        if not soup.select_one("table.article-table"):
            findings.append(Finding(post_id, "FAIL", "TABLE_MISSING", "비교·정리 표 없음"))
        if len(soup.select("footer.source a[href]")) < 1:
            findings.append(Finding(post_id, "FAIL", "SOURCE_TRACEABILITY", "클릭 가능한 주제별 참고자료 없음"))
        if len(figures) < 3:
            findings.append(Finding(post_id, "FAIL", "IMAGE_COUNT", f"전체 이미지 {len(figures)}개"))

        images = []
        paths_seen = set()
        for index, figure in enumerate(figures, 1):
            image = figure.find("img")
            caption = figure.find("figcaption")
            if image is None:
                findings.append(Finding(post_id, "FAIL", "IMG_TAG", f"그림 {index}: img 없음"))
                continue
            src = image.get("src", "")
            alt = image.get("alt", "").strip()
            if not src or src in paths_seen:
                findings.append(Finding(post_id, "FAIL", "DUPLICATE_REFERENCE", f"그림 {index}: 중복 경로 {src}"))
            paths_seen.add(src)
            if len(alt) < 12:
                findings.append(Finding(post_id, "FAIL", "ALT_TEXT", f"그림 {index}: 대체텍스트 부족"))
            if caption is None or len(caption.get_text(strip=True)) < 12:
                findings.append(Finding(post_id, "FAIL", "CAPTION", f"그림 {index}: 캡션 부족"))
            path = resolve_image(root, html_file, src)
            if not path.exists():
                findings.append(Finding(post_id, "FAIL", "IMAGE_MISSING", str(path)))
                continue
            with Image.open(path) as opened:
                dimensions = opened.size
            if dimensions != (1600, 900):
                findings.append(Finding(post_id, "FAIL", "IMAGE_SIZE", f"{path.name}: {dimensions}"))
            digest = sha256(path)
            perceptual = dhash(path)
            global_hashes.setdefault(digest, []).append(f"{post_id}:{path.name}")
            images.append((path, digest, perceptual))

        for left in range(len(images)):
            for right in range(left + 1, len(images)):
                a, b = images[left], images[right]
                if a[1] == b[1]:
                    findings.append(Finding(post_id, "FAIL", "EXACT_DUPLICATE_IMAGE", f"{a[0].name} = {b[0].name}"))
                else:
                    delta = distance(a[2], b[2])
                    if delta <= 28:
                        findings.append(Finding(post_id, "FAIL", "NEAR_DUPLICATE_IMAGE", f"{a[0].name} ~ {b[0].name}, dHash 거리 {delta}"))

        summaries.append({
            "post": post_id,
            "title": h1.get_text(strip=True) if h1 else "",
            "body_characters": len(compact),
            "sections": len(sections),
            "example_signals": len(numeric_examples),
            "images": len(images),
        })

        series = "series-01" if number <= 20 else ("series-02" if number <= 40 else "series-03")
        notes = root / "assets" / "images" / "theory" / series / "sources" / post_id / "review_notes.md"
        if not notes.exists():
            findings.append(Finding(post_id, "FAIL", "REVIEW_NOTES_MISSING", str(notes)))
        else:
            review = notes.read_text(encoding="utf-8")
            required = ["원본", "모바일", "기술", "중복", "PASS"]
            missing = [token for token in required if token not in review]
            if missing:
                findings.append(Finding(post_id, "FAIL", "REVIEW_NOTES_INCOMPLETE", "누락: " + ", ".join(missing)))

    for digest, refs in global_hashes.items():
        post_ids = {ref.split(":", 1)[0] for ref in refs}
        if len(post_ids) > 1:
            findings.append(Finding("ALL", "FAIL", "CROSS_POST_EXACT_DUPLICATE", f"{digest[:12]}: {', '.join(refs)}"))

    app_text = (root / "assets" / "app.js").read_text(encoding="utf-8")
    for number in range(first, last + 1):
        post_id = f"{number:03d}"
        count = len(re.findall(rf'posts/theory/{post_id}-[^"\']+\.html', app_text))
        if count != 1:
            findings.append(Finding(post_id, "FAIL", "APP_METADATA_COUNT", f"app.js URL 등록 {count}회"))

    failures = [asdict(item) for item in findings if item.severity == "FAIL"]
    return {
        "range": [first, last],
        "scope": "AUTOMATED_PREFLIGHT_ONLY",
        "independent_visual_approval": False,
        "status": "PASS" if not failures else "FAIL",
        "release_blocked": bool(failures),
        "summary": summaries,
        "findings": [asdict(item) for item in findings],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--first", type=int, default=1)
    parser.add_argument("--last", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve(), args.first, args.last)
    output = args.output or args.root / "qa" / "theory" / f"independent_qa_{args.first:03d}_{args.last:03d}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = output.with_suffix(".md")
    lines = [
        f"# 원자력이론 {args.first:03d}~{args.last:03d} 자동 사전검사",
        "",
        f"- 판정: **{result['status']}**",
        f"- 자동검사 결함에 따른 차단: **{'예' if result['release_blocked'] else '없음'}**",
        "- 독립 시각승인·게시 승인: 이 검사로 부여하지 않음",
        f"- 발견사항: {len(result['findings'])}건",
        "",
        "## 발견사항",
        "",
        "| 게시물 | 판정 | 코드 | 내용 |",
        "|---:|---|---|---|",
    ]
    lines.extend(
        f"| {item['post']} | {item['severity']} | {item['code']} | {item['detail'].replace('|', '/')} |"
        for item in result["findings"]
    )
    if not result["findings"]:
        lines.append("| 전체 | PASS | - | 자동검사에서 결함이 발견되지 않음 |")
    lines.extend([
        "",
        "## 별도 시각검사",
        "",
        "자동검사 PASS 후 원본 1600×900 이미지와 모바일 축소 화면에서 기술 정확성, 가짜 문자, 잘림·겹침, 정보 밀도와 전문적 완성도를 독립적으로 확인해야 한다.",
    ])
    markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "release_blocked": result["release_blocked"], "finding_count": len(result["findings"]), "output": str(output)}, ensure_ascii=False))
    return 1 if result["release_blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
