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
from typing import TYPE_CHECKING

from Utils import cardinal_tools

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.updater.events import *
from FunPayAPI.types import MessageTypes
from FunPayAPI.common.utils import RegularExpressions
import tg_bot.static_keyboards
from os.path import exists
from tg_bot import CBT
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B
from bs4 import BeautifulSoup as bs
import telebot
import logging
from locales.localizer import Localizer
from Utils.cardinal_tools import format_order_text
logger = logging.getLogger("FPS.handlers")
localizer = Localizer()
_ = localizer.translate

NAME = "Review Chat Reply"
VERSION = "0.0.4"
DESCRIPTION = "Плагин добавляет новую функцию, которая отвечает клиентам в чате после того, как они оставят отзыв."
CREDITS = "yuepi-FPS"
UUID = "9e63856d-ba0e-455e-8800-79d7e1f8765d"
SETTINGS_PAGE = True

CBT_TEXT_EDIT = "ReviewChatReply_Edit"
CBT_TEXT_EDITED = "ReviewChatReply_Edited"
CBT_TEXT_SWITCH = "ReviewChatReply_Switch"
CBT_TEXT_SHOW = "ReviewChatReply_Show"

SETTINGS = {
    "on_feedback_changed": False,
    "watermark": True,
    "1": {
        "enable": False,
        "text": "",
        "title": "⭐"
    },
    "2": {
        "enable": False,
        "text": "",
        "title": "⭐⭐"
    },
    "3": {
        "enable": False,
        "text": "",
        "title": "⭐⭐⭐"
    },
    "4": {
        "enable": False,
        "text": "",
        "title": "⭐⭐⭐⭐"
    },
    "5": {
        "enable": False,
        "text": "",
        "title": "⭐⭐⭐⭐⭐"
    },
    "6": {
        "enable": False,
        "text": "",
        "title": "🗑"
    },
}


def init(cardinal: Cardinal):
    if not all([x in _("about", cardinal.VERSION) for x in ("sidor0912", "funpay_cardinal")]):
        for chat_id in cardinal.telegram.notification_settings.keys():
            text = "⚠️ Привет! Если ты видишь это сообщение - ты c очень большой вероятностью используешь украденный у меня ( @sidor0912 ) код.\n\n<b>Исходник FunPay Studio:</b> https://github.com/sidor0912/FunPayStudio\n" \
                   "Ты можешь ознакомиться по ссылке со списком моих коммитов: https://github.com/sidor0912/FunPayStudio/commits/main/\n" \
                   "И со списком релизов: https://github.com/sidor0912/FunPayStudio/releases\n\n" \
                   "Я - единственный, кто делает обновы FunPay Studio и его плагинов после скама @woopertail . Абсолютно полностью пиздить МОИ обновы," \
                   " не привнеся абсолютно ничего своего и не спросив разрешения - низко.\n\n" \
                   "<b>Новости об обновлениях:</b> @fpc_updates (ознакомьтесь с датами, содержимым постов и описанием канала)\n" \
                   "<b>Канал с плагинами:</b> @fps_plugins1 (аналогично)\n" \
                   "<b>Чат:</b> @funpaystudio"
            cardinal.telegram.bot.send_message(chat_id=chat_id, text=text)
            time.sleep(1)
        cardinal_tools.shut_down()
    tg = cardinal.telegram
    bot = tg.bot

    if exists("storage/plugins/review_chat_reply.json"):
        with open("storage/plugins/review_chat_reply.json", "r", encoding="utf-8") as f:
            global SETTINGS
            SETTINGS.update(json.loads(f.read()))

    def edit(call: telebot.types.CallbackQuery):
        stars = call.data.replace(f"{CBT_TEXT_EDIT}:", "")
        variables = ["v_date", "v_date_text", "v_full_date_text", "v_time", "v_full_time", "v_username", "v_order_id", "v_order_title", "v_photo"]
        text = f"Введите текст ответа отзыв с {SETTINGS[stars]['title']}.\n\n{_('v_list')}:\n" + "\n".join(_(i) for i in variables)
        result = bot.send_message(call.message.chat.id, text, reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN())

        tg.set_state(call.message.chat.id, result.id, call.from_user.id, CBT_TEXT_EDITED, {"stars": stars})
        bot.answer_callback_query(call.id)

    def edited(message: telebot.types.Message):
        stars = tg.get_state(message.chat.id, message.from_user.id)["data"]["stars"]
        tg.clear_state(message.chat.id, message.from_user.id, True)
        if message.text == "-":
            message.text = ""
        SETTINGS[stars]["text"] = message.text
        save_config()
        keyboard = K() \
            .row(B("◀️ Назад", callback_data=f"{CBT.PLUGIN_SETTINGS}:{UUID}"),
                 B("✏️ Изменить", callback_data=f"{CBT_TEXT_EDIT}:{stars}"))
        bot.reply_to(message, f"✅ Текст ответа отзыв с {SETTINGS[stars]['title']} изменен!", reply_markup=keyboard)

    def show(call: telebot.types.CallbackQuery):
        stars = call.data.replace(f"{CBT_TEXT_SHOW}:", "")
        keyboard = K().row(B("◀️ Назад", callback_data=f"{CBT.PLUGIN_SETTINGS}:{UUID}"), B("✏️ Изменить", callback_data=f"{CBT_TEXT_EDIT}:{stars}"))
        if SETTINGS[stars]["text"] == "":
            if stars == "6":
                bot.edit_message_text(f"❌ Ответ на удаленный отзыв не установлен.", call.message.chat.id, call.message.id, reply_markup=keyboard)
            else:
                bot.edit_message_text(f"❌ Ответ на отзыв с {SETTINGS[stars]['title']} не установлен.", call.message.chat.id, call.message.id, reply_markup=keyboard)
        else:
            if stars == "6":
                bot.edit_message_text(f"Ответ на удаленный отзыв:\n<code>{SETTINGS[stars]['text']}</code>", call.message.chat.id, call.message.id, reply_markup=keyboard)
            else:
                bot.edit_message_text(f"Ответ на отзыв с {SETTINGS[stars]['title']}:\n<code>{SETTINGS[stars]['text']}</code>", call.message.chat.id, call.message.id, reply_markup=keyboard)

        bot.answer_callback_query(call.id)

    def save_config():
        with open("storage/plugins/review_chat_reply.json", "w", encoding="utf-8") as f:
            global SETTINGS
            f.write(json.dumps(SETTINGS, indent=4, ensure_ascii=False))

    def switch(call: telebot.types.CallbackQuery):
        if "on_feedback_changed" in call.data:
            SETTINGS["on_feedback_changed"] = not SETTINGS["on_feedback_changed"]
        elif "watermark" in call.data:
            SETTINGS["watermark"] = not SETTINGS["watermark"]
        else:
            SETTINGS[call.data.replace(f"{CBT_TEXT_SWITCH}:", "")]["enable"] = not SETTINGS[call.data.replace(f"{CBT_TEXT_SWITCH}:", "")]["enable"]
        save_config()
        open_settings(call)

    def open_settings(call: telebot.types.CallbackQuery):
        keyboard = K()
        keyboard.add(B(f"{'🟢' if SETTINGS['watermark'] else '🔴'} Вотермарка сообщений",
                       callback_data=f"{CBT_TEXT_SWITCH}:watermark"))
        keyboard.add(B(f"{'🟢' if SETTINGS['on_feedback_changed'] else '🔴'} Отвечать когда отзыв изменяется", callback_data=f"{CBT_TEXT_SWITCH}:on_feedback_changed"))
        for i in range(1, 7):
            keyboard.row(B(f"{SETTINGS[str(i)]['title']}{' '*(10-i)}", callback_data=f"{CBT_TEXT_SHOW}:{i}"),
                         B("🟢" if SETTINGS[str(i)]["enable"] else "🔴", callback_data=f"{CBT_TEXT_SWITCH}:{i}"))
        keyboard.add(B("◀️ Назад", callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:0"))

        bot.edit_message_text("В данном разделе вы можете настроить текста ответа на отзывы.", call.message.chat.id, call.message.id, reply_markup=keyboard)
        bot.answer_callback_query(call.id)

    tg.msg_handler(edited, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, CBT_TEXT_EDITED))
    tg.cbq_handler(edit, lambda c: f"{CBT_TEXT_EDIT}" in c.data)
    tg.cbq_handler(show, lambda c: f"{CBT_TEXT_SHOW}" in c.data)
    tg.cbq_handler(switch, lambda c: f"{CBT_TEXT_SWITCH}" in c.data)
    tg.cbq_handler(open_settings, lambda c: f"{CBT.PLUGIN_SETTINGS}:{UUID}" in c.data)


def message_hook(cardinal: Cardinal, event: NewMessageEvent):
    if event.message.type not in [MessageTypes.NEW_FEEDBACK, MessageTypes.FEEDBACK_CHANGED, MessageTypes.FEEDBACK_DELETED]:
        return
    if bs(event.message.html, "html.parser").find("a").text == cardinal.account.username:
        return
    if event.message.type == MessageTypes.FEEDBACK_CHANGED and not SETTINGS["on_feedback_changed"]:
        return

    id = RegularExpressions().ORDER_ID.findall(str(event.message))[0][1:]
    stars = "6"
    order = cardinal.account.get_order(id)
    if event.message.type != MessageTypes.FEEDBACK_DELETED:
        stars = str(order.review.stars)
    txt = SETTINGS[stars]["text"]

    if SETTINGS[stars]["enable"] and txt != "":
        txt = format_order_text(txt, order)
        cardinal.send_message(event.message.chat_id, txt, event.message.chat_name, watermark=SETTINGS["watermark"])


BIND_TO_PRE_INIT = [init]
BIND_TO_NEW_MESSAGE = [message_hook]
BIND_TO_DELETE = None
