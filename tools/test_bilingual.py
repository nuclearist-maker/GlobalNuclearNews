import unittest,tempfile,json
from pathlib import Path
from bs4 import BeautifulSoup
from build_bilingual import switch,translate,localize,install,BASE,KBASE
from public_files import collect

class BilingualTests(unittest.TestCase):
    def test_same_article_round_trip(self):
        text='<html lang="en"><head><title>T</title></head><body><header class="masthead"></header></body></html>'
        en=BeautifulSoup(switch(text,'posts/news/example.html','en'),'html.parser')
        ko=BeautifulSoup(switch(text,'posts/news/example.html','ko'),'html.parser')
        self.assertEqual(en.select_one('a[hreflang=ko]')['href'],'../../ko/posts/news/example.html')
        self.assertEqual(ko.select_one('a[hreflang=en]')['href'],'../../../posts/news/example.html')
        self.assertEqual(ko.select_one('link[hreflang=x-default]')['href'],BASE+'posts/news/example.html')
        self.assertEqual(ko.select_one('[aria-current=true]')['hreflang'],'ko')
    def test_translation_preserves_enum_and_link(self):
        text='<html><head></head><body><option value="Operational">Operational</option><a href="Operational.html">Next</a><script>const x="Next";</script></body></html>'
        s=BeautifulSoup(localize(text,{'Operational':'운영','Next':'다음'}),'html.parser')
        self.assertEqual(s.option['value'],'Operational');self.assertEqual(s.option.text,'운영')
        self.assertEqual(s.a['href'],'Operational.html');self.assertEqual(s.script.string,'const x="Next";')
        self.assertEqual(s.html['lang'],'ko')
    def test_dynamic_static_labels(self):
        self.assertEqual(translate('417 records · showing the first 10',{}),'417건 · 첫 10건 표시')
        self.assertEqual(translate('Nuclear Theory | GlobalNuclearNews',{'Nuclear Theory':'원자력이론'}),'원자력이론 | GlobalNuclearNews')
    def test_incomplete_pair_fails_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'locales/ko').mkdir(parents=True);(r/'assets').mkdir()
            for n in ['ui','reactors','categories']:(r/f'locales/ko/{n}.json').write_text('{}')
            (r/'assets/reactor-display.js').write_text('window.REACTOR_DISPLAY = {"inventory":{"records":[]}};')
            (r/'locales/ko/posts.json').write_text('[]');(r/'assets/app.js').write_text('const posts = [{"url":"posts/news/a.html"}];')
            with self.assertRaisesRegex(ValueError,'incomplete'):install(r,r/'_site')
            self.assertFalse((r/'_site').exists())
    def test_closure_repeated_assets_and_directory_links(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'assets').mkdir();(r/'posts').mkdir();(r/'archive').mkdir()
            (r/'index.html').write_text('<img src="assets/a.png"><img src="assets/a.png?v=2"><a href="archive/">archive</a>')
            (r/'assets/a.png').write_bytes(b'example');(r/'archive/index.html').write_text('<a href="../index.html">home</a>')
            files=collect(r)
            self.assertEqual(len(files),3)
    def test_closure_missing_and_escaping_asset_fail(self):
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);(r/'posts').mkdir()
            for href,message in [('missing.png','Missing'),('../outside.png','escapes')]:
                (r/'index.html').write_text('<img src="'+href+'">')
                with self.assertRaisesRegex(ValueError,message):collect(r)
if __name__=='__main__':unittest.main()
