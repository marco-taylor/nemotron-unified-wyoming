import html,urllib.request
from html.parser import HTMLParser
from pathlib import Path
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.tags=[]
    def handle_starttag(self,t,a):
        d=dict(a);u=d.get('href','')
        if t=='a' and '2.7.1%2Bcpu' in u and 'cp311-cp311-manylinux_2_28_x86_64.whl' in u:
            self.tags.append('<a '+' '.join(k+'="'+html.escape(v or '',quote=True)+'"' for k,v in a)+'>wheel</a>')
lines=[]
for pkg in ['torch','torchaudio']:
    with urllib.request.urlopen(f'https://download.pytorch.org/whl/cpu/{pkg}/',timeout=30) as r:
        p=Parser();p.feed(r.read().decode());assert len(p.tags)==1;lines+=p.tags
Path('export/cpu-wheels.html').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
