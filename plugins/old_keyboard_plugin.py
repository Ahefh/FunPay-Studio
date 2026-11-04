# ==============================================================================
# FunPay Studio (FPS) — Официальный плагин
# Создатель: yuepi-FPS
# Официальный канал: https://t.me/funpaystudio
# Каталог плагинов:   https://t.me/fps_plugins1
# Наш FunPay магазин: https://funpay.com/users/11535828/
# Версия под 2026 год
# ==============================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cardinal import Cardinal

import telebot.types
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton


NAME = "Old Keyboard Plugin"
VERSION = "0.0.1"
DESCRIPTION = "Данный плагин добавляет команду /keyboard," \
              "которая открывает клавиатуру из старых версий FunPay Studio'а."
CREDITS = "yuepi-FPS"
UUID = "8d46ec6e-9cba-4dbb-9adf-a962366a5d12"
SETTINGS_PAGE = False

KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True)\
    .row(KeyboardButton("📋 Логи 📋"), KeyboardButton("⚙️ Настройки ⚙️"), KeyboardButton("📈 Система 📈"))\
    .row(KeyboardButton("🔄 Перезапуск 🔄"), KeyboardButton("❌ Закрыть ❌"), KeyboardButton("🔌 Отключение 🔌"))


def main(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot

    def open_keyboard(m: Message):
        bot.send_message(m.chat.id, "Клавиатура появилась!", reply_markup=KEYBOARD)

    def close_keyboard(m: Message):
        bot.send_message(m.chat.id, "Клавиатура скрыта!", reply_markup=telebot.types.ReplyKeyboardRemove())

    cardinal.add_telegram_commands(UUID, [
        ("keyboard", "показывает / скрывает клавиатуру старых версий FunPay Studio'а.", True)
    ])

    tg.msg_handler(open_keyboard, commands=["keyboard"])

    tg.msg_handler(tg.send_logs, func=lambda m: m.text == "📋 Логи 📋")
    tg.msg_handler(tg.send_settings_menu, func=lambda m: m.text == "⚙️ Настройки ⚙️")
    tg.msg_handler(tg.send_system_info, func=lambda m: m.text == "📈 Система 📈")
    tg.msg_handler(tg.restart_cardinal, func=lambda m: m.text == "🔄 Перезапуск 🔄")
    tg.msg_handler(close_keyboard, func=lambda m: m.text == "❌ Закрыть ❌")
    tg.msg_handler(tg.ask_power_off, func=lambda m: m.text == "🔌 Отключение 🔌")


BIND_TO_PRE_INIT = [main]
BIND_TO_DELETE = None
