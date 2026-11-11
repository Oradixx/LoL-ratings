"""Assemble app/ (gabarit, style, script, données) en une seule page : docs/index.html."""
import os
H = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: open(os.path.join(H, 'app', f), encoding='utf-8').read()
html = rd('index.template.html').replace('/*CSS*/', rd('style.css')).replace('/*JS*/', rd('app.js')).replace('/*DATA*/', rd('data.json').replace('</', '<\\/'))
os.makedirs(os.path.join(H, 'docs'), exist_ok=True)
open(os.path.join(H, 'docs', 'index.html'), 'w', encoding='utf-8').write(html)
open(os.path.join(H, 'docs', '.nojekyll'), 'w').close()
print('docs/index.html', len(html) // 1000, 'Ko')
