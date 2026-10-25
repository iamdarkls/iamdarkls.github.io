'use strict';
(() => {
  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
  const themeButton = $('#theme-toggle');
  const themeMedia = matchMedia('(prefers-color-scheme: light)');
  function storageGet(key) { try { return localStorage.getItem(key); } catch { return null; } }
  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    themeButton.setAttribute('aria-label', theme === 'dark' ? 'Включить светлую тему' : 'Включить тёмную тему');
    themeButton.title = themeButton.getAttribute('aria-label');
    $('span', themeButton).textContent = theme === 'dark' ? 'Светлая' : 'Тёмная';
  }
  setTheme(storageGet('darkls-theme') || (themeMedia.matches ? 'light' : 'dark'));
  themeButton.hidden = false;
  themeButton.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    try { localStorage.setItem('darkls-theme', next); } catch { /* Private browsing remains usable. */ }
  });
  themeMedia.addEventListener('change', event => {
    if (!storageGet('darkls-theme')) setTheme(event.matches ? 'light' : 'dark');
  });

  let selectedCategory = 'all';
  function filterProjects() {
    if (!$('#project-search')) return;
    const search = $('#project-search').value.trim().toLocaleLowerCase();
    let visible = 0;
    for (const card of $$('[data-category]')) {
      const matches = (selectedCategory === 'all' || card.dataset.category === selectedCategory) && card.textContent.toLocaleLowerCase('ru').includes(search);
      card.hidden = !matches;
      if (matches) visible++;
    }
    for (const section of [$('#projects'), $('#other-projects')]) {
      section.hidden = !$$('[data-category]', section).some(card => !card.hidden);
    }
    const status = $('#filter-status');
    status.hidden = selectedCategory === 'all' && !search;
    status.textContent = visible ? `Найдено проектов: ${visible}` : 'Ничего не найдено. Попробуйте другое название или категорию.';
  }
  if ($('#explorer')) $('#explorer').hidden = false;
  for (const button of $$('[data-filter]')) button.addEventListener('click', () => {
    selectedCategory = button.dataset.filter;
    for (const other of $$('[data-filter]')) other.setAttribute('aria-pressed', String(other === button));
    filterProjects();
  });
  $('#project-search')?.addEventListener('input', filterProjects);

  const repositories = { ipa: 'IPA-Desktop', tools: 'IPA-Desktop', vpn: 'DARKLS-VPN-Panel' };
  const dateFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'Europe/Moscow' });
  const timeFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit', timeZone: 'Europe/Moscow' });
  function validDate(value) { return typeof value === 'string' && Number.isFinite(Date.parse(value)); }
  function date(value) { return validDate(value) ? dateFormat.format(new Date(value)) : 'Дата не указана'; }
  function safeUrl(value, key, download = false) {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && url.hostname === 'github.com' && !url.username && !url.password && url.pathname.startsWith(`/iamdarkls/${repositories[key]}/releases/${download ? 'download/' : 'tag/'}`) ? url.href : null;
    } catch { return null; }
  }
  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function link(text, url, className = '') { const node = el('a', className, text); node.href = url; return node; }
  function notesText(text) {
    return String(text || '').replace(/\r/g, '').replace(/^#{1,6}\s+/gm, '').replace(/!\[[^\]]*\]\([^)]*\)/g, '').replace(/\[([^\]]+)\]\(([^)]+)\)/g, '$1 ($2)').replace(/\*\*([^*]+)\*\*/g, '$1').replace(/`([^`]+)`/g, '$1').trim();
  }
  function summary(text) {
    const lines = notesText(text).split('\n').map(line => line.trim()).filter(line => line && !/^[-=]{3,}$/.test(line));
    return (lines.join(' ').slice(0, 240) + (lines.join(' ').length > 240 ? '…' : '')) || 'Подробности этого выпуска доступны на GitHub.';
  }
  function releaseDetails(release, key) {
    const details = el('details', 'release-notes');
    details.append(el('summary', '', 'Что изменилось'));
    details.append(el('pre', 'notes', notesText(release.notes) || 'Описание выпуска не заполнено.'));
    const url = safeUrl(release.url, key);
    if (url) details.append(link('Полный выпуск на GitHub ↗', url, 'text-link'));
    return details;
  }
  function renderChannel(key, data) {
    const target = $(`[data-release="${key}"]`);
    if (!target || !data || !data.latest || !safeUrl(data.latest.url, key)) return;
    // Keep visitor-expanded sections open after periodic data refresh.
    const open = $$('details', target).map(details => details.open);
    const latest = data.latest;
    const fragment = document.createDocumentFragment();
    const top = el('div', 'release-top');
    const version = key === 'tools' ? latest.tag.replace(/^device-tools-/, '') : latest.tag;
    top.append(link(version, safeUrl(latest.url, key), 'version'), el('span', 'release-label', key === 'tools' ? 'device-tools · инструменты iPhone' : 'Стабильный выпуск'));
    fragment.append(top, el('p', 'release-date', `Выпущено ${date(latest.published_at)}`));
    if (key !== 'tools') fragment.append(el('p', 'release-summary', summary(latest.notes)));
    fragment.append(releaseDetails(latest, key));
    if (data.preview && safeUrl(data.preview.url, key)) {
      const preview = el('div', 'prerelease');
      preview.append(el('span', '', 'Предварительный выпуск: '), link(data.preview.tag, safeUrl(data.preview.url, key)));
      preview.append(el('div', '', `${date(data.preview.published_at)} · для тестирования`));
      fragment.append(preview);
    }
    const history = el('details', 'history');
    history.append(el('summary', '', 'История выпусков'));
    const list = el('ol', 'history-list');
    for (const release of (Array.isArray(data.history) ? data.history : []).slice(0, 6)) {
      const url = safeUrl(release.url, key);
      if (!url) continue;
      const item = el('li');
      const row = el('div', 'history-line');
      row.append(link(release.tag + (release.prerelease ? ' · предварительный' : ''), url));
      const time = el('time', '', date(release.published_at));
      if (validDate(release.published_at)) time.dateTime = release.published_at;
      row.append(time);
      item.append(row, el('p', 'release-summary', summary(release.notes)));
      list.append(item);
    }
    history.append(list);
    fragment.append(history);
    const downloadable = (Array.isArray(latest.assets) ? latest.assets : []).find(asset => safeUrl(asset.url, key, true));
    if (key === 'tools') fragment.append(link(downloadable ? 'Скачать device-tools ↓' : 'Открыть выпуск device-tools ↗', downloadable ? safeUrl(downloadable.url, key, true) : safeUrl(latest.url, key), 'text-link'));
    else {
      const button = $(`[data-download="${key}"]`);
      button.href = downloadable ? safeUrl(downloadable.url, key, true) : safeUrl(latest.url, key);
      button.title = downloadable ? downloadable.name : 'Открыть страницу выпуска';
      button.setAttribute('aria-label', `Скачать ${key === 'ipa' ? 'IPA Desktop' : 'DARKLS VPN Panel'} ${latest.tag}`);
    }
    target.replaceChildren(fragment);
    $$('details', target).forEach((details, i) => { details.open = Boolean(open[i]); });
  }
  let feedFilter = 'all';
  let feedSignature = null;
  function renderFeed(data) {
    const target = $('#release-feed');
    if (!target) return;
    const signature = JSON.stringify(data.projects) + feedFilter;
    if (signature === feedSignature) return;
    const items = new Map();
    const names = {ipa:'IPA Desktop', vpn:'DARKLS VPN Panel', tools:'device-tools'};
    for (const key of Object.keys(names)) {
      const channel = data.projects[key] || {};
      for (const release of [...(channel.history || []), channel.latest, channel.preview]) {
        if (!release || !validDate(release.published_at) || !safeUrl(release.url,key)) continue;
        items.set(key + ':' + release.tag, {...release, channel:key});
      }
    }
    const all = [...items.values()].sort((a,b) => Date.parse(b.published_at) - Date.parse(a.published_at)).slice(0,12);
    const fragment = document.createDocumentFragment();
    for (const release of all.filter(item => feedFilter === 'all' || item.channel === feedFilter)) {
      const item = el('li', 'feed-item');
      const meta = el('div', 'feed-meta');
      const time = el('time','',date(release.published_at));
      time.dateTime = release.published_at;
      meta.append(el('span','',names[release.channel]), time);
      const title = el('h3');
      title.append(link(release.tag + ' ↗',safeUrl(release.url,release.channel)),el('span','feed-badge',release.prerelease ? 'Предварительный' : 'Стабильный'));
      item.append(meta,title,el('p','',summary(release.notes)));
      fragment.append(item);
    }
    if (!fragment.childNodes.length) fragment.append(el('li','feed-item','Для выбранного проекта пока нет выпусков в ленте.'));
    target.replaceChildren(fragment);
    feedSignature = signature;
  }
  if ($('.feed-filters')) $('.feed-filters').hidden = false;
  for (const button of $$('[data-feed-filter]')) button.addEventListener('click', () => {
    feedFilter = button.dataset.feedFilter;
    for (const other of $$('[data-feed-filter]')) other.setAttribute('aria-pressed',String(other === button));
    if (snapshot) renderFeed(snapshot);
  });
  let snapshot = null;
  let refreshing = false;
  function showSnapshot(data, failed = false) {
    if (!data || data.schema !== 1 || !data.projects) return;
    snapshot = data;
    renderFeed(data);
    for (const key of Object.keys(repositories)) renderChannel(key, data.projects[key]);
    const checks = Object.keys(repositories).map(key => data.projects[key]?.checked_at).filter(validDate);
    const oldest = checks.length ? new Date(Math.min(...checks.map(value => Date.parse(value)))) : null;
    const stale = failed || !oldest || Date.now() - oldest.getTime() > 3 * 3600000 || (data.errors || []).length > 0;
    const status = $('#sync-status');
    status.classList.toggle('stale', stale);
    status.textContent = `${oldest ? `Данные GitHub Releases проверены ${timeFormat.format(oldest)} МСК.` : 'Время проверки неизвестно.'} ${stale ? 'Показываем последние сохранённые данные; обновление временно задерживается.' : 'Обновление примерно раз в час.'}`;
    filterProjects();
  }
  try { showSnapshot(JSON.parse($('#release-snapshot').textContent)); } catch {
    $('#sync-status').textContent = 'Не удалось загрузить версии. Актуальные выпуски доступны по ссылкам на GitHub.';
  }
  let catalogSnapshot = null;
  let catalogRefreshing = false;
  let catalogSignature = null;
  function validCatalog(data) {
    return data?.schema === 1 && data.owner === 'iamdarkls' && validDate(data.checked_at) && Array.isArray(data.repositories) && data.repositories.every(repo => {
      if (!repo || typeof repo.name !== 'string' || !/^[A-Za-z0-9_.-]+$/.test(repo.name)) return false;
      try {
        const url = new URL(repo.url);
        return url.origin === 'https://github.com' && !url.username && !url.password && !url.search && !url.hash && url.pathname === `/iamdarkls/${repo.name}`;
      } catch { return false; }
    });
  }
  function renderCatalog(data, failed = false) {
    if (!$('#repository-catalog') || !validCatalog(data)) return;
    catalogSnapshot = data;
    const signature = JSON.stringify(data.repositories);
    if (signature !== catalogSignature) {
      const fragment = document.createDocumentFragment();
      for (const repo of data.repositories) {
        const card = el('article', 'repo-row');
        card.dataset.category = repo.fork ? 'forks' : 'other';
        const icon = el('span', 'repo-icon', repo.fork ? '⑂' : '↗');
        icon.setAttribute('aria-hidden', 'true');
        const heading = el('div');
        const badges = [repo.language || 'Язык не указан', repo.fork ? 'форк' : 'проект'];
        if (repo.archived) badges.push('архив');
        heading.append(el('h3', '', repo.name), el('span', 'repo-kind', badges.join(' · ')));
        const description = el('div', 'repo-description');
        description.append(el('p', '', repo.description || 'Описание пока не добавлено на GitHub.'));
        if (validDate(repo.pushed_at)) {
          const updated = el('span', 'repo-updated', 'Последний коммит: ');
          const time = el('time', '', date(repo.pushed_at));
          time.dateTime = repo.pushed_at;
          updated.append(time);
          description.append(updated);
        }
        const github = link('GitHub ↗', repo.url, 'text-link');
        github.setAttribute('aria-label', `${repo.name} на GitHub`);
        card.append(icon, heading, description, github);
        fragment.append(card);
      }
      if (!data.repositories.length) fragment.append(el('p', 'catalog-empty', 'Других публичных репозиториев пока нет.'));
      $('#repository-catalog').replaceChildren(fragment);
      catalogSignature = signature;
    }
    const stale = failed || data.error || Date.now() - Date.parse(data.checked_at) > 3 * 3600000;
    const status = $('#catalog-status');
    status.classList.toggle('stale', Boolean(stale));
    status.textContent = `Каталог GitHub проверен ${timeFormat.format(new Date(data.checked_at))} МСК. ${stale ? 'Показываем последний сохранённый список; обновление задерживается.' : 'Новые публичные репозитории появляются автоматически, примерно раз в час.'}`;
    filterProjects();
  }
  try { renderCatalog(JSON.parse($('#repository-snapshot').textContent)); } catch {
    if ($('#catalog-status')) $('#catalog-status').textContent = 'Показываем сохранённый каталог. Список репозиториев доступен на GitHub.';
  }
  async function refreshCatalog() {
    if (!$('#repository-catalog') || catalogRefreshing) return;
    catalogRefreshing = true;
    try {
      const response = await fetch('/data/repositories.json', { cache: 'no-cache', signal: AbortSignal.timeout(12000) });
      if (!response.ok) throw new Error('Catalog unavailable');
      const data = await response.json();
      if (!validCatalog(data)) throw new Error('Invalid catalog');
      renderCatalog(data);
    } catch { if (catalogSnapshot) renderCatalog(catalogSnapshot, true); }
    finally { catalogRefreshing = false; }
  }
  async function refresh() {
    if (refreshing) return;
    refreshing = true;
    try {
      const response = await fetch('/data/releases.json', { cache: 'no-cache', signal: AbortSignal.timeout(12000) });
      if (!response.ok) throw new Error('Snapshot unavailable');
      const data = await response.json();
      if (data.schema !== 1 || !['ipa', 'vpn', 'tools'].every(key => data.projects?.[key]?.latest && validDate(data.projects[key].checked_at) && safeUrl(data.projects[key].latest.url, key))) throw new Error('Invalid snapshot');
      showSnapshot(data);
    } catch { if (snapshot) showSnapshot(snapshot, true); }
    finally { refreshing = false; }
  }
  const imageDialog = $('#image-dialog');
  if (imageDialog) {
    for (const anchor of $$('[data-lightbox]')) anchor.addEventListener('click', event => {
      event.preventDefault();
      const image = $('img', anchor);
      $('#image-full').src = anchor.href;
      $('#image-full').alt = image.alt;
      $('#image-caption').textContent = image.alt;
      imageDialog.showModal();
    });
    $('#image-close').addEventListener('click', () => imageDialog.close());
    imageDialog.addEventListener('click', event => {
      if (event.target === imageDialog) {
        const box = imageDialog.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) imageDialog.close();
      }
    });
  }
  function refreshAll() { refresh(); refreshCatalog(); }
  refreshAll();
  setInterval(() => { if (!document.hidden) refreshAll(); }, 5 * 60 * 1000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshAll(); });
})();
