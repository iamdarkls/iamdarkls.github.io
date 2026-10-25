"""Public GitHub repositories and escaped HTML for the no-JavaScript catalog."""
from html import escape
from datetime import datetime
import re
from urllib.parse import urlparse


def valid_repository_url(value, owner, name):
    if not isinstance(value, str):
        return False
    url = urlparse(value)
    return url.scheme == 'https' and url.netloc == 'github.com' and url.path == f'/{owner}/{name}' and not url.query and not url.fragment


def normalize_repositories(items, config):
    if not isinstance(items, list):
        raise ValueError('Expected repository list')
    owner = config['owner']
    excluded = {name.casefold() for name in config.get('excluded_repositories', []) + config.get('featured_repositories', [])}
    repos = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError('Invalid repository item')
        name = item.get('name', '')
        if (item.get('private') is not False or item.get('visibility', 'public') != 'public'
                or item.get('owner', {}).get('login', '').casefold() != owner.casefold()
                or not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or name.casefold() in excluded
                or not valid_repository_url(item.get('html_url'), owner, name)):
            continue
        repos[name.casefold()] = {
            'name': name, 'url': item['html_url'],
            'description': str(item.get('description') or '')[:1000],
            'language': str(item.get('language') or '')[:80],
            'fork': bool(item.get('fork')), 'archived': bool(item.get('archived')),
            'pushed_at': item.get('pushed_at') or None,
            'updated_at': item.get('updated_at') or None,
        }
    # Stable alphabetical tie-breaker; original projects before forks, recent commits first.
    result = sorted(repos.values(), key=lambda repo: repo['name'].casefold())
    result.sort(key=lambda repo: repo['pushed_at'] or '', reverse=True)
    result.sort(key=lambda repo: repo['fork'])
    return result


def apply_exclusions(repositories, config):
    excluded = {name.casefold() for name in config.get('excluded_repositories', []) + config.get('featured_repositories', [])}
    return [repo for repo in repositories if isinstance(repo, dict) and repo.get('name', '').casefold() not in excluded]


def render_catalog(repositories):
    rows = []
    for repo in repositories:
        name = escape(repo['name'])
        labels = [escape(repo['language'] or 'Язык не указан'), 'форк' if repo['fork'] else 'проект']
        if repo['archived']:
            labels.append('архив')
        date_html = ''
        if repo.get('pushed_at'):
            try:
                value = datetime.fromisoformat(repo['pushed_at'].replace('Z', '+00:00'))
                date_html = f'<span class="repo-updated">Последний коммит: <time datetime="{escape(repo["pushed_at"], quote=True)}">{value:%d.%m.%Y}</time></span>'
            except (ValueError, TypeError):
                pass
        rows.append(f'<article class="repo-row" data-category="{"forks" if repo["fork"] else "other"}">'
                    f'<span class="repo-icon" aria-hidden="true">{"⑂" if repo["fork"] else "↗"}</span>'
                    f'<div><h3>{name}</h3><span class="repo-kind">{" · ".join(labels)}</span></div>'
                    f'<div class="repo-description"><p>{escape(repo["description"] or "Описание пока не добавлено на GitHub.")}</p>{date_html}</div>'
                    f'<a class="text-link" href="{escape(repo["url"], quote=True)}" aria-label="{name} на GitHub">GitHub ↗</a></article>')
    return '\n'.join(rows) or '<p class="catalog-empty">Других публичных репозиториев пока нет.</p>'
