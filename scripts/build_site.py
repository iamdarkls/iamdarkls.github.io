"""Package only public site files; refresh the inline offline snapshot."""
from pathlib import Path
import json
import re
import shutil
import hashlib
from repository_catalog import render_catalog
from site_pages import generate_pages
from site_translations import translate_app

root = Path(__file__).resolve().parents[1]
out = root / '_site'
if out.exists():
    shutil.rmtree(out)
(out / 'data').mkdir(parents=True)
for name in ('index.html', 'styles.css', 'app.js', 'favicon.svg', 'robots.txt', 'sitemap.xml', '.nojekyll'):
    shutil.copy2(root / name, out / name)
for filename in ('releases.json', 'repositories.json'):
    shutil.copy2(root / 'data' / filename, out / 'data' / filename)
data = json.loads((root / 'data/releases.json').read_text())
html = (root / 'index.html').read_text()
encoded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
html = re.sub(r'(<script id="release-snapshot" type="application/json">).*?(</script>)', lambda match: match[1] + encoded + match[2], html, flags=re.S)
catalog = json.loads((root / 'data/repositories.json').read_text())
encoded_catalog = json.dumps(catalog, ensure_ascii=False).replace('<', '\\u003c')
html = re.sub(r'(<script id="repository-snapshot" type="application/json">).*?(</script>)', lambda match: match[1] + encoded_catalog + match[2], html, flags=re.S)
html = re.sub(r'(<div id="repository-catalog">).*?(</div>\s*<p class="catalog-status")', lambda match: match[1] + render_catalog(catalog['repositories']) + match[2], html, flags=re.S)
generate_pages(root, out, html, data, catalog)
(out / 'app.en.js').write_text(translate_app((root / 'app.js').read_text()))
shutil.copytree(root / 'assets', out / 'assets', dirs_exist_ok=True)
# Use content-versioned URLs so fresh markup never loads an older cached stylesheet/script.
versions = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()[:12] for name in ('styles.css', 'app.js', 'app.en.js')}
for page in out.rglob('index.html'):
    content = page.read_text()
    for name, version in versions.items():
        content = re.sub(r'((?:href|src)=")/?' + re.escape(name) + r'(?:\?v=[a-f0-9]+)?(")', lambda match: match[1] + '/' + name + '?v=' + version + match[2], content)
    page.write_text(content)
print('Packaged static website in _site/')
