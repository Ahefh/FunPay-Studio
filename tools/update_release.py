import urllib.request
import json

import os
import sys

token = os.environ.get('GITHUB_TOKEN') or (sys.argv[1] if len(sys.argv) > 1 else '')
if not token:
    raise ValueError("GITHUB_TOKEN not provided")
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'FPS'
}

req = urllib.request.Request('https://api.github.com/repos/Ahefh/FunPay-Studio/releases/tags/v1.0.0', headers=headers)
with urllib.request.urlopen(req) as resp:
    rel = json.loads(resp.read().decode('utf-8'))
    rel_id = rel['id']
    upload_url = rel['upload_url'].split('{')[0]
    for asset in rel.get('assets', []):
        print(f"Deleting old asset {asset['name']} (ID: {asset['id']})...")
        del_req = urllib.request.Request(asset['url'], headers=headers, method='DELETE')
        urllib.request.urlopen(del_req)

zip_path = r'C:\Bots\FunPayStudio\FunPayStudio-v1.0.0.zip'
print('Uploading unified FunPayStudio-v1.0.0.zip...')
with open(zip_path, 'rb') as f:
    zip_bytes = f.read()

up_req = urllib.request.Request(
    f'{upload_url}?name=FunPayStudio-v1.0.0.zip',
    data=zip_bytes,
    headers={
        'Authorization': f'token {token}',
        'Content-Type': 'application/zip',
        'User-Agent': 'FPS'
    }
)
with urllib.request.urlopen(up_req) as up_resp:
    print('Unified ZIP uploaded to GitHub Release successfully!')

patch_payload = {
    'name': 'FunPay Studio v1.0.0 (FPS) — Официальный релиз',
    'body': '📦 **Официальная единая сборка FunPay Studio v1.0.0**\n\nВключает автономное ядро, защиту Smart Anti-Ban, облачные конфиги (.fps), библиотеку FunPayAPI и Telegram-панель управления.\n\n🧩 **Плагины и расширения:**\nВсе официальные плагины и дополнения публикуются отдельно в Telegram-канале:\n👉 https://t.me/fps_plugins1\n\n📢 **Канал проекта:** https://t.me/funpaystudio'
}
patch_req = urllib.request.Request(
    f'https://api.github.com/repos/Ahefh/FunPay-Studio/releases/{rel_id}',
    data=json.dumps(patch_payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)
with urllib.request.urlopen(patch_req) as p_resp:
    print('Release description updated!')
