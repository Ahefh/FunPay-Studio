import os
import re

src_dir = r'C:\Users\bobka\Downloads\Telegram Desktop'
files = [f for f in os.listdir(src_dir) if f.endswith('.py')]

groups = {}
for f in files:
    m = re.match(r'^(.*?)(?:\s*\(\d+\))?\.py$', f)
    if m:
        base = m.group(1).strip()
        p = os.path.join(src_dir, f)
        size = os.path.getsize(p)
        mtime = os.path.getmtime(p)
        if base not in groups:
            groups[base] = []
        groups[base].append({'file': f, 'path': p, 'size': size, 'mtime': mtime})

print(f'Total unique plugins found: {len(groups)}')
for base, list_files in sorted(groups.items()):
    best = max(list_files, key=lambda x: (x['size'], x['mtime']))
    bfile = best['file']
    bsize = best['size']
    print(f'Plugin: {base:<22} | Variants: {len(list_files):<2} | Best: {bfile} ({bsize} bytes)')
