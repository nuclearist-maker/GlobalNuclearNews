"""Phone portrait twin (<id>_m) regressions (2026-11-26 Codex workflow review r3 F01-F03)."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bs4 import BeautifulSoup  # noqa: E402
import import_korean as ik  # noqa: E402
import build_bilingual as bb  # noqa: E402


class PhoneTwinTests(unittest.TestCase):
    def test_srcset_twins_are_collected_for_deployment(self):  # r3 F01
        page = ('<picture><source media="(max-width: 600px)" srcset="/GlobalNuclearNews/assets/images/ko/news/s/body_01_m.avif" '
                'width="1080" height="1350"/><img src="/GlobalNuclearNews/assets/images/ko/news/s/body_01.avif"/></picture>')
        self.assertEqual(bb.image_refs(page), {'/GlobalNuclearNews/assets/images/ko/news/s/body_01.avif',
                                              '/GlobalNuclearNews/assets/images/ko/news/s/body_01_m.avif'})

    def test_plain_markdown_image_gets_figure_around_picture(self):  # r3 F02
        soup = BeautifulSoup('<p><img src="a.png"/></p>', 'html.parser')
        img = soup.img
        box = ik.add_twin(soup, img, 'a_m.avif')
        box.wrap(soup.new_tag('figure'))
        fig = soup.figure
        self.assertEqual(fig.contents[0].name, 'picture')
        self.assertEqual([c.name for c in fig.picture.contents], ['source', 'img'])

    def test_existing_picture_input_is_rebuilt_not_left_without_srcset(self):  # r3 F02
        # import_korean strips srcset, then removes <source> and unwraps <picture>; add_twin rebuilds one picture
        soup = BeautifulSoup('<figure><picture><source srcset="x.png"/><img src="a.png"/></picture></figure>', 'html.parser')
        for el in soup.find_all():
            if 'srcset' in el.attrs:
                del el['srcset']
        for el in soup.find_all('source'):
            el.decompose()
        for el in soup.find_all('picture'):
            el.unwrap()
        ik.add_twin(soup, soup.img, 'a_m.avif')
        self.assertEqual(len(soup.find_all('picture')), 1)
        self.assertEqual(soup.source['srcset'], 'a_m.avif')

    def test_cache_key_changes_when_only_a_twin_is_added(self):  # r3 F03, r4 F02 (sibling images/ folder)
        with tempfile.TemporaryDirectory() as d:
            draft = Path(d) / 'drafts' / 'post'
            images = Path(d) / 'drafts' / 'images'  # locate() also resolves base.parent/images
            (draft / 'assets').mkdir(parents=True); images.mkdir()
            a = draft / 'assets/body_01.png'; b = images / 'thumbnail_01.png'
            a.write_bytes(b'a'); b.write_bytes(b't')
            before = ik.twin_state([a, b])
            (images / 'thumbnail_01_m.png').write_bytes(b'm')
            after = ik.twin_state([a, b])
            self.assertNotEqual(before, after)
            (images / 'thumbnail_01_m.png').write_bytes(b'n')
            self.assertNotEqual(after, ik.twin_state([a, b]))
            self.assertEqual(ik.twin_of(a).name, 'body_01_m.png')

    def test_cache_miss_when_a_landscape_source_changes(self):  # r4 F01
        with tempfile.TemporaryDirectory() as d:
            a = Path(d) / 'body_01.png'; a.write_bytes(b'a')
            images = [{'source': str(a), 'source_sha256': ik.sha(a)}]
            self.assertTrue(ik.sources_current(images))
            a.write_bytes(b'changed')
            self.assertFalse(ik.sources_current(images))
            a.unlink()
            self.assertFalse(ik.sources_current(images))

    def test_any_attribute_quoting_is_collected(self):  # r5 F03
        page = ("<img src='/GlobalNuclearNews/assets/images/ko/news/s/a.avif'>"
                "<source SRCSET=/GlobalNuclearNews/assets/images/ko/news/s/a_m.avif>")
        self.assertEqual(bb.image_refs(page), {'/GlobalNuclearNews/assets/images/ko/news/s/a.avif',
                                              '/GlobalNuclearNews/assets/images/ko/news/s/a_m.avif'})

    def test_copy_images_needs_only_an_existing_safe_file(self):  # 2026-11-26: no hash-manifest comparison
        with tempfile.TemporaryDirectory() as d:
            root, out = Path(d) / 'repo', Path(d) / 'out'
            img = root / 'assets/images/ko/news/s'; img.mkdir(parents=True); out.mkdir()
            (img / 'a.avif').write_bytes(b'land')
            bb.copy_images(bb.image_refs('<img src="/GlobalNuclearNews/assets/images/ko/news/s/a.avif">'), root, out)
            self.assertEqual((out / 'assets/images/ko/news/s/a.avif').read_bytes(), b'land')
            with self.assertRaises(ValueError):  # missing file
                bb.copy_images({'/GlobalNuclearNews/assets/images/ko/news/s/none.avif'}, root, out)
            # outside assets/images/ko: a REAL file reached through '..', so only the path check can reject it
            (root / 'tools').mkdir(); (root / 'tools/x.py').write_bytes(b'code')
            escape = '/GlobalNuclearNews/assets/images/ko/../../../tools/x.py'
            self.assertTrue((root / escape.removeprefix('/GlobalNuclearNews/')).resolve().is_file())
            with self.assertRaises(ValueError):
                bb.copy_images({escape}, root, out)
            self.assertFalse((out / 'tools/x.py').exists())

    def test_asset_list_hash_mismatch_does_not_fail_build(self):  # F01: install no longer compares assets.json hashes
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            img = root / 'assets/images/ko/news/s'; img.mkdir(parents=True)
            (img / 'a.avif').write_bytes(b'new pixels')
            (root / 'tools').mkdir(); (root / 'tools/x.py').write_bytes(b'code')
            bb.check_assets(root, {'assets/images/ko/news/s/a.avif': '0' * 64})  # stale hash: accepted
            with self.assertRaises(ValueError):  # missing file
                bb.check_assets(root, {'assets/images/ko/news/s/none.avif': '0' * 64})
            with self.assertRaises(ValueError):  # real file outside assets/images
                bb.check_assets(root, {'assets/images/../../tools/x.py': '0' * 64})


if __name__ == '__main__':
    unittest.main()
