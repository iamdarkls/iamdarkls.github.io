"""Refresh all public repositories, preserving the last complete catalog on failure."""
import argparse
import copy
import json
from pathlib import Path
from repository_catalog import apply_exclusions, normalize_repositories
from update_releases import now, request_json

ROOT = Path(__file__).resolve().parents[1]


def fetch_repositories(owner, requester=request_json):
    items = []
    # Only the public user endpoint; never fetch authenticated private repository lists.
    for page in range(1, 101):
        batch = requester(f'https://api.github.com/users/{owner}/repos?type=owner&sort=full_name&per_page=100&page={page}')
        if not isinstance(batch, list):
            raise ValueError('Invalid repository response')
        items.extend(batch)
        if len(batch) < 100:
            return items
    raise ValueError('Repository pagination did not finish')


def update_catalog(previous, config, fetcher=fetch_repositories):
    result = copy.deepcopy(previous)
    result.update(schema=1, owner=config['owner'], attempted_at=now(), error=False)
    try:
        result['repositories'] = normalize_repositories(fetcher(config['owner']), config)
        result['checked_at'] = now()
    except Exception as exc:
        print(f'::warning::Repository sync failed: {type(exc).__name__}')
        result['error'] = True
        result['repositories'] = apply_exclusions(result.get('repositories', []), config)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-url')
    args = parser.parse_args()
    config = json.loads((ROOT / 'projects.json').read_text())
    output = ROOT / 'data/repositories.json'
    previous = json.loads(output.read_text()) if output.exists() else {'schema': 1, 'owner': config['owner'], 'repositories': []}
    if args.baseline_url:
        try:
            baseline = request_json(args.baseline_url)
            if (baseline.get('schema') == 1 and baseline.get('owner') == config['owner']
                    and isinstance(baseline.get('repositories'), list)
                    and baseline.get('checked_at', '') > previous.get('checked_at', '')):
                previous = baseline
        except Exception as exc:
            print(f'::warning::Published catalog unavailable: {type(exc).__name__}')
    result = update_catalog(previous, config)
    if not result.get('checked_at'):
        raise RuntimeError('No successfully fetched repository catalog available')
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(output)


if __name__ == '__main__':
    main()
