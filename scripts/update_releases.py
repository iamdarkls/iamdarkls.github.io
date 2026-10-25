"""Fetch public release metadata. No dependencies, no credentials in output."""
import argparse
import copy
import datetime as dt
import json
import os
from pathlib import Path
import re
import urllib.request
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REPOS = {"ipa": "IPA-Desktop", "vpn": "DARKLS-VPN-Panel"}
SCHEMA = 1

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def safe_url(value, repo, download=False):
    value = value if isinstance(value, str) else ""
    url = urlparse(value)
    prefix = f"/iamdarkls/{repo}/releases/" + ("download/" if download else "tag/")
    return value if url.scheme == "https" and url.netloc == "github.com" and url.path.startswith(prefix) else ""

def compact_release(release, repo, channel):
    patterns = {"ipa": r"IPA-Desktop-.+-Windows\.zip", "tools": r"IPA-DeviceTools-.+-Windows-x64\.zip", "vpn": r"DARKLS-VPN-Panel-.+\.zip"}
    assets = []
    for asset in release.get("assets", []):
        if re.fullmatch(patterns[channel], asset.get("name", "")):
            url = safe_url(asset.get("browser_download_url"), repo, download=True)
            if url:
                assets.append({"name": asset["name"], "url": url, "size": asset.get("size", 0)})
    tag = release["tag_name"]
    body = str(release.get("body") or "")[:30000]
    return {"tag": tag, "name": str(release.get("name") or tag), "published_at": release["published_at"],
            "prerelease": bool(release.get("prerelease")), "url": safe_url(release.get("html_url"), repo),
            "notes": body, "assets": assets}

def select_channels(releases, repo):
    if not isinstance(releases, list):
        raise ValueError("Expected release list")
    channels = {"ipa": [], "tools": []} if repo == "IPA-Desktop" else {"vpn": []}
    for release in releases:
        if release.get("draft") or not release.get("published_at"):
            continue
        tag = release.get("tag_name", "")
        channel = "tools" if tag.startswith("device-tools-v") else ("ipa" if repo == "IPA-Desktop" else "vpn")
        pattern = r"device-tools-v\d+\.\d+\.\d+.*" if channel == "tools" else r"v\d+\.\d+\.\d+.*"
        if channel not in channels or not re.fullmatch(pattern, tag):
            continue
        item = compact_release(release, repo, channel)
        if item["url"]:
            channels[channel].append(item)
    result = {}
    for channel, items in channels.items():
        items.sort(key=lambda item: item["published_at"], reverse=True)
        stable = [item for item in items if not item["prerelease"]]
        preview = [item for item in items if item["prerelease"]]
        if not stable:
            raise ValueError(f"No stable releases for {channel}")
        result[channel] = {"latest": stable[0], "preview": preview[0] if preview else None, "history": items[:6]}
    return result

def request_json(url, authenticated=False):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "DARKLS-portfolio-release-sync"}
    if authenticated and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
        return json.load(response)

def fetch_releases(repo):
    releases = []
    for page in range(1, 11):
        batch = request_json(f"https://api.github.com/repos/iamdarkls/{repo}/releases?per_page=100&page={page}", True)
        if not isinstance(batch, list):
            raise ValueError("Invalid GitHub response")
        releases.extend(batch)
        if len(batch) < 100:
            return releases
    # Latest channels are covered by the first 1000 releases, older history is not needed.
    return releases

def update_data(previous, fetcher=fetch_releases):
    result = copy.deepcopy(previous)
    result["schema"] = SCHEMA
    result["attempted_at"] = now()
    result.setdefault("projects", {})
    result["errors"] = []
    for key, repo in REPOS.items():
        try:
            channels = select_channels(fetcher(repo), repo)
            checked_at = now()
            for channel, data in channels.items():
                result["projects"][channel] = {**data, "checked_at": checked_at}
        except Exception as exc:
            # Keep every previously valid channel for this repository.
            print(f"::warning::Release sync failed for {repo}: {type(exc).__name__}")
            result["errors"].append(key)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-url", help="Previous published snapshot, used as fallback")
    args = parser.parse_args()
    output = ROOT / "data/releases.json"
    previous = json.loads(output.read_text()) if output.exists() else {"schema": SCHEMA, "projects": {}}
    if args.baseline_url:
        try:
            baseline = request_json(args.baseline_url)
            if baseline.get("schema") == SCHEMA and isinstance(baseline.get("projects"), dict):
                for channel, data in baseline["projects"].items():
                    if channel in {"ipa", "vpn", "tools"} and isinstance(data, dict) and data.get("checked_at", "") > previous.get("projects", {}).get(channel, {}).get("checked_at", ""):
                        previous.setdefault("projects", {})[channel] = data
        except Exception as exc:
            print(f"::warning::Published baseline unavailable: {type(exc).__name__}")
    result = update_data(previous)
    if not all(channel in result["projects"] for channel in ("ipa", "vpn", "tools")):
        raise RuntimeError("Missing release data and no usable fallback")
    output.parent.mkdir(exist_ok=True)
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(output)

if __name__ == "__main__":
    main()
