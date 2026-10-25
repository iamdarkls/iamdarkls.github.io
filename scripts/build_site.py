"""Package only public site files; refresh the inline offline snapshot."""
from pathlib import Path
import json
import re
import shutil

root = Path(__file__).resolve().parents[1]
out = root / '_site'
if out.exists():
    shutil.rmtree(out)
(out / 'data').mkdir(parents=True)
for name in ('index.html', 'styles.css', 'app.js', 'favicon.svg', 'robots.txt', 'sitemap.xml', '.nojekyll'):
    shutil.copy2(root / name, out / name)
shutil.copy2(root / 'data/releases.json', out / 'data/releases.json')
data = json.loads((root / 'data/releases.json').read_text())
html = (root / 'index.html').read_text()
encoded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
html = re.sub(r'(<script id="release-snapshot" type="application/json">).*?(</script>)', lambda match: match[1] + encoded + match[2], html, flags=re.S)
(out / 'index.html').write_text(html)
print('Packaged static website in _site/')
