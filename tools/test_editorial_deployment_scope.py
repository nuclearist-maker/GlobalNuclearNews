"""Synthetic tests; no fixture is a real publication approval."""
import copy,json,tempfile,unittest,subprocess
from pathlib import Path
from editorial_maintenance_gate import scope_errors,sha_bytes,canonical_scope,safe_path
from check_bilingual import localization_scope_errors

class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.site=self.root/'site';self.site.mkdir();self.built=self.root/'built';self.built.mkdir()
        self.name='posts/history/001-test.html';self.write(self.name,b'<p>same</p>')
        self.write('qa/deployments/current.json',b'{}')
        self.git('init','-q');self.git('config','user.name','Synthetic');self.git('config','user.email','fixture@example.invalid');self.git('add','.');self.git('commit','-qm','fixture')
        base=self.git('rev-parse','HEAD').strip();self.write(self.name,b'<p>same</p><footer class="source"><a href="https://example.org">ref</a></footer>')
        self.write('qa/deployments/current.json',b'{"changed":true}')
        p=self.built/self.name;p.parent.mkdir(parents=True);p.write_text('rendered')
        for n in ['editorial-policy.html','ko/editorial-policy.html']:
            p=self.built/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('rendered')
        h=sha_bytes((self.site/self.name).read_bytes())
        self.m={'kind':'editorial-maintenance','base_commit':base,'new_posts':[], 'repository_changes':{self.name:h},'changed_features':[{'source_path':self.name,'path':self.name,'sha256':h,'feature':'reference','reason':'editorial'}]}
    def tearDown(self):self.tmp.cleanup()
    def git(self,*a):return subprocess.check_output(['git','-C',str(self.site),*a],text=True,stderr=subprocess.DEVNULL)
    def write(self,n,data):p=self.site/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
    def errors(self):return scope_errors(self.m,self.site,self.built)
    def test_exact_existing_revision(self):self.assertEqual(self.errors(),[])
    def test_bilingual_scope_modes_preserve_coverage(self):
        actual=['ko/'+self.name]
        self.assertEqual(localization_scope_errors(self.m,actual),[])
        legacy=dict(self.m,kind='language-edition',new_localized_pages=actual)
        self.assertEqual(localization_scope_errors(legacy,actual),[])
        legacy['new_localized_pages']=[];self.assertTrue(localization_scope_errors(legacy,actual))
        bad=copy.deepcopy(self.m);bad['changed_features'][0]['path']='../escape';self.assertTrue(localization_scope_errors(bad,actual))
    def test_bad_current_hash(self):self.write(self.name,b'changed');self.assertTrue(self.errors())
    def test_missing_declaration(self):self.m['changed_features']=[];self.assertTrue(self.errors())
    def test_missing_counterpart(self):(self.built/self.name).unlink();self.assertTrue(self.errors())
    def test_nonempty_new_posts(self):self.m['new_posts']=[1];self.assertTrue(self.errors())
    def test_extra_file(self):self.write('extra.txt',b'x');self.assertTrue(self.errors())
    def test_missing_source_map(self):self.m['repository_changes']={};self.assertTrue(self.errors())
    def test_wrong_base(self):self.m['base_commit']='bad';self.assertTrue(self.errors())
    def test_new_article(self):
        n='posts/history/002-new.html';self.write(n,b'new');self.m['repository_changes'][n]=sha_bytes(b'new');self.assertTrue(self.errors())
    def test_theory_or_assets(self):
        for n in ['posts/theory/001-test.html','assets/new.png']:
            self.write(n,b'new');self.m['repository_changes'][n]=sha_bytes(b'new');self.assertTrue(self.errors())
    def test_private_package(self):(self.built/'qa').mkdir();self.assertTrue(self.errors())
    def test_path_traversal(self):
        for n in ['../escape','/absolute','C:/outside','a\\..\\outside']:
            with self.assertRaises(ValueError):safe_path(self.site,n)
    def test_proof_missing_and_scope_mutation(self):
        self.assertTrue(scope_errors(self.m,self.site,self.built,True))
        self.m['release_proof']={'status':'PASS','scope_sha256':canonical_scope(self.m),'record_sha256':'a'*64,'receipt_sha256':'b'*64,'review_manifest_sha256':'c'*64}
        self.assertEqual(scope_errors(self.m,self.site,self.built,True),[])
        self.m['changed_features'][0]['reason']='different';self.assertTrue(scope_errors(self.m,self.site,self.built,True))

if __name__=='__main__':unittest.main()
