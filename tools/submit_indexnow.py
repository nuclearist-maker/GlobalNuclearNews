"""Submit public sitemap URLs to IndexNow. Dry-run unless --submit is supplied."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from search_discovery import BASE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--submit', action='store_true')
    parser.add_argument('--sitemap', type=Path, default=Path(__file__).resolve().parents[1] / '_site/sitemap.xml')
    args = parser.parse_args()
    config = json.loads(Path(__file__).with_name('search_config.json').read_text(encoding='utf-8'))
    key = config['indexnow_key']
    urls = [n.text for n in ET.parse(args.sitemap).iter() if n.tag.endswith('}loc')]
    if not urls or len(urls) > 10000 or len(set(urls)) != len(urls) or any(not u.startswith(BASE) for u in urls):
        raise ValueError('Sitemap URLs outside authorized scope or invalid count')
    payload = {'host': urlsplit(BASE).netloc, 'key': key, 'keyLocation': BASE + key + '.txt', 'urlList': urls}
    if not args.submit:
        print(json.dumps({'mode': 'dry-run', 'count': len(urls), 'host': payload['host'], 'keyLocation': payload['keyLocation']}))
        return
    with urlopen(payload['keyLocation'], timeout=30) as response:
        if response.read().decode('utf-8').strip() != key: raise ValueError('Live key does not match')
    request = Request('https://api.indexnow.org/indexnow', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json; charset=utf-8'}, method='POST')
    with urlopen(request, timeout=60) as response:
        print(json.dumps({'http_status': response.status, 'url_count': len(urls), 'meaning': 'Received; indexing is not guaranteed' if response.status == 200 else 'Key verification pending; indexing is not guaranteed', 'response': response.read().decode('utf-8')}))


if __name__ == '__main__': main()
