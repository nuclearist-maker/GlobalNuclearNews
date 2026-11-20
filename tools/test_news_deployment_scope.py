import json,subprocess,tempfile,unittest,copy
from pathlib import Path
from news_deployment_scope import scope_errors,digest

class NewsScopeTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.site=self.root/'_site'
  def g(*args):return subprocess.check_output(['git','-C',str(self.root),*args],stderr=subprocess.PIPE).decode().strip()
  self.g=g;g('init');g('config','user.name','Fixture');g('config','user.email','fixture@example.invalid')
  self.old='posts/news/2026-11-19-old.html';self.new='posts/news/2026-11-20-new.html'
  self.put(self.old,'old');self.put('locales/ko/'+self.old,'old-ko')
  self.put('assets/app.js','const posts = '+json.dumps([{'url':self.old,'title':'old'}])+';')
  self.put('locales/ko/posts.json',json.dumps([{'url':self.old,'title':'old-ko'}]));self.put('locales/ko/assets.json','{}')
  g('add','.');g('commit','-qm','baseline');base=g('rev-parse','HEAD')
  self.put(self.new,'new');self.put('locales/ko/'+self.new,'new-ko');self.put('_site/'+self.new,'new');self.put('_site/ko/'+self.new,'new-ko')
  self.put('assets/app.js','const posts = '+json.dumps([{'url':self.old,'title':'old'},{'url':self.new,'title':'new'}])+';')
  self.put('locales/ko/posts.json',json.dumps([{'url':self.old,'title':'old-ko'},{'url':self.new,'title':'new-ko'}]))
  names=[self.new,'locales/ko/'+self.new,'assets/app.js','locales/ko/posts.json']
  self.m={'kind':'news-publication','new_posts':[],'base_commit':base,'new_news_paths':[self.new],'release_files':{x:digest(self.root/x) for x in names},'changed_features':[{'path':x,'feature':'listing','reason':'new article'} for x in names[-2:]],'verification':{'content_review_sha256':'1'*64,'local_publish_gate_sha256':'2'*64}}
 def put(self,p,text):
  target=self.root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf8')
 def errors(self):return scope_errors(self.m,self.root,self.site)
 def test_valid(self):self.assertEqual([],self.errors())
 def test_missing_counterpart(self):
  (self.root/'locales/ko'/self.new).unlink();self.assertTrue(self.errors())
 def test_undeclared_file(self):
  self.put('assets/leak.txt','internal');self.assertTrue(self.errors())
 def test_stale_hash(self):
  self.put(self.new,'changed');self.assertTrue(self.errors())
 def test_missing_metadata_prefix(self):
  self.put('assets/app.js','invalid metadata');self.assertTrue(self.errors())
 def test_metadata_edit_even_if_declared(self):
  self.put('locales/ko/posts.json',json.dumps([{'url':self.old,'title':'changed'},{'url':self.new,'title':'new-ko'}]));self.m['release_files']['locales/ko/posts.json']=digest(self.root/'locales/ko/posts.json');self.assertTrue(self.errors())
 def test_old_body_change(self):
  self.put(self.old,'changed');self.assertTrue(self.errors())
 def test_deletion(self):
  (self.root/self.old).unlink();self.assertTrue(self.errors())
 def test_no_proof(self):
  self.m['verification']={};self.assertTrue(self.errors())
 def test_bad_path(self):
  self.m['release_files']['../escape']='a'*64;self.assertTrue(self.errors())
 def test_private_source(self):
  p='assets/images/news/context.json';self.put(p,'{}');self.m['release_files'][p]=digest(self.root/p);self.assertTrue(self.errors())
 def test_reserved_kind(self):
  self.m['kind']='pe-board';self.assertTrue(self.errors())
 def test_missing_built_page(self):
  (self.site/'ko'/self.new).unlink();self.assertTrue(self.errors())
 def test_duplicate_paths(self):
  self.m['new_news_paths']*=2;self.assertTrue(self.errors())

if __name__=='__main__':unittest.main()
