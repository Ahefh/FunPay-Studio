import os
import zipfile
import shutil

dist_dir = r'C:\Bots\FunPayStudio\dist\FunPayStudio'
root_dir = r'C:\Bots\FunPayStudio'
out_zip = r'C:\Bots\FunPayStudio\FunPayStudio-v1.0.0.zip'

os.makedirs(os.path.join(dist_dir, 'plugins'), exist_ok=True)
os.makedirs(os.path.join(dist_dir, 'configs'), exist_ok=True)
os.makedirs(os.path.join(dist_dir, 'logs'), exist_ok=True)
os.makedirs(os.path.join(dist_dir, 'storage', 'presets'), exist_ok=True)

shutil.copytree(os.path.join(root_dir, 'storage', 'presets'), os.path.join(dist_dir, 'storage', 'presets'), dirs_exist_ok=True)

for fname in ['Start.bat', 'Stop.bat', 'Install.bat', 'README.md', 'LICENSE']:
    src_f = os.path.join(root_dir, fname)
    if os.path.exists(src_f):
        shutil.copy(src_f, os.path.join(dist_dir, fname))

start_exe_bat = '@echo off\ntitle FunPay Studio (FPS)\ncls\ncd /d "%~dp0"\nFunPayStudio.exe\npause\n'
with open(os.path.join(dist_dir, 'Start_EXE.bat'), 'w', encoding='utf-8') as f:
    f.write(start_exe_bat)

print('Archiving standalone distribution with FunPayStudio.exe...')
with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, dirs, files in os.walk(dist_dir):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, dist_dir)
            z.write(full_path, os.path.join('FunPayStudio', rel_path))

print('Complete Standalone Release ZIP with EXE created:', out_zip)
print('Archive size:', os.path.getsize(out_zip), 'bytes')
