"""Disposable local computation cache, never an approval store."""
from pathlib import Path
import hashlib,json,os,sqlite3

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def default_cache_dir():
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.cache')))/'GlobalNuclearNews'/'qa-cache'

class ComputationCache:
    def __init__(self,directory,namespace):
        self.namespace=namespace;self.hits=0;self.misses=0;self.invalid=0;self.db=None;self.pruned=False;self.path=None
        policy=json.loads((Path(__file__).resolve().parents[1]/'policies/theory_incremental_qa.json').read_text(encoding='utf8'))
        self.max_bytes=policy['cache_max_bytes']
        if type(self.max_bytes)is not int or self.max_bytes<=0 or policy.get('reuse_is_approval') is not False:raise ValueError('Invalid cache policy')
        if directory is not None:
            try:
                directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
                self.path=directory/'computations.sqlite3';self.db=sqlite3.connect(self.path,timeout=20)
                self.db.execute('CREATE TABLE IF NOT EXISTS memo (key TEXT PRIMARY KEY,payload TEXT NOT NULL,checksum TEXT NOT NULL)')
            except (OSError,sqlite3.Error):
                self.db=None # cache unavailable means recompute, never PASS/skip
    def key(self,kind,inputs):return fingerprint([self.namespace,kind,inputs])
    def get(self,kind,inputs,valid):
        key=self.key(kind,inputs)
        if self.db is not None:
            try:
                row=self.db.execute('SELECT payload,checksum FROM memo WHERE key=?',(key,)).fetchone()
                if row:
                    value=json.loads(row[0])
                    if hashlib.sha256(row[0].encode()).hexdigest()==row[1] and valid(value):
                        self.hits+=1;return value
                    self.invalid+=1
            except (sqlite3.Error,ValueError,TypeError,KeyError,OverflowError):self.invalid+=1
        self.misses+=1;return None
    def put(self,kind,inputs,value):
        if self.db is None:return
        payload=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        try:self.db.execute('INSERT OR REPLACE INTO memo VALUES (?,?,?)',(self.key(kind,inputs),payload,hashlib.sha256(payload.encode()).hexdigest()))
        except sqlite3.Error:pass
    def close(self):
        if self.db is not None:
            try:
                self.db.commit()
                if self.path.stat().st_size>self.max_bytes:
                    self.db.execute('DELETE FROM memo');self.db.commit();self.db.execute('VACUUM');self.pruned=True
            except (sqlite3.Error,OSError):pass
            self.db.close();self.db=None
    def stats(self):return {'hits':self.hits,'misses':self.misses,'invalid_recomputed':self.invalid,'namespace':self.namespace,'approval_cache':False,'pruned_at_size_limit':self.pruned}
