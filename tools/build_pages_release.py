"""Package only browser-facing site files, preserving their paths."""
from pathlib import Path
from urllib.parse import urlsplit,unquote
import re,shutil
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_site'
pending=list(ROOT.glob('*.html'))+list((ROOT/'posts').rglob('*.html'))+[ROOT/'assets/app.js']
for name in ('CNAME','.nojekyll','robots.txt','sitemap.xml','favicon.ico'):
 if (ROOT/name).is_file():pending.append(ROOT/name)
seen=set()
def dependency(base,value):
 if not value or value.startswith(('data:','#','mailto:','javascript:')):return
 u=urlsplit(value)
 if u.scheme or u.netloc:return
 p=((ROOT/unquote(u.path).lstrip('/')) if u.path.startswith('/') else (base.parent/unquote(u.path))).resolve()
 if p==ROOT or p.is_dir():return
 if not p.is_relative_to(ROOT):raise ValueError(f'Outside site: {value}')
 if not p.is_file():raise FileNotFoundError(f'{base.relative_to(ROOT)} -> {value}')
 pending.append(p)
while pending:
 p=pending.pop().resolve()
 if p in seen:continue
 seen.add(p)
 if p.suffix=='.html':
  soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
  for tag in soup.select('[src],link[href],a[href]'):dependency(p,tag.get('src') or tag.get('href'))
 elif p.suffix=='.css':
  for value in re.findall(r'url\([\s\"\']*([^\)\"\']+)',p.read_text(encoding='utf-8')):dependency(p,value.strip())
 elif p.name=='app.js':
  for value in re.findall(r'[\"\']((?:assets|posts)/[^\"\']+)[\"\']',p.read_text(encoding='utf-8')):dependency(ROOT/'index.html',value)
for p in sorted(seen):
 target=OUT/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
print(f'Packaged {len(seen)} public files, {sum(p.stat().st_size for p in seen)/2**20:.1f} MiB')
