"""Failure-oriented citation regression tests for the publishing checker."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qa_theory_citations import audit_html

CITE = '<a class="citation" href="#ref-1" aria-label="참고문헌 1">[1]</a>'
REF = '<div class="reference-entry" id="ref-1"><span class="reference-number">[1]</span>DOE, Nuclear Physics, §1.</div>'
def doc(body='핵종의 변화를 설명합니다. '+CITE, refs=REF):
    return '<article><p>'+body+'</p><footer class="source">'+refs+'</footer></article>'

class Citations(unittest.TestCase):
    def test_no_article(self): self.assertEqual(audit_html('<p>설명합니다.</p>'), ['ARTICLE_MISSING'])
    def test_no_footer(self): self.assertEqual(audit_html('<article><p>설명합니다.</p></article>'), ['BIBLIOGRAPHY_MISSING'])
    def test_invalid_id(self): self.assertIn('REFERENCE_ID_INVALID',audit_html(doc(refs=REF.replace('ref-1','ref-01'))))
    def test_gap(self): self.assertIn('REFERENCE_SEQUENCE',audit_html(doc(refs=REF+REF.replace('ref-1','ref-3').replace('[1]','[3]'))))
    def test_class_missing(self): self.assertIn('CITATION_CLASS_MISSING',audit_html(doc().replace('class="citation"','')))
    def test_container(self): self.assertIn('CITATION_CONTAINER',audit_html(doc().replace('<p>','<h2>').replace('</p>','</h2>')))
    def test_caption_requires_sentence(self): self.assertIn('CITATION_NOT_SENTENCE_END',audit_html(doc('반감기(년) '+CITE).replace('<p>','<figcaption>').replace('</p>','</figcaption>')))
    def test_good(self): self.assertEqual(audit_html(doc()), [])
    def test_missing(self): self.assertIn('BODY_CITATION_MISSING',audit_html(doc('설명합니다.')))
    def test_broken(self): self.assertIn('CITATION_TARGET',audit_html(doc().replace('href="#ref-1"','href="#ref-9"')))
    def test_duplicate(self): self.assertIn('DUPLICATE_ID',audit_html(doc(refs=REF+REF)))
    def test_wrong_label(self): self.assertIn('CITATION_LABEL',audit_html(doc().replace('>[1]</a>','>[9]</a>')))
    def test_wrong_ref_label(self): self.assertIn('REFERENCE_LABEL:1',audit_html(doc().replace('>[1]</span>','>[2]</span>')))
    def test_accessibility(self): self.assertIn('CITATION_ACCESSIBILITY',audit_html(doc().replace('aria-label="참고문헌 1"','')))
    def test_middle(self): self.assertIn('CITATION_NOT_SENTENCE_END',audit_html(doc('이 현상은 '+CITE+'로 설명합니다.')))
    def test_external(self): self.assertIn('BODY_EXTERNAL_SOURCE_LINK',audit_html(doc('설명합니다. '+CITE+' <a href="https://example.org">자료</a>')))
    def test_empty_source(self): self.assertIn('REFERENCE_EMPTY:1',audit_html(doc(refs=REF.replace('DOE, Nuclear Physics, §1.',''))))
    def test_intro(self): self.assertIn('SOURCE_INTRO_REVIEW_REQUIRED',audit_html(doc('NIST의 설명처럼 연결됩니다. '+CITE)))
    def test_real_actor(self): self.assertEqual(audit_html(doc('NIST·MIT·ILL 연구진은 2005년에 실험했습니다. '+CITE)),[])
    def test_device(self): self.assertEqual(audit_html(doc('ITER의 설계 목표를 설명합니다. '+CITE)),[])
    def test_repeat(self): self.assertEqual(audit_html(doc('첫 문장입니다. '+CITE+' 다음 문장입니다. '+CITE)),[])
    def test_multiple(self):
        c2=CITE.replace('ref-1','ref-2').replace('참고문헌 1','참고문헌 2').replace('[1]','[2]')
        r2=REF.replace('ref-1','ref-2').replace('[1]','[2]')
        self.assertEqual(audit_html(doc('설명합니다. '+CITE+' '+c2,REF+r2)),[])
    def test_page_only_moved(self): self.assertIn('CITATION_LABEL',audit_html(doc().replace('>[1]</a>','>[1, 49쪽]</a>')))

if __name__=='__main__': unittest.main(verbosity=2)
