import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote
from site_pages import feed_items, feedback, project_page

ROOT = Path(__file__).resolve().parents[1]

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids=[]; self.urls=[]; self.h1=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a: self.ids.append(a['id'])
        if tag == 'h1': self.h1 += 1
        for name in ('href','src'):
            if name in a: self.urls.append(a[name])

class SitePagesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable,str(ROOT/'scripts/build_site.py')],check=True,stdout=subprocess.DEVNULL)
    def test_all_local_links_and_assets_exist_and_ids_are_unique(self):
        out=ROOT/'_site'
        pages=list(out.rglob('index.html'))
        self.assertEqual(len(pages),6)
        for page in pages:
            parser=PageParser();parser.feed(page.read_text())
            self.assertEqual(parser.h1,1,str(page))
            self.assertEqual(len(parser.ids),len(set(parser.ids)),str(page))
            for value in parser.urls:
                url=urlparse(value)
                if url.scheme or url.netloc: continue
                target=(out/unquote(url.path).lstrip('/')) if url.path.startswith('/') else page.parent/unquote(url.path)
                if target.is_dir(): target=target/'index.html'
                self.assertTrue(target.exists(),f'{page}: {value}')
                if url.fragment:
                    p=PageParser();p.feed(target.read_text())
                    self.assertIn(url.fragment,p.ids,f'{page}: {value}')
    def test_locale_routes_and_feedback_stay_on_the_right_project(self):
        for slug,repo in [('ipa-desktop','IPA-Desktop'),('vpn-panel','DARKLS-VPN-Panel')]:
            ru=(ROOT/f'_site/projects/{slug}/index.html').read_text()
            en=(ROOT/f'_site/en/projects/{slug}/index.html').read_text()
            self.assertIn(f'href="/en/projects/{slug}/"',ru)
            self.assertIn(f'href="/projects/{slug}/"',en)
            self.assertIn(f'{repo}/issues/new?',en)
            self.assertIn('What+happened',en)
            self.assertIn('type="application/json"',en)
            self.assertIn('src="/app.en.js"',en)
    def test_feed_sorts_across_channels_and_deduplicates(self):
        def release(tag,date): return {'tag':tag,'published_at':date,'url':f'https://github.com/iamdarkls/IPA-Desktop/releases/tag/{tag}'}
        old=release('v1.0.0','2026-01-01T00:00:00Z');new=release('device-tools-v2.0.0','2026-02-01T00:00:00Z')
        items=feed_items({'projects':{'ipa':{'latest':old,'history':[old]},'tools':{'latest':new}}})
        self.assertEqual(len(items),2)
        self.assertEqual(items[0]['channel'],'tools')
    def test_external_vpn_project_is_present_in_both_languages(self):
        for lang in ('', 'en/'):
            home=(ROOT/f'_site/{lang}index.html').read_text()
            self.assertIn('data-project="website"',home)
            self.assertIn('href="https://darkls-vpn.ru/"',home)
        self.assertFalse((ROOT/'_site/assets/screenshots/ipa-interface-detail.jpg').exists())

    def test_gallery_is_labelled_and_english_app_is_translated(self):
        ipa=(ROOT/'_site/en/projects/ipa-desktop/index.html').read_text()
        vpn=(ROOT/'_site/en/projects/vpn-panel/index.html').read_text()
        self.assertIn('not published yet',ipa)
        self.assertNotIn('ipa-interface-detail.jpg',ipa)
        self.assertIn('demonstration data',vpn)
        app=(ROOT/'_site/app.en.js').read_text()
        self.assertNotRegex(app,r'[А-Яа-яЁё]')
        self.assertIn('en-GB',app)

if __name__=='__main__':unittest.main()
