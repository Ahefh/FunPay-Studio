# ==============================================================================
# FunPay Studio (FPS) — Официальный плагин
# Создатель: yuepi-FPS
# Официальный канал: https://t.me/funpaystudio
# Каталог плагинов:   https://t.me/fps_plugins1
# Наш FunPay магазин: https://funpay.com/users/11535828/
# Версия под 2026 год
# ==============================================================================

from __future__ import annotations

import json
from os.path import exists
from threading import Thread
from typing import TYPE_CHECKING

from tg_bot import CBT

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.updater.events import *

if TYPE_CHECKING:
    from cardinal import Cardinal
import telebot
from logging import getLogger
from bs4 import BeautifulSoup as bs
from FunPayAPI.types import MessageTypes as MT
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B

NAME = "SRAS Info Plugin"
VERSION = "0.0.4"
DESCRIPTION = "Отслеживает изменения в ограничениях рейтинга на странице https://funpay.com/sras/info"

CREDITS = "yuepi-FPS"
UUID = "e3a3b2f3-b890-4f48-a5f0-a9c49cb4ab07"
SETTINGS_PAGE = True

logger = getLogger("FPS.sras_info_plugin")
LOGGER_PREFIX = "[SRAS INFO]"
SETTINGS = {
    "chats": []
}
CBT_TEXT_SWITCH = "sras_info.switch"


def init(cardinal: Cardinal, *args):
    tg = cardinal.telegram
    bot = tg.bot
    sras_info = {}
    last_sras_time = 0
    no_limitations_text = "В данный момент на вашем аккаунте нет никаких ограничений. Если бы мы были Макдональдсом, вы бы могли стать «Лучшим продавцом месяца». Так держать!"

    if exists("storage/plugins/sras_info.json"):
        with open("storage/plugins/sras_info.json", "r", encoding="utf-8") as f:
            global SETTINGS
            settings = json.loads(f.read())
            SETTINGS.update(settings)

    def save_config():
        with open("storage/plugins/sras_info.json", "w", encoding="utf-8") as f:
            global SETTINGS
            f.write(json.dumps(SETTINGS, indent=4, ensure_ascii=False))

    def open_settings(call: telebot.types.CallbackQuery):
        keyboard = K()
        keyboard.add(B(f"{'🟢' if call.message.chat.id in SETTINGS['chats'] else '🔴'} Уведомлять в этом чате",
                       callback_data=f"{CBT_TEXT_SWITCH}:"))
        keyboard.add(B("◀️ Назад", callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:0"))
        bot.edit_message_text("В данном разделе Вы можете настроить получение уведомлений о ограничениях рейтинга.",
                              call.message.chat.id, call.message.id, reply_markup=keyboard)

    def switch(call: telebot.types.CallbackQuery):
        if call.message.chat.id in SETTINGS["chats"]:
            SETTINGS["chats"].remove(call.message.chat.id)
        else:
            SETTINGS["chats"].append(call.message.chat.id)
        save_config()
        open_settings(call)

    def get_sras_info(cardinal: Cardinal) -> dict[str, int]:
        r = cardinal.account.method("get", "https://funpay.com/sras/info", {}, {}, raise_not_200=True)
        soup = bs(r.text, "lxml")
        body = soup.find("tbody")
        result = {}
        if body is None:
            text = soup.find("p", class_="text-bold")
            if text:
                nonlocal no_limitations_text
                no_limitations_text = text.text
            return result
        for tr in body.find_all("tr"):
            section, stars = tr.find_all("td")
            section = section.find("a")["href"].split("/")[-3:-1]
            stars = int("".join([i for i in stars.text if i.isdigit()]))
            result[tuple(section)] = stars
        logger.debug(f"{LOGGER_PREFIX} Ограничения: {result}")
        return result

    def get_sras_changes(d1: dict, d2: dict) -> dict:
        result = {}
        for key in set(list(d1.keys()) + list(d2.keys())):
            d1.setdefault(key, 5)
            d2.setdefault(key, 5)
            if d1[key] != d2[key]:
                result[key] = (d1[key], d2[key])
        nonlocal sras_info
        sras_info = {k: v for k, v in d2.items() if v != 5}  # обновляем старый словарь
        logger.debug(f"{LOGGER_PREFIX} Изменения: {result}")
        nonlocal last_sras_time
        last_sras_time = time.time()
        return result

    try:
        sras_info = get_sras_info(cardinal)
    except:
        logger.warning(f"{LOGGER_PREFIX} Не удалось получить информацию о ограничениях рейтинга.")
        logger.debug("TRACEBACK", exc_info=True)

    def send_sras_changes(sras_changes, chat_ids):
        good = {}
        bad = {}
        str4tg = ""
        for k, v in sras_changes.items():
            if v[1] > v[0]:
                good[k] = v
            else:
                bad[k] = v

        def to_str(d: dict):
            res = ""
            d2 = {}
            for k, v in d.items():
                subcategory = cardinal.account.get_subcategory(
                    SubCategoryTypes.COMMON if k[0] == "lots" else SubCategoryTypes.CURRENCY,
                    int(k[1]))
                if subcategory is not None:
                    d2[subcategory] = v
                else:
                    logger.warning(f"{LOGGER_PREFIX} Категория {k} не найдена")
                    logger.debug("TRACEBACK")
            for k, v in sorted(d2.items(), key=lambda x: (x[0].category.name.lower(), x[0].fullname.lower())):
                res += f"<a href='{k.public_link}'>{k.fullname}</a>: {v[0]}⭐ -> {v[1]}⭐\n"
            return res

        if good:
            str4tg += f"🟢 Улучшения рейтинга:\n\n{to_str(good)}"
        if bad:
            str4tg += f"\n\n🔴 Ухудшения рейтинга:\n\n{to_str(bad)}"

        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id, str4tg, disable_web_page_preview=True)
            except:
                logger.warning(f"{LOGGER_PREFIX} Произошла ошибка при отпраке уведомления в чат {chat_id}")
                logger.debug("TRACEBACK", exc_info=True)
            time.sleep(1)

    def msg_handler(c: Cardinal, e: NewMessageEvent | LastChatMessageChangedEvent):
        if not c.old_mode_enabled:
            if isinstance(e, LastChatMessageChangedEvent):
                return
            mtype = e.message.type
        else:
            mtype = e.chat.last_message_type
        if time.time() - last_sras_time < 5 * 60:
            return
        if mtype in [MT.REFUND, MT.REFUND_BY_ADMIN, MT.PARTIAL_REFUND, MT.FEEDBACK_DELETED, MT.NEW_FEEDBACK,
                     MT.FEEDBACK_CHANGED, MT.ORDER_CONFIRMED_BY_ADMIN, MT.ORDER_CONFIRMED, MT.ORDER_REOPENED]:
            def run_func():
                sras_changes = get_sras_changes(sras_info, get_sras_info(c))
                if not sras_changes:
                    return
                send_sras_changes(sras_changes, SETTINGS["chats"])

            Thread(target=run_func, daemon=True).start()

    def sras_info_handler(m: telebot.types.Message):
        sras_info_ = get_sras_info(cardinal)
        if not sras_info_:
            text4tg = f"<b>{no_limitations_text}</b>"
        else:
            text4tg = "<u><b>Текущие ограничения рейтига:</b></u>\n\n"
            for k, v in sras_info_.items():
                subcategory = cardinal.account.get_subcategory(
                    SubCategoryTypes.COMMON if k[0] == "lots" else SubCategoryTypes.CURRENCY,
                    int(k[1]))
                if subcategory:
                    text4tg += f"<a href='{subcategory.public_link}'>{subcategory.fullname}</a>: {v}⭐\n"
                else:
                    logger.warning(f"{LOGGER_PREFIX} Категория {k} не найдена")
                    logger.debug("TRACEBACK")
        bot.send_message(m.chat.id, text4tg, disable_web_page_preview=True)

    setattr(msg_handler, "plugin_uuid", UUID)
    cardinal.new_message_handlers.append(msg_handler)
    cardinal.last_chat_message_changed_handlers.append(msg_handler)
    tg.msg_handler(sras_info_handler, commands=["sras_info"])
    tg.cbq_handler(switch, lambda c: f"{CBT_TEXT_SWITCH}" in c.data)
    tg.cbq_handler(open_settings, lambda c: f"{CBT.PLUGIN_SETTINGS}:{UUID}" in c.data)
    cardinal.add_telegram_commands(UUID, [
        ("sras_info", "Текущие ограничения рейтинга", True)
    ])


BIND_TO_PRE_INIT = [init]
BIND_TO_DELETE = None
