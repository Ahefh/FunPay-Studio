import os
import shutil
import re

src_dir = r"C:\Users\bobka\Downloads\Telegram Desktop"
dst_dir = r"C:\Bots\FunPayStudio\free_plugins"
os.makedirs(dst_dir, exist_ok=True)

# Selected best files mapping
best_plugins = {
    "adv_profile_stat.py": "adv_profile_stat.py",
    "auto_withdraw.py": "auto_withdraw (2).py",
    "chat_sync_plugin.py": "chat_sync_plugin.py",
    "cookie_changer.py": "cookie_changer.py",
    "copy_lots_plugin.py": "copy_lots_plugin.py",
    "del_old_users.py": "del_old_users.py",
    "graphs_plugin.py": "graphs_plugin.py",
    "list_old_orders.py": "list_old_orders.py",
    "money_generator_plugin.py": "money_generator_plugin.py",
    "old_keyboard_plugin.py": "old_keyboard_plugin.py",
    "review_chat_reply.py": "review_chat_reply (7).py",
    "sras_info_plugin.py": "sras_info_plugin.py",
    "status_plugin.py": "status_plugin (2).py",
    "tg_proxy_plugin.py": "tg_proxy_plugin.py",
    "wallets_plugin.py": "wallets_plugin (2).py",
}

replacements = [
    ("https://t.me/fpc_plugins", "https://t.me/fps_plugins1"),
    ("@fpc_plugins", "@fps_plugins1"),
    ("t.me/fpc_plugins", "t.me/fps_plugins1"),
    ("https://t.me/funpay_cardinal", "https://t.me/funpaystudio"),
    ("@funpay_cardinal", "@funpaystudio"),
    ("FunPay Studio", "FunPay Studio"),
    ("FunPayStudio", "FunPayStudio"),
    ("FPC", "FPS"),
    ("2023", "2026"),
    ("2024", "2026"),
    ("2025", "2026"),
]

our_header = """# ==============================================================================
# FunPay Studio (FPS) — Официальный плагин
# Создатель: yuepi-FPS
# Официальный канал: https://t.me/funpaystudio
# Каталог плагинов:   https://t.me/fps_plugins1
# Наш FunPay магазин: https://funpay.com/users/11535828/
# Версия под 2026 год
# ==============================================================================
"""

processed = []
for clean_name, src_file in best_plugins.items():
    s_path = os.path.join(src_dir, src_file)
    d_path = os.path.join(dst_dir, clean_name)
    
    with open(s_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Rebrand credits and authors
    content = re.sub(r'CREDITS\s*=\s*["\'].*?["\']', 'CREDITS = "yuepi-FPS"', content)
    
    # Apply standard replacements
    for old_val, new_val in replacements:
        content = content.replace(old_val, new_val)

    # Prepend header if not already there
    final_content = our_header + "\n" + content

    with open(d_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    processed.append(clean_name)
    print(f"Updated & Saved: {clean_name}")

print(f"\nSuccessfully prepared {len(processed)} free plugins in {dst_dir}!")
