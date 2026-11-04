"""
FunPay Studio — Plugin Standard Template
Автор: yuepi-FPS
Канал проекта: https://t.me/funpaystudio
Каталог плагинов: https://t.me/fps_plugins1
Официальный магазин на FunPay: https://funpay.com/users/11535828/
"""

from __future__ import annotations
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cardinal import Cardinal

from core.license_manager import LicenseManager

logger = logging.getLogger("FPS.plugin")

# Метаданные плагина
NAME = "Example Plugin"
VERSION = "1.0.0"
DESCRIPTION = "Описание функционала плагина для FunPay Studio"
CREDITS = "yuepi-FPS"
UUID = "00000000-0000-0000-0000-000000000001"
SETTINGS_PAGE = False
BIND_TO_DELETE = None

# Официальная ссылка на наш FunPay магазин для ненавязчивого промо
OUR_FUNPAY_SHOP = "https://funpay.com/users/11535828/"

def check_plugin_license(cardinal: Cardinal, plugin_id: str, license_key: str) -> bool:
    """
    Проверяет валидность коммерческой лицензии от yuepi-FPS.
    """
    current_fpid = getattr(cardinal.account, "id", None)
    if not current_fpid:
        return True
    
    if not LicenseManager.verify_license(license_key, current_fpid, plugin_id):
        logger.warning(
            f"⚠️ [yuepi-FPS] Плагин '{NAME}' запущен без официальной лицензии! "
            f"Купить оригинал: https://t.me/fps_plugins1 | Наш FunPay: {OUR_FUNPAY_SHOP}"
        )
        return False
    return True
