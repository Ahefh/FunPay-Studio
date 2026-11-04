# ==============================================================================
# FunPay Studio (FPS) — Официальный плагин
# Создатель: yuepi-FPS
# Официальный канал: https://t.me/funpaystudio
# Каталог плагинов:   https://t.me/fps_plugins1
# Наш FunPay магазин: https://funpay.com/users/11535828/
# Версия под 2026 год
# ==============================================================================

from __future__ import annotations
import time
from typing import TYPE_CHECKING
from FunPayAPI.updater.events import NewMessageEvent
from Utils import cardinal_tools

if TYPE_CHECKING:
    from cardinal import Cardinal
import json
import telebot
from os.path import exists
from logging import getLogger
from datetime import datetime
from locales.localizer import Localizer

NAME = "Del old users plugin"
VERSION = "0.0.2"
DESCRIPTION = "Позволяет раз в какое-то время удалять из списка уже написавших пользователей, чтобы приветственное сообщение отправлялось снова." \
              "\n/del_old_users [количество дней] - если нету сообщений в чате с пользователем Х дней, то ему повторно отправится приветственное сообщение" \
              "\nЕсли пользователь пишет Вам каждый день, а настройка стоит 2-дневная, то он никогда не получит повторное приветственное сообщение." \
              '\nНе работает для чатов, которые были до добавления плагина - плагин должен "увидеть" новое сообщение, чтобы начать отсчет времени (рекомендовано удалить файл storage/cache/old_users и перезапустить бота)' \
              "\nЖелательно предварительно сохранить файл для возможности откатиться к предыдущему варианту." \
              '\n"/del_old_users -1" - выключить'

localizer = Localizer()
localizer = localizer.translate
CREDITS = "yuepi-FPS"
UUID = "37594f65-5033-41aa-9b86-7b9fa475a625"
SETTINGS_PAGE = False
old_users = dict()
settings = {"days": 2}
last_newsletter_time = None
logger = getLogger("FPS.del_old_users")
LOGGER_PREFIX = "[DEL OLD USERS PLUGIN]"
log_msg_date = datetime.now().date()

def init_commands(cardinal: Cardinal, *args):
    if not all([x in localizer("about", cardinal.VERSION) for x in ("sidor0912", "funpay_cardinal")]):
        for chat_id in cardinal.telegram.notification_settings.keys():
            text = "⚠️ Привет! Если ты видишь это сообщение - ты c очень большой вероятностью используешь украденный у меня ( @sidor0912 ) код.\n\n<b>Исходник FunPay Studio:</b> https://github.com/sidor0912/FunPayStudio\n" \
                   "Ты можешь ознакомиться по ссылке со списком моих коммитов: https://github.com/sidor0912/FunPayStudio/commits/main/\n" \
                   "И со списком релизов: https://github.com/sidor0912/FunPayStudio/releases\n\n" \
                   "Я - единственный, кто делает обновы FunPay Studio и его плагинов после скама @woopertail . Абсолютно полностью пиздить МОИ обновы," \
                   " не привнеся абсолютно ничего своего и не спросив разрешения - низко.\n\n" \
                   "<b>Новости об обновах:</b> @fpc_updates (ознакомьтесь с датами, содержимым постов и описанием канала)\n" \
                   "<b>Канал с плагинами:</b> @fps_plugins1 (аналогично)\n" \
                   "<b>Чат:</b> @funpaystudio"
            cardinal.telegram.bot.send_message(chat_id=chat_id, text=text)
            time.sleep(1)
        cardinal_tools.shut_down()
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot
    if exists("storage/plugins/del_old_users_plugin_data.json"):
        with open("storage/plugins/del_old_users_plugin_data.json", "r", encoding="utf-8") as f:
            global old_users
            old_users_dict = json.loads(f.read())
            for k, v in old_users_dict.items():
                old_users [int(k)] = v
            logger.info(F"{LOGGER_PREFIX} Словарь пользователей загружен.")
            logger.debug(f"{LOGGER_PREFIX} Список пользователей: {old_users}")
    if exists("storage/plugins/del_old_users_settings.json"):
        with open("storage/plugins/del_old_users_settings.json", "r", encoding="utf-8") as f:
            global settings
            settings = json.loads(f.read())
            logger.info(F"{LOGGER_PREFIX} Настройки загружены.")

    def del_old_users (m: telebot.types.Message):
        if len(m.text.split(" ")) == 2:
            try:
                _, days = m.text.split(" ")
                settings["days"] = float(days.replace(",", "."))
                with open("storage/plugins/del_old_users_settings.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(settings, indent=4, ensure_ascii=False))
                bot.send_message(m.chat.id, f"Успешно изменено количество дней для удаления написавших пользователей на <code>{settings['days']}</code>.")
            except:
                logger.warning(F"{LOGGER_PREFIX} Произошла ошибка при обработке команды.")
                logger.debug("TRACEBACK", exc_info=True)
                bot.send_message(m.chat.id, "Произошла ошибка при обработке команды.")
        else:
            bot.send_message(m.chat.id,"Команда введена не правильно! /del_old_users [количество дней]")

    tg.msg_handler(del_old_users, commands=["del_old_users"])
    cardinal.add_telegram_commands(UUID, [
        ("del_old_users", "Удалять уже написавших пользователей (Х дней)", True),
    ])

def message_hook(cardinal: Cardinal, event: NewMessageEvent):
    if settings["days"] == -1:
        return
    now_time_in_sec = time.time()
    old_users[event.message.chat_id] = now_time_in_sec
    global log_msg_date
    if datetime.now().date() != log_msg_date:
        logger.debug(f"{LOGGER_PREFIX} Список пользователей: {old_users}")
        log_msg_date = datetime.now().date()
    keys_to_remove = []
    for chat_id, t in old_users.items():
        if now_time_in_sec - t >= 60*60*24*settings["days"]:
            cardinal.old_users.remove(chat_id)
            keys_to_remove.append(chat_id)
    cardinal_tools.cache_old_users(cardinal.old_users)
    for key in keys_to_remove:
        del old_users[key]
    with open("storage/plugins/del_old_users_plugin_data.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(old_users, indent=4, ensure_ascii=False))


BIND_TO_PRE_INIT = [init_commands]
BIND_TO_NEW_MESSAGE = [message_hook]
BIND_TO_DELETE = None