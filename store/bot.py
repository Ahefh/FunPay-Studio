"""
FunPay Studio — Official Plugin Marketplace Bot
Telegram-бот магазина плагинов для экосистемы FunPay Studio.
Канал: https://t.me/funpaystudio
Магазин: https://t.me/fps_plugins1
"""

import logging
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.license_manager import LicenseManager

# Автор и создатель экосистемы плагинов
CREATOR = "yuepi-FPS"
OFFICIAL_SHOP_URL = "https://funpay.com/users/11535828/"

# Список коммерческих плагинов в каталоге
CATALOG = {
    "smm_reseller": {
        "name": "🚀 SMM & Vingboost Auto-Reseller Pro",
        "author": CREATOR,
        "price": "490 ₽",
        "desc": (
            "Полный автопилот перепродажи накрутки соцсетей (Telegram, TikTok, VK, Twitch, YouTube) на FunPay!\n"
            "— Автор: yuepi-FPS\n"
            "— Моментальное размещение заказов через API провайдера\n"
            "— Маржинальность 300-500% на пассиве\n"
            "— Авто-уведомления об остатке баланса и статусе"
        )
    },
    "gemini_sales": {
        "name": "🧠 Gemini Smart Sales Agent Pro",
        "author": CREATOR,
        "price": "390 ₽",
        "desc": (
            "Интеллектуальный ИИ-продавец на базе Google Gemini 2.0 / 3.8 Flash.\n"
            "— Автор: yuepi-FPS\n"
            "— Защита от спама и перебивания диалогов (умные задержки)\n"
            "— Память диалога и мягкая допродажа сопутствующих лотов\n"
            "— Авто-эскалация на продавца при спорных ситуациях"
        )
    },
    "review_booster": {
        "name": "🎁 Review Booster 5★ & Gift Delivery",
        "author": CREATOR,
        "price": "199 ₽",
        "desc": (
            "Автоматический бустер 5-звёздочных отзывов для вашего профиля.\n"
            "— Автор: yuepi-FPS\n"
            "— Автовыдача секретных подарков (игры Steam, твики, аватарки) за отзыв 5★\n"
            "— Автоматические напоминания покупателям через 60 минут после выполнения заказа\n"
            "— Поднимает конверсию положительных отзывов на 85%"
        )
    },
    "restock_guard": {
        "name": "🛡 Auto-Restock & Position Guard",
        "author": CREATOR,
        "price": "199 ₽",
        "desc": (
            "Защитник ваших позиций в топе выдачи FunPay.\n"
            "— Автор: yuepi-FPS\n"
            "— Автоматическое восстановление количества до 999 шт при опустошении\n"
            "— Рандомизация автоподнятия (Anti-Ban) для защиты от алгоритмов площадки\n"
            "— Мониторинг деактивированных лотов 24/7"
        )
    }
}

def generate_plugin_purchase(funpay_id: str | int, plugin_id: str) -> dict:
    """
    Генерирует лицензию и готовый пакет для покупателя.
    """
    if plugin_id not in CATALOG:
        return {"error": "Плагин не найден в каталоге"}
    
    key = LicenseManager.generate_license(funpay_id, plugin_id)
    return {
        "plugin_id": plugin_id,
        "name": CATALOG[plugin_id]["name"],
        "funpay_id": funpay_id,
        "license_key": key,
        "instruction": (
            f"1. Скачайте файл плагина '{plugin_id}.py' выше.\n"
            f"2. Поместите его в папку plugins/ вашего FunPay Studio.\n"
            f"3. В созданном configs/{plugin_id}.json укажите лицензионный ключ:\n"
            f"   {key}\n"
            f"4. Перезапустите FunPay Studio — плагин активирован навсегда!"
        )
    }

if __name__ == "__main__":
    print("=" * 60)
    print("  FunPay Studio — Store Engine Module Loaded Successfully")
    print("  Официальный канал: https://t.me/funpaystudio")
    print("  Магазин плагинов:  https://t.me/fps_plugins1")
    print("=" * 60)
    for pid, p in CATALOG.items():
        print(f"\n[КАТАЛОГ] {p['name']} — {p['price']}")
        print(f"Пример лицензии для ID 11535828: {LicenseManager.generate_license(11535828, pid)}")
