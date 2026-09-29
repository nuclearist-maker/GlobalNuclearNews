"""Enumerate precisely the browser-facing dependency closure, without writing files."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re

class References(HTMLParser):
 def __init__(self):super().__init__();self.refs=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if d.get('src'):self.refs.append(d['src'])
  if tag in ('a','link') and d.get('href'):self.refs.append(d['href'])
  if d.get('srcset'):
   self.refs.extend(x.strip().split()[0] for x in d['srcset'].split(',') if x.strip())

def collect(root):
 root=root.resolve()
 pending=list(root.glob('*.html'))+list((root/'posts').rglob('*.html'))
 for name in ('assets/app.js','CNAME','.nojekyll','robots.txt','sitemap.xml','favicon.ico'):
  if (root/name).is_file():pending.append(root/name)
 seen=set()
 def add(base,value):
  u=urlsplit(value)
  if not u.path or u.scheme or u.netloc:return
  p=(root/unquote(u.path).lstrip('/') if u.path.startswith('/') else base.parent/unquote(u.path)).resolve()
  if not p.is_relative_to(root):raise ValueError('Dependency escapes site: '+value)
  if p.is_dir():p=p/'index.html'
  if not p.is_file():raise ValueError('Missing public dependency: '+str(p.relative_to(root)))
  pending.append(p)
 while pending:
  p=pending.pop().resolve()
  if p in seen:continue
  seen.add(p)
  if p.suffix=='.html':
   parser=References();parser.feed(p.read_text(encoding='utf-8-sig'))
   for value in parser.refs:add(p,value)
  elif p.suffix=='.css':
   for value in re.findall(r'url\([\s\"\']*([^\)\"\']+)',p.read_text(encoding='utf-8-sig')):add(p,value.strip())
  elif p.name=='app.js':
   for value in re.findall(r'[\"\']((?:assets|posts)/[^\"\']+)[\"\']',p.read_text(encoding='utf-8-sig')):add(root/'index.html',value)
 return seen
