import tempfile
import unittest
from pathlib import Path
from news_spacing_gate import html_errors,text_errors

class NumericSpacingTests(unittest.TestCase):
    def test_repeated_published_defects(self):
        for text in ['직전4년','2026년7월15일','50mSv/년','약5km','전기1MWh','추정합니다.2024년','달러,3%']:
            with self.subTest(text=text):self.assertTrue(text_errors(text))
    def test_valid_numbers_and_identifiers(self):
        for text in ['직전 4년', '2026년 7월 15일','50 mSv/년','AP1000 원전 3기','U-235, SSR-5, NUREG-0713, ML26069A604','제1조 및 제20조의2','2.99%, 10%, 100%','1,047만 9천 달러','20·30·40·50 mSv','§20.1205']:
            with self.subTest(text=text):self.assertFalse(text_errors(text),text_errors(text))
    def test_actual_dom_text_and_attributes(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'test.html'
            p.write_text('<style>x1mSv</style><h1>직전<strong>4년</strong></h1><img alt="평균1.6mSv"><p>50 mSv</p><script>9mSv</script>',encoding='utf-8')
            errors=html_errors(p)
            self.assertEqual(len(errors),3)
            self.assertFalse(any('9mSv' in e['context'] for e in errors))

if __name__=='__main__':unittest.main()
