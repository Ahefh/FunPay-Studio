import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.cloud_configs import CloudConfigEngine

presets_dir = r"C:\Bots\FunPayStudio\storage\presets"
os.makedirs(presets_dir, exist_ok=True)

# 1. Генерация Турбо-Продажи
f1 = CloudConfigEngine.export_config(
    output_path=os.path.join(presets_dir, "turbo_sales.fps"),
    name="⚡️ Турбо-Продажи 24/7",
    author="yuepi-FPS"
)

# 2. Генерация Скрытный Режим (Anti-Ban)
f2 = CloudConfigEngine.export_config(
    output_path=os.path.join(presets_dir, "stealth_anti_ban.fps"),
    name="🛡 Скрытный Режим (Anti-Ban)",
    author="yuepi-FPS"
)

# 3. Генерация Игры и Макросы
f3 = CloudConfigEngine.export_config(
    output_path=os.path.join(presets_dir, "game_keys_macros.fps"),
    name="🎮 Игры, Ключи и Макросы",
    author="yuepi-FPS"
)

print("All 3 official .fps presets generated successfully:")
for f in [f1, f2, f3]:
    print(" -", f, f"({os.path.getsize(f)} bytes)")
