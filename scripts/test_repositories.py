import unittest
from urllib.parse import urlparse, parse_qs
from repository_catalog import normalize_repositories, render_catalog
from update_repositories import fetch_repositories, update_catalog

CONFIG = {'owner': 'iamdarkls', 'featured_repositories': ['IPA-Desktop', 'DARKLS-VPN-Panel'], 'excluded_repositories': ['iamdarkls.github.io']}

def repo(name='new-project', **changes):
    return {'name': name, 'owner': {'login': 'iamdarkls'}, 'private': False, 'visibility': 'public',
            'html_url': f'https://github.com/iamdarkls/{name}', 'fork': False,
            'description': 'Description', 'language': 'Python', 'pushed_at': '2026-10-25T10:00:00Z', **changes}

class RepositoryTest(unittest.TestCase):
    def test_excludes_featured_site_private_and_foreign_repos(self):
        items = [repo(), repo('IPA-Desktop'), repo('iamdarkls.github.io'), repo('secret', private=True), repo('foreign', owner={'login': 'another'}), repo('bad-link', html_url='https://evil.example')]
        self.assertEqual([r['name'] for r in normalize_repositories(items, CONFIG)], ['new-project'])
    def test_updates_metadata_and_removes_deleted_items(self):
        previous = {'repositories': [{'name':'deleted'}], 'checked_at':'old'}
        result = update_catalog(previous, CONFIG, lambda owner: [repo(description='Changed', fork=True, archived=True)])
        self.assertEqual(len(result['repositories']), 1)
        self.assertEqual(result['repositories'][0]['description'], 'Changed')
        self.assertTrue(result['repositories'][0]['fork'])
        self.assertTrue(result['repositories'][0]['archived'])
        self.assertEqual(previous['checked_at'], 'old')
    def test_partial_pagination_failure_preserves_complete_previous_catalog(self):
        previous = {'repositories': [repo()], 'checked_at':'previous'}
        def requester(url):
            if parse_qs(urlparse(url).query)['page'] == ['1']: return [repo(str(i)) for i in range(100)]
            raise TimeoutError()
        result = update_catalog(previous, CONFIG, lambda owner: fetch_repositories(owner, requester))
        self.assertTrue(result['error'])
        self.assertEqual(result['repositories'], previous['repositories'])
        self.assertEqual(result['checked_at'], 'previous')
    def test_fetches_all_pages(self):
        calls = []
        def requester(url):
            calls.append(url)
            return [repo(str(i)) for i in range(100)] if len(calls) == 1 else [repo('last')]
        self.assertEqual(len(fetch_repositories('iamdarkls', requester)), 101)
        self.assertEqual(len(calls), 2)
    def test_empty_success_clears_previous_and_exclusions_work_during_failure(self):
        previous = {'repositories': [{'name':'iamdarkls.github.io'}, {'name':'visible'}], 'checked_at':'old'}
        self.assertEqual(update_catalog(previous, CONFIG, lambda owner: [])['repositories'], [])
        def fail(owner): raise TimeoutError()
        self.assertEqual(update_catalog(previous, CONFIG, fail)['repositories'], [{'name':'visible'}])
    def test_html_escapes_descriptions(self):
        items = normalize_repositories([repo(description='<script>alert(1)</script>')], CONFIG)
        html = render_catalog(items)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

if __name__ == '__main__': unittest.main()
