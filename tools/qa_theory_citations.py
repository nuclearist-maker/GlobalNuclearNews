"""Numbered citation structure; never claims semantic source verification."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

INTRO = re.compile(r'(?:IAEA|NIST|DOE|NRC|EPA|LBNL|NNDC|DDEP|CODATA|AME|MIT|Fermilab|Lamarsh)(?:의|가|는|에서)?\s*(?:[^.!?。]{0,32})?(?:자료에\s*따르면|교재(?:는|에서는)|문헌(?:은|에서는)|설명처럼|표에\s*따르면)')

def audit_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, 'html.parser')
    errors = []
    article = soup.select_one('article')
    if not article:
        return ['ARTICLE_MISSING']
    foot = article.select_one('footer.source')
    if not foot:
        return ['BIBLIOGRAPHY_MISSING']
    ids = [x['id'] for x in soup.select('[id]')]
    if len(ids) != len(set(ids)):
        errors.append('DUPLICATE_ID')
    refs = foot.select('.reference-entry')
    numbers = []
    for ref in refs:
        match = re.fullmatch(r'ref-([1-9]\d*)', ref.get('id', ''))
        if not match:
            errors.append('REFERENCE_ID_INVALID'); continue
        n = int(match[1]); numbers.append(n)
        label = ref.select_one('.reference-number')
        if not label or label.get_text(strip=True) != f'[{n}]':
            errors.append(f'REFERENCE_LABEL:{n}')
        body = BeautifulSoup(str(ref), 'html.parser')
        for x in body.select('.reference-number'):
            x.decompose()
        if len(body.get_text(' ', strip=True)) < 5:
            errors.append(f'REFERENCE_EMPTY:{n}')
    if not numbers or numbers != list(range(1, len(refs) + 1)):
        errors.append('REFERENCE_SEQUENCE')
    foot.decompose()
    citations = article.select('a.citation')
    if not citations:
        errors.append('BODY_CITATION_MISSING')
    for link in article.select('a[href]'):
        href = link['href']
        if re.match(r'^(?:https?:)?//', href, re.I):
            errors.append('BODY_EXTERNAL_SOURCE_LINK')
        if href.startswith('#ref') and 'citation' not in link.get('class', []):
            errors.append('CITATION_CLASS_MISSING')
    for cite in citations:
        match = re.fullmatch(r'#ref-([1-9]\d*)', cite.get('href', ''))
        if not match or int(match[1]) not in numbers:
            errors.append('CITATION_TARGET'); continue
        n = int(match[1])
        if cite.get_text(strip=True) != f'[{n}]':
            errors.append('CITATION_LABEL')
        if cite.get('aria-label') != f'참고문헌 {n}':
            errors.append('CITATION_ACCESSIBILITY')
        block = cite.find_parent(['p', 'li', 'figcaption', 'td', 'th'])
        if block is None:
            errors.append('CITATION_CONTAINER'); continue
        preceding = ''
        for elem in block.descendants:
            if elem is cite:
                break
            if isinstance(elem, NavigableString) and not elem.find_parent('a', class_='citation'):
                preceding += str(elem)
        if not re.search(r'[.!?。][”’"\']?\s*$', preceding):
            errors.append('CITATION_NOT_SENTENCE_END')
    for block in article.select('p,li,figcaption,td'):
        if INTRO.search(block.get_text(' ', strip=True)):
            errors.append('SOURCE_INTRO_REVIEW_REQUIRED')
    return sorted(set(errors))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--first', type=int, default=1)
    ap.add_argument('--last', type=int, required=True)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    rows = []
    for n in range(a.first, a.last + 1):
        paths = list((a.root/'posts/theory').glob(f'{n:03d}-*.html'))
        errors = audit_html(paths[0].read_text(encoding='utf-8')) if len(paths) == 1 else ['HTML_COUNT']
        rows.append({'post': n, 'errors': errors})
    result = {'status': 'FAIL' if any(x['errors'] for x in rows) else 'PASS', 'posts': rows}
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return int(result['status'] != 'PASS')

if __name__ == '__main__':
    raise SystemExit(main())
