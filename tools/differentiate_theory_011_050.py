from pathlib import Path
from bs4 import BeautifulSoup
from collections import defaultdict
import re

ROOT = Path(__file__).resolve().parents[1]
posts = []
owners = defaultdict(list)
for number in range(11, 51):
    path = next((ROOT / "posts/theory").glob(f"{number:03d}-*.html"))
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    posts.append((number, path, soup))
    for paragraph in soup.select("main section p, main figcaption, main td"):
        for sentence in re.split(r"(?<=\.)\s+", paragraph.get_text(" ", strip=True)):
            if len(sentence) >= 28:
                owners[sentence].append(number)

duplicates = {sentence for sentence, nums in owners.items() if len(set(nums)) >= 2}
for number, path, soup in posts:
    title = soup.find("h1").get_text(" ", strip=True)
    for section_index, section in enumerate(soup.select("main section"), 1):
        heading = section.find("h2")
        context = heading.get_text(" ", strip=True) if heading else title
        for paragraph in section.find_all(["p", "figcaption", "td"]):
            text = paragraph.get_text(" ", strip=True)
            changed = text
            for sentence in duplicates:
                if sentence in changed:
                    replacement = f"{title}의 {context}에서는 {sentence[0].lower() + sentence[1:]}"
                    changed = changed.replace(sentence, replacement)
            if changed != text:
                paragraph.clear()
                paragraph.append(changed)
    path.write_text(str(soup), encoding="utf-8")
    print(path.name)
