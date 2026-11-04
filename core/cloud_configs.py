"""
FunPay Studio — Cloud Configs Engine (.fps)
Система импорта, экспорта и облачной синхронизации конфигураций софта.
Создатель: yuepi-FPS
Канал проекта: https://t.me/funpaystudio
Каталог плагинов: https://t.me/fps_plugins1
Наш FunPay магазин: https://funpay.com/users/11535828/
"""

import os
import json
import base64
import time
import logging

logger = logging.getLogger("FPS.cloud_configs")

FPS_MAGIC_HEADER = "FPS_CONFIG_V1"

class CloudConfigEngine:
    """
    Позволяет сохранять и загружать полные слепки стандартных настроек FunPay Studio
    в универсальном формате *.fps для мгновенной автонастройки.
    """
    
    @staticmethod
    def export_config(output_path: str = "storage/presets/backup.fps", name: str = "Пользовательский пресет", author: str = "yuepi-FPS") -> str:
        """
        Сохраняет стандартные конфиги (_main.cfg, auto_delivery.cfg, auto_response.cfg) в один файл .fps
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        cfg_files = {
            "main": "configs/_main.cfg",
            "auto_delivery": "configs/auto_delivery.cfg",
            "auto_response": "configs/auto_response.cfg"
        }
        
        bundle = {
            "magic": FPS_MAGIC_HEADER,
            "name": name,
            "author": author,
            "created_at": int(time.time()),
            "fps_version": "1.0.0",
            "channel": "https://t.me/funpaystudio",
            "configs": {}
        }
        
        for key, path in cfg_files.items():
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    bundle["configs"][key] = f.read()
            else:
                bundle["configs"][key] = ""
                
        raw_json = json.dumps(bundle, ensure_ascii=False)
        encoded_data = base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# FUNPAY STUDIO CONFIG PRESET (.fps)\n# Official: https://t.me/funpaystudio\n{encoded_data}")
            
        logger.info(f"[Cloud Config] Успешно экспортирован конфиг в {output_path}")
        return output_path

    @staticmethod
    def import_config(fps_file_path: str) -> dict:
        """
        Применяет файл конфигурации *.fps к текущей установке FunPay Studio
        """
        if not os.path.exists(fps_file_path):
            return {"success": False, "error": "Файл конфига .fps не найден"}
            
        try:
            with open(fps_file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [line.strip() for line in f if not line.startswith("#") and line.strip()]
            
            payload = "".join(lines)
            decoded_json = base64.b64decode(payload.encode("utf-8")).decode("utf-8")
            bundle = json.loads(decoded_json)
            
            if bundle.get("magic") != FPS_MAGIC_HEADER:
                return {"success": False, "error": "Неверный формат файла .fps"}
                
            configs = bundle.get("configs", {})
            
            # Применяем конфигурации
            if "auto_delivery" in configs and configs["auto_delivery"]:
                with open("configs/auto_delivery.cfg", "w", encoding="utf-8") as f:
                    f.write(configs["auto_delivery"])
                    
            if "auto_response" in configs and configs["auto_response"]:
                with open("configs/auto_response.cfg", "w", encoding="utf-8") as f:
                    f.write(configs["auto_response"])
                    
            # Для _main.cfg сохраняем golden_key текущего пользователя, чтобы не сбивать авторизацию!
            if "main" in configs and configs["main"]:
                current_golden_key = ""
                if os.path.exists("configs/_main.cfg"):
                    try:
                        import configparser
                        cp = configparser.ConfigParser()
                        cp.read("configs/_main.cfg", encoding="utf-8")
                        current_golden_key = cp.get("FunPay", "golden_key", fallback="")
                    except:
                        pass
                
                new_main = configs["main"]
                if current_golden_key:
                    # Подставляем родной токен пользователя
                    import re
                    new_main = re.sub(r'golden_key\s*=.*', f'golden_key = {current_golden_key}', new_main)
                    
                with open("configs/_main.cfg", "w", encoding="utf-8") as f:
                    f.write(new_main)
                    
            name = bundle.get("name", "Без названия")
            author = bundle.get("author", "yuepi-FPS")
            logger.info(f"[Cloud Config] Успешно применен пресет '{name}' от {author}!")
            return {"success": True, "name": name, "author": author}
        except Exception as e:
            logger.error(f"[Cloud Config] Ошибка импорта .fps: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_official_cloud_presets() -> list[dict]:
        """
        Список официальных облачных пресетов от yuepi-FPS
        """
        return [
            {
                "id": "turbo_sales",
                "name": "⚡️ Турбо-Продажи 24/7",
                "desc": "Быстрые автоответы, моментальная автовыдача и агрессивный сбор отзывов 5★.",
                "filename": "turbo_sales.fps"
            },
            {
                "id": "stealth_anti_ban",
                "name": "🛡 Скрытный Режим (Anti-Ban)",
                "desc": "Мягкие человеческие задержки, плавающее автоподнятие лотов и защита от детекта.",
                "filename": "stealth_anti_ban.fps"
            },
            {
                "id": "game_keys_macros",
                "name": "🎮 Игры, Ключи и Макросы",
                "desc": "Идеально настроенные шаблоны автодоставки ключей, аккаунтов и скриптов.",
                "filename": "game_keys_macros.fps"
            }
        ]
