import copy
import unittest
from update_releases import select_channels, update_data

def release(tag, date="2026-10-24T10:00:00Z", **kwargs):
    repo = "IPA-Desktop"
    return {"tag_name": tag, "published_at": date, "html_url": f"https://github.com/iamdarkls/{repo}/releases/tag/{tag}", "assets": [], **kwargs}

class ReleasesTest(unittest.TestCase):
    def test_separates_tools_and_prereleases_and_sorts_by_publication(self):
        data = select_channels([release("v0.3.1"), release("device-tools-v1.0.3"), release("v0.4.0-beta", prerelease=True), release("v0.3.2", "2026-10-25T10:00:00Z"), release("v9.0.0", draft=True)], "IPA-Desktop")
        self.assertEqual(data["ipa"]["latest"]["tag"], "v0.3.2")
        self.assertEqual(data["tools"]["latest"]["tag"], "device-tools-v1.0.3")
        self.assertEqual(data["ipa"]["preview"]["tag"], "v0.4.0-beta")
    def test_failed_fetch_preserves_snapshot_and_marks_error(self):
        previous = {"projects": {"ipa": {"checked_at": "old", "latest": {"tag": "v1"}}}}
        original = copy.deepcopy(previous)
        def fail(repo): raise TimeoutError()
        result = update_data(previous, fail)
        self.assertEqual(result["projects"], previous["projects"])
        self.assertEqual(previous, original)
        self.assertEqual(result["errors"], ["ipa", "vpn"])
    def test_rejects_untrusted_links_and_source_archives(self):
        r = release("v0.3.2", assets=[{"name":"IPA-Desktop-0.3.2-Windows.zip", "browser_download_url":"https://evil.example/file"}])
        data = select_channels([r, release("device-tools-v1.0.3")], "IPA-Desktop")
        self.assertEqual(data["ipa"]["latest"]["assets"], [])
    def test_missing_channel_keeps_previous_instead_of_erasing(self):
        with self.assertRaises(ValueError): select_channels([release("v0.3.2")], "IPA-Desktop")

if __name__ == "__main__": unittest.main()
