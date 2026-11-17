import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from build_pe import expected_pages,load,record_digest
from check_pe import scope_errors
from build_bilingual import digest

class PEGuards(unittest.TestCase):
    def test_missing_article_scope_and_extra_page_fail(self):
        rows=[{'id':'Y2026-1-01','group':'exam','year':2026,'url':'ko/pe/posts/y2026-1-01.html'}]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for rel in expected_pages(rows):
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('page')
            scope={'kind':'pe-board','new_posts':[rows[0]['url']],'changed_features':[{'path':'index.html','feature':'default','reason':'Korean'}]}
            with patch('check_pe.load',return_value=rows):
                self.assertEqual(scope_errors(scope,root,root),[])
                scope['new_posts']=[]
                self.assertIn('PE article scope mismatch',scope_errors(scope,root,root))
                (root/'ko/pe/unlisted.html').write_text('extra')
                self.assertIn('PE generated page set mismatch',scope_errors(scope,root,root))

    def test_changed_body_and_unsafe_identifier_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'locales/ko/pe';(base/'bodies').mkdir(parents=True)
            body=base/'bodies/c-fm-001.html';body.write_text('original')
            row={'id':'C-FM-001','group':'concept','body':'bodies/c-fm-001.html','url':'ko/pe/posts/c-fm-001.html','body_sha256':digest(body),'assets':{}}
            (base/'posts.json').write_text(json.dumps([row]));self.assertEqual(len(load(root)),1)
            body.write_text('modified')
            with self.assertRaisesRegex(ValueError,'changed body'):load(root)
            row['id']='../escape';(base/'posts.json').write_text(json.dumps([row]))
            with self.assertRaisesRegex(ValueError,'invalid/duplicate'):load(root)

    def test_years_are_not_hardcoded(self):
        pages=expected_pages([{'group':'exam','year':2030,'url':'ko/pe/posts/y2030-1-01.html'}])
        self.assertIn('ko/pe/exams/2030.html',pages)

    def test_existing_metadata_change_needs_declared_revision(self):
        row={'id':'C-FM-001','group':'concept','url':'ko/pe/posts/c-fm-001.html','title':'before'}
        previous={row['url']:record_digest(row)};row['title']='after'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for rel in expected_pages([row]):
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('page')
            scope={'kind':'pe-board','new_posts':[],'previous_posts':previous,'changed_features':[{'path':'index.html','feature':'routing','reason':'Korean default'}]}
            with patch('check_pe.load',return_value=[row]):
                self.assertTrue(any('Undeclared PE revision' in e for e in scope_errors(scope,root,root)))
                scope['changed_features'].append({'path':row['url'],'feature':'revision','reason':'New final'})
                self.assertEqual(scope_errors(scope,root,root),[])

if __name__=='__main__':unittest.main()
