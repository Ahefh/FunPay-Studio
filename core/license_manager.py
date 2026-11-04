"""
FunPay Studio — License Manager
Система валидации и защиты коммерческих плагинов экосистемы FunPay Studio.
Официальный магазин плагинов: https://t.me/fps_plugins1
Официальное сообщество: https://t.me/funpaystudio
"""

import hmac
import hashlib
import logging

logger = logging.getLogger("FPS.license")

SECRET_SALT = "FUNPAY_STUDIO_OFFICIAL_SECRET_KEY_2026_PROTECTION"

class LicenseManager:
    @staticmethod
    def generate_license(funpay_id: int | str, plugin_id: str) -> str:
        """
        Генерирует уникальный лицензионный ключ для покупателя плагина в Telegram-боте @fps_plugins1.
        Ключ привязан строго к ID аккаунта FunPay покупателя.
        """
        raw = f"{funpay_id}:{plugin_id}:{SECRET_SALT}"
        token = hmac.new(SECRET_SALT.encode(), raw.encode(), hashlib.sha256).hexdigest()[:16].upper()
        return f"FPS-{plugin_id.upper()}-{funpay_id}-{token}"

    @staticmethod
    def verify_license(license_key: str, current_funpay_id: int | str, plugin_id: str) -> bool:
        """
        Проверяет, что плагин запущен именно тем продавцом, который его официально купил.
        Защищает от сливов на форумы.
        """
        if not license_key or not isinstance(license_key, str):
            return False
        
        parts = license_key.strip().split("-")
        if len(parts) != 4 or parts[0] != "FPS":
            return False
        
        key_plugin, key_fpid, key_token = parts[1], parts[2], parts[3]
        if key_plugin.lower() != plugin_id.lower() or str(key_fpid) != str(current_funpay_id):
            return False
        
        expected_key = LicenseManager.generate_license(current_funpay_id, plugin_id)
        is_valid = (license_key.strip() == expected_key)
        if not is_valid:
            logger.warning(
                f"[LICENSE ALERT] Обнаружен нелицензионный запуск плагина '{plugin_id}'! "
                f"Официальный магазин плагинов: https://t.me/fps_plugins1"
            )
        return is_valid
