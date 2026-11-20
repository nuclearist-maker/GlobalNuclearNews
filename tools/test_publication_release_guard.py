import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import publication_release_guard as guard


class ReleaseGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.repo=Path(self.tmp.name);self.git('init','-q');self.git('config','user.email','test@example.invalid');self.git('config','user.name','Fixture')
        (self.repo/'article.html').write_text('old',encoding='utf8');self.git('add','.');self.git('commit','-qm','base');self.base=self.git('rev-parse','HEAD')
        (self.repo/'article.html').write_text('new',encoding='utf8')
        self.path=self.repo/'qa/deployments/publication.json';self.path.parent.mkdir(parents=True)
        self.manifest={'base_commit':self.base,'release_files':{'article.html':guard.digest(b'new','article.html')},'verification':{'local_publish_gate_sha256':'a'*64,'independent_review_sha256':'b'*64}}

    def git(self,*args):return subprocess.check_output(['git','-C',str(self.repo),*args],text=True).strip()

    def commit(self):
        self.manifest['verification']['reviewed_release_sha256']=guard.scope_digest(self.manifest)
        self.path.write_text(json.dumps(self.manifest),encoding='utf8');self.git('add','.');self.git('commit','-qm','release')

    def test_valid(self):
        self.commit();self.assertEqual(guard.verify(self.repo)['status'],'PASS')

    def test_uncoordinated_extra_file_fails_without_hook(self):
        (self.repo/'unreviewed.txt').write_text('extra');self.commit()
        with self.assertRaises(ValueError):guard.verify(self.repo)

    def test_missing_proof(self):
        self.manifest['verification']={};self.commit()
        with self.assertRaises(ValueError):guard.verify(self.repo)

    def test_modified_reviewed_file(self):
        self.commit();(self.repo/'article.html').write_text('wrong')
        with self.assertRaises(ValueError):guard.verify(self.repo)

    def test_wrong_base(self):
        self.manifest['base_commit']='c'*40;self.commit()
        with self.assertRaises(ValueError):guard.verify(self.repo)

    def test_shallow_checkout_reads_actual_parent(self):
        self.commit();head=self.git('rev-parse','HEAD');(self.repo/'.git/shallow').write_text(head+'\n')
        self.assertEqual(guard.verify(self.repo)['status'],'PASS')

    def test_later_remote_ref_blocks_obsolete_deploy(self):
        self.commit();original=subprocess.check_output
        def output(cmd,**kwargs):
            if 'ls-remote' in cmd:return 'd'*40+'\trefs/heads/main\n'
            return original(cmd,**kwargs)
        with patch.object(guard.subprocess,'check_output',side_effect=output):
            with self.assertRaises(ValueError):guard.verify(self.repo,latest=True)


if __name__=='__main__':unittest.main()
