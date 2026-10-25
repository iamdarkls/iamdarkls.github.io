"""Generate bilingual project pages and release feed using standard-library tools."""
from html import escape as e
import json
from pathlib import Path
import re
from urllib.parse import urlencode

BASE = 'https://iamdarkls.github.io'
REPO_BASE = 'https://github.com/iamdarkls/'
SOCIAL = [('Telegram · новости', 'Telegram · updates', 'https://t.me/graveofthedarkls'), ('Личный Telegram', 'Personal Telegram', 'https://t.me/iamdarkls'), ('X / Twitter', 'X / Twitter', 'https://x.com/iamdarkls')]


def feedback(repo, lang):
    bug = {'ru': ('Сообщить об ошибке', 'Что произошло?\n\nКак повторить?\n\nВерсия приложения и система:\n\nОжидалось:\n\nФактический результат:\n'), 'en': ('Report a bug', 'What happened?\n\nSteps to reproduce:\n\nApp version and operating system:\n\nExpected result:\n\nActual result:\n')}
    idea = {'ru': ('Предложить идею', 'Какую задачу хочется решить?\n\nКакое поведение предлагается?\n\n'), 'en': ('Suggest an idea', 'What problem would you like to solve?\n\nWhat behavior would you suggest?\n\n')}
    return '<div class="feedback-links">' + ' '.join(f'<a href="{e(REPO_BASE + repo + "/issues/new?" + urlencode({"title": prefix, "body": item[lang][1]}), quote=True)}">{item[lang][0]} ↗</a>' for item, prefix in [(bug, '[Bug] '), (idea, '[Idea] ')]) + '</div>'


def social_links(lang):
    return ''.join(f'<a class="button" href="{url}">{ru if lang == "ru" else en} ↗</a>' for ru, en, url in SOCIAL)


def feed_items(data):
    items = {}
    for key, title in [('ipa', 'IPA Desktop'), ('vpn', 'DARKLS VPN Panel'), ('tools', 'device-tools')]:
        channel = data.get('projects', {}).get(key, {})
        for release in channel.get('history', []) + [channel.get('latest'), channel.get('preview')]:
            if not release:
                continue
            if not release.get('url', '').startswith(REPO_BASE + ('DARKLS-VPN-Panel' if key == 'vpn' else 'IPA-Desktop') + '/releases/tag/'):
                continue
            items[(key, release['tag'])] = {**release, 'channel': key, 'project': title}
    return sorted(items.values(), key=lambda r: r['published_at'], reverse=True)[:12]


def render_feed(data, lang):
    rows = []
    for release in feed_items(data):
        summary = re.sub(r'[#*`]', '', release.get('notes', '')).replace('\n', ' ').strip()
        badge = ('Предварительный' if lang == 'ru' else 'Preview') if release.get('prerelease') else ('Стабильный' if lang == 'ru' else 'Stable')
        rows.append(f'<li class="feed-item" data-feed-channel="{release["channel"]}"><div class="feed-meta"><span>{release["project"]}</span><time datetime="{e(release["published_at"])}">{e(release["published_at"][:10])}</time></div><h3><a href="{e(release["url"], quote=True)}">{e(release["tag"])} ↗</a><span class="feed-badge">{badge}</span></h3><p>{e(summary[:260])}{"…" if len(summary) > 260 else ""}</p></li>')
    return '<ol class="release-feed" id="release-feed">' + ''.join(rows) + '</ol>'


def dialog(lang):
    close = 'Закрыть изображение' if lang == 'ru' else 'Close image'
    return f'<dialog class="lightbox" id="image-dialog" aria-labelledby="image-caption"><div class="lightbox-head"><p id="image-caption"></p><button type="button" id="image-close" aria-label="{close}">×</button></div><img id="image-full" alt=""></dialog>'


def project_page(project, key, lang, releases):
    en = lang == 'en'
    c = project[lang]
    prefix = '/en' if en else ''
    home = '/en/' if en else '/'
    counterpart = f'/projects/{project["slug"]}/' if en else f'/en/projects/{project["slug"]}/'
    path = f'{prefix}/projects/{project["slug"]}/'
    ru_path = f'/projects/{project["slug"]}/'
    en_path = f'/en/projects/{project["slug"]}/'
    labels = ['Features', 'Requirements', 'Get started', 'Screenshots', 'Frequently asked questions', 'Releases'] if en else ['Возможности', 'Требования', 'Как начать', 'Скриншоты', 'Частые вопросы', 'Выпуски']
    snapshots = json.dumps(releases, ensure_ascii=False).replace('<', '\\u003c')
    latest = releases['projects'][key]['latest']
    sections = ''.join(f'<article><h3>{e(title)}</h3><p>{e(body)}</p></article>' for title, body in c['features'])
    requirements = ''.join(f'<li>{e(item)}</li>' for item in c['requirements'])
    steps = ''.join(f'<li>{e(item)}</li>' for item in c['steps'])
    faq = ''.join(f'<details><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q, a in c['faq'])
    gallery = ''.join(f'<figure><a data-lightbox href="/assets/screenshots/{filename}" aria-label="{e(caption, quote=True)}"><img src="/assets/screenshots/{filename}" alt="{e(caption, quote=True)}" loading="lazy" width="{720 if key == "ipa" else 1349}" height="{960 if key == "ipa" else 936}"><span class="zoom-hint">{"Увеличить ↗" if not en else "Enlarge ↗"}</span></a><figcaption>{e(caption)}</figcaption></figure>' for filename, caption in c['screenshots'])
    docs = REPO_BASE + project['repo'] + ('#readme' if key == 'ipa' else '/blob/main/docs/USER_GUIDE.md')
    return f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#101110"><title>{project['name']} — DARKLS</title><meta name="description" content="{e(c['intro'], quote=True)}"><meta property="og:title" content="{project['name']} — DARKLS"><meta property="og:description" content="{e(c['intro'], quote=True)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}{path}"><link rel="canonical" href="{BASE}{path}"><link rel="alternate" hreflang="ru" href="{BASE}{ru_path}"><link rel="alternate" hreflang="en" href="{BASE}{en_path}"><link rel="icon" href="/favicon.svg"><link rel="stylesheet" href="/styles.css"><script>try{{document.documentElement.dataset.theme=localStorage.getItem('darkls-theme')||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark')}}catch{{}}</script></head><body><a class="skip" href="#project-content">{'К содержимому' if not en else 'Skip to content'}</a><div class="wrap"><header class="header"><a class="brand" href="{home}">DARKLS<span>↗</span></a><nav aria-label="{'Навигация' if not en else 'Navigation'}"><a href="{home}">{'Все проекты' if not en else 'All projects'}</a><a class="nav-extra" href="{home}#updates">{'Обновления' if not en else 'Updates'}</a><a class="lang-switch" href="{counterpart}" lang="{'ru' if en else 'en'}" hreflang="{'ru' if en else 'en'}">{'RU' if en else 'EN'}</a><button class="theme-toggle" id="theme-toggle" type="button" aria-label="{'Переключить тему' if not en else 'Switch theme'}" hidden>◐ <span>{'Тема' if not en else 'Theme'}</span></button></nav></header><main id="project-content"><section class="project-hero"><a class="back-link" href="{home}">← {'Все проекты' if not en else 'All projects'}</a><p class="eyebrow"><span class="dot"></span>{project['platform']}</p><p class="project-wordmark">{project['name']}</p><h1>{e(c['lead'])}</h1><p class="intro">{e(c['intro'])}</p><div class="actions project-hero-actions"><a class="button primary {'warm' if key == 'vpn' else ''}" data-download="{key}" href="{e(latest['url'], quote=True)}">{'Скачать' if not en else 'Download'} ↓</a><a class="button" href="{REPO_BASE}{project['repo']}">GitHub ↗</a><a class="button" href="{docs}">{'Документация' if not en else 'Documentation'} ↗</a></div>{feedback(project['repo'],lang)}</section><nav class="page-toc" aria-label="{'Разделы проекта' if not en else 'On this page'}">{''.join(f'<a href="#{id}">{label}</a>' for id,label in zip(['features','requirements','start','screenshots','faq','releases'], labels))}</nav><section class="detail-section" id="features"><h2>{labels[0]}</h2><div class="feature-grid">{sections}</div></section><section class="detail-columns"><div class="detail-section" id="requirements"><h2>{labels[1]}</h2><ul class="requirements">{requirements}</ul></div><div class="detail-section" id="start"><h2>{labels[2]}</h2><ol class="setup-steps">{steps}</ol></div></section><section class="detail-section" id="screenshots"><h2>{labels[3]}</h2><p class="section-note">{e(c['gallery_note'])}</p><div class="screenshot-grid {'screenshot-detail' if key=='ipa' else ''}">{gallery}</div></section><section class="detail-section" id="faq"><h2>{labels[4]}</h2><div class="faq-list">{faq}</div></section><section class="detail-section" id="releases"><h2>{labels[5]}</h2><div class="project-release-grid"><section class="release-box" data-release="{key}" aria-label="{project['name']} releases"><p class="release-loading">{'Загружаем версии…' if not en else 'Loading releases…'}</p></section>{'<section class="tools-release" data-release="tools" aria-label="device-tools releases"></section>' if key == 'ipa' else ''}</div><p class="section-note">{'Release notes are shown in their original language.' if en else 'Описания выпусков загружаются из GitHub Releases.'}</p><p class="sync-status" id="sync-status" role="status"></p><noscript><a class="text-link" href="{REPO_BASE}{project['repo']}/releases">{'Все выпуски на GitHub' if not en else 'All releases on GitHub'} ↗</a></noscript></section><section class="follow-section"><h2>{'На связи' if not en else 'Stay in touch'}</h2><p>{'Новости разработки — в канале. Обсудить вопрос лично — в Telegram.' if not en else 'Follow development updates in the channel or get in touch on Telegram.'}</p><div class="actions">{social_links(lang)}</div></section></main><footer><span>© 2026 DARKLS · {'Дмитрий Суханов' if not en else 'Dmitry Sukhanov'}</span><a href="{home}">← {'На главную' if not en else 'Home'}</a></footer></div>{dialog(lang)}<script id="release-snapshot" type="application/json">{snapshots}</script><script src="/app{'.en' if en else ''}.js" defer></script></body></html>'''

# Exact strings in the source home template. GitHub-authored descriptions and notes stay original.
HOME_EN = {
    '<html lang="ru">':'<html lang="en">',
    'DARKLS — проекты Дмитрия Суханова':'DARKLS — projects by Dmitry Sukhanov',
    'Личные проекты DARKLS: IPA Desktop для iPhone и Windows, DARKLS VPN Panel для ASUS и другие эксперименты. Исходники, релизы и документация.':'Personal DARKLS projects: IPA Desktop for iPhone and Windows, DARKLS VPN Panel for ASUS, and experiments. Source code, releases and documentation.',
    'DARKLS — от идеи до работающего инструмента':'DARKLS — from an idea to a working tool',
    'IPA Desktop, DARKLS VPN Panel и другие личные проекты. Открытый код, релизы и документация.':'IPA Desktop, DARKLS VPN Panel and other personal projects. Open source, releases and documentation.',
    'Перейти к проектам':'Skip to projects','DARKLS, в начало':'DARKLS, home','Основная навигация':'Main navigation',
    '>Проекты<':'>Projects<','>Об авторе<':'>About<','>Обновления<':'>Updates<','Переключить тему':'Switch theme','>Тема<':'>Theme<',
    'Личные проекты · открытый код':'Personal projects · open source',
    'От идеи — к инструментам,<br>которыми <em>пользуюсь сам.</em>':'From an idea to tools<br>I <em>use myself.</em>',
    'Я Дима, он же DARKLS. Делаю приложения и разбираюсь в технологиях. Здесь собираю свои проекты — от работы с iPhone до домашнего VPN.':"I’m Dima, also known as DARKLS. I build apps and explore technology. Here are my projects, from iPhone tools to home VPN routing.",
    'Смотреть проекты':'Explore projects','Категории проектов':'Project categories','>Все<':'>All<','>Приложения<':'>Apps<','>Сеть<':'>Networking<','>Другие проекты<':'>Other projects<','>Форки<':'>Forks<','Поиск проектов':'Search projects','Найти проект…':'Find a project…',
    'Главные проекты':'Featured projects','Приложения, сервисы и инструменты':'Apps, services and tools','Приложения и инструменты':'Apps and tools',
    'VPN · сервис':'VPN · service','Сайт VPN-проекта DARKLS. Информация о сервисе и подключении — на официальном сайте.':'The DARKLS VPN project website. Visit the official site for service and connection information.','Открыть сайт':'Visit website',
    'Поиск, скачивание и установка приложений на iPhone — в одном приложении для Windows.':'Find, download and install iPhone apps in one Windows application.',
    'Вход в Apple Account прямо в окне программы':'Sign in to your Apple Account inside the app',
    'Очереди загрузки, версии и наборы приложений':'Download queues, versions and app collections',
    'Установка IPA и управление хранилищем':'IPA installation and storage management',
    'Локальная панель для домашнего роутера. Выбирай, какие сайты и устройства будут работать через VPN.':'A local panel for your home router. Choose which sites and devices use your VPN.',
    'Маршруты для сайтов и отдельных устройств':'Routing for sites and individual devices',
    'Переключение серверов и диагностика связи':'Server switching and connectivity diagnostics',
    'Обновления панели и ядра Xray':'Independent panel and Xray core updates',
    'Версии IPA Desktop':'IPA Desktop releases','Версии DARKLS VPN Panel':'DARKLS VPN Panel releases','Версии device-tools':'device-tools releases',
    'Загружаем сведения о версиях…':'Loading release information…','Инструменты iPhone · загрузка версии…':'iPhone tools · loading version…',
    '>Скачать <':'>Download <','О проекте и требованиях':'About the project and requirements',
    'Windows 10 (1809+) или Windows 11, x64. Для скачивания нужен Apple Account. Для установки на iPhone — компоненты Apple Mobile Device Support и доверие к компьютеру. Установка по Wi-Fi экспериментальная.':'Windows 10 (1809+) or Windows 11, x64. Downloads require an Apple Account. iPhone installation requires Apple Mobile Device Support and a trusted pairing. Wi-Fi installation is experimental.',
    'Инструкция и помощь':'Instructions and help',
    'Для уже настроенного VPN на роутере':'For an existing router VPN setup',
    'Панель для ASUS TUF-BE6500 со штатной прошивкой, SSH и уже настроенным Xray. VPN-подписка и сервер в комплект не входят. Панель работает в домашней сети.':'For the ASUS TUF-BE6500 with stock firmware, SSH and an existing Xray setup. A VPN subscription and server are not included. The panel runs on your home network.',
    'Руководство пользователя':'User guide','Другие репозитории':'Other repositories','С GitHub · автоматически':'From GitHub · automatic',
    'Каталог публичных репозиториев обновляется автоматически.':'The public repository catalog updates automatically.',
    'За проектами — Дима.':'The person behind the projects: Dima.',
    'Начинаю с задачи, которая нужна мне самому, и постепенно превращаю решение в отдельный проект. ':'I start with something I need myself and gradually turn the solution into a project. ',
    'Исходники, инструкции и история изменений — на GitHub. Там же можно предложить идею или рассказать об ошибке.':'Source code, instructions and release history are on GitHub. You can also suggest an idea or report a bug there.',
    'Версии загружаются из последнего снимка GitHub Releases.':'Release data comes from the latest GitHub Releases snapshot.',
    'Для фильтров, переключения темы и списка версий включите JavaScript. Ссылки на проекты и скачивание работают без него.':'Enable JavaScript for filters, theme switching and release details. Project and download links also work without it.',
    'Дмитрий Суханов':'Dmitry Sukhanov','Наверх':'Back to top',
    'Подробнее о проекте':'Explore the project','Сообщить об ошибке':'Report a bug','Предложить идею':'Suggest an idea',
    'Выпуски по проектам':'Releases by project','Лента обновлений':'Release feed','Все проекты':'All projects','Оригинальные описания из GitHub Releases.':'Original release notes from GitHub Releases.',
    'На связи':'Stay in touch','Новости разработки — в канале. Обсудить вопрос лично — в Telegram.':'Follow development updates in the channel or get in touch on Telegram.',
    'Telegram · новости':'Telegram · updates','Личный Telegram':'Personal Telegram',
}


def generate_pages(root, out, html, releases, catalog):
    projects = json.loads((root / 'content/project_pages.json').read_text())
    html = re.sub(r'<ol class="release-feed" id="release-feed">.*?</ol>', lambda _: render_feed(releases, 'ru'), html, flags=re.S)
    (out / 'index.html').write_text(html)
    en = html
    for project in projects.values():
        en = en.replace(feedback(project['repo'],'ru'),feedback(project['repo'],'en'))
    for ru, english in HOME_EN.items():
        en = en.replace(ru, english)
    en = en.replace('href="/en/" lang="en" hreflang="en">EN</a>', 'href="/" lang="ru" hreflang="ru">RU</a>')
    en = en.replace('href="/projects/', 'href="/en/projects/').replace('src="app.js"', 'src="/app.en.js"').replace('href="styles.css"','href="/styles.css"').replace('href="favicon.svg"','href="/favicon.svg"')
    en = en.replace('href="https://iamdarkls.github.io/"', 'href="https://iamdarkls.github.io/en/"', 1)
    en = en.replace('content="https://iamdarkls.github.io/"', 'content="https://iamdarkls.github.io/en/"')
    en = re.sub(r'<ol class="release-feed" id="release-feed">.*?</ol>', lambda _: render_feed(releases, 'en'), en, flags=re.S)
    # Translate generated no-JS catalog labels, retaining GitHub descriptions as authored.
    en = en.replace('С GITHUB', 'FROM GITHUB').replace('Язык не указан','Language not specified').replace(' · проект',' · project').replace(' · форк',' · fork').replace(' · архив',' · archived').replace('Описание пока не добавлено на GitHub.','No description has been added on GitHub.').replace('Последний коммит:','Last commit:').replace(' на GitHub"',' on GitHub"')
    (out / 'en').mkdir(exist_ok=True)
    (out / 'en/index.html').write_text(en)
    for lang in ('ru','en'):
        for key, project in projects.items():
            dest = out / ('en' if lang == 'en' else '') / 'projects' / project['slug']
            dest.mkdir(parents=True, exist_ok=True)
            (dest / 'index.html').write_text(project_page(project,key,lang,releases))
    paths = ['/', '/en/'] + [prefix+'/projects/'+p['slug']+'/' for prefix in ('','/en') for p in projects.values()]
    (out / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>{BASE}{path}</loc></url>' for path in paths)+'</urlset>')
