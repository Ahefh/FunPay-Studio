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
from threading import Thread
from typing import TYPE_CHECKING

from FunPayAPI.common.utils import RegularExpressions

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.account import Account
from FunPayAPI.updater.events import *
from FunPayAPI.types import MessageTypes
import tg_bot.static_keyboards
from os.path import exists
from tg_bot import CBT
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B
from bs4 import BeautifulSoup as bs
import telebot
import logging
from locales.localizer import Localizer

logger = logging.getLogger("FPS.auto_withdraw")
LOGGER_PREFIX = "[AUTO WITHDRAW]"

NAME = "Auto Withdraw"
VERSION = "0.0.10"
DESCRIPTION = "Плагин добавляет новую функцию автовывода для вашего бота, перед выводом - настройте способ вывода. В случае проблем пишите @sidor0912."
CREDITS = "yuepi-FPS"
UUID = "f70eb246-8239-4fec-8f85-65544fbc08a0"
SETTINGS_PAGE = False

CBT_MAIN3 = "CBT_MAIN3"
CBT_WITHDRAW_MENU = "CBT_WITHDRAW_MENU"
CBT_WITHDRAW_ACCEPT_USER_AUTH = "CBT_WITHDRAW_ACCEPT_USER_AUTH"
CBT_TEXT_LISTENER = "CBT_WITHDRAW_TEXT_LISTENER"

SETTINGS = {
    "enable_auto": False,
    "auth_user_id": "0",
    "amount_int": 0,
    "currency_id": "rub",
    "ext_currency_id": "card_rub",
    "wallet": "-",  # 111111••••••1111
    "currency_name": "-",
    "ext_currency_name": "-",
    "keep_on_balance": 0
}

DATA_DATA = {}

localizer = Localizer()
_ = localizer.translate


def SETTINGS_SECTIONS_2() -> K:
    return K() \
        .add(B(_("mm_greetings"), callback_data=f"{CBT.CATEGORY}:gr")) \
        .add(B(_("mm_order_confirm"), callback_data=f"{CBT.CATEGORY}:oc")) \
        .add(B(_("mm_review_reply"), callback_data=f"{CBT.CATEGORY}:rr")) \
        .add(B(_("mm_new_msg_view"), callback_data=f"{CBT.CATEGORY}:mv")) \
        .add(B(_("mm_blacklist"), callback_data=f"{CBT.CATEGORY}:bl")) \
        .add(B(_("mm_configs"), callback_data=CBT.CONFIG_LOADER)) \
        .add(B(_("mm_authorized_users"), callback_data=f"{CBT.AUTHORIZED_USERS}:0")) \
        .add(B(_("mm_proxy"), callback_data=f"{CBT.PROXY}:0")) \
        .row(B(_("gl_back"), callback_data=CBT.MAIN), B("▶️ Еще", callback_data=CBT_MAIN3))


MAIN3PAGE = K() \
    .add(B("💰 Управление авто-выводом", callback_data=f"{CBT_WITHDRAW_MENU}")) \
    .add(B("◀️ Назад", callback_data=CBT.MAIN2))
AUTO_WITHDRAW_MENU_NOT_AUTH = K() \
    .row(B("✅ Да", callback_data=CBT_WITHDRAW_ACCEPT_USER_AUTH), B("◀️ Назад", callback_data=CBT_MAIN3))
AUTO_WITHDRAW_MENU_AUTH_FAILED = K() \
    .add(B("◀️ Назад", callback_data=CBT_MAIN3))
AUTO_WITHDRAW_MENU_AUTH = K() \
    .add(B("⚙ Настроить способ вывода", callback_data=f"{CBT_WITHDRAW_MENU}:1:0")) \
    .add(B("⚙ Настроить сумму автовывода", callback_data=f"{CBT_WITHDRAW_MENU}:2")) \
    .add(B("⚙ Настроить остаток на балансе при выводе", callback_data=f"{CBT_WITHDRAW_MENU}:keep")) \
    .add(B("💰 Вывести средства сейчас", callback_data=f"{CBT_WITHDRAW_MENU}:3")) \
    .add(B("☕️ Поддержать создателей (yuepi-FPS)", url="https://funpay.com/users/11535828/")) \
    .add(B("◀️ Назад", callback_data=CBT_MAIN3))


def calc(account: Account, amount_int: float):
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {
        "csrf_token": account.csrf_token,
        "preview": "1",
        "currency_id": SETTINGS["currency_id"],
        "ext_currency_id": SETTINGS["ext_currency_id"],
        "wallet": SETTINGS["wallet"],
        "amount_int": amount_int
    }
    return account.method("post", "https://funpay.com/withdraw/withdraw", headers, data).json()["amount_ext"]


def withdraw(account: Account, amount_int: float) -> float:
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "x-requested-with": "XMLHttpRequest"
    }
    amount_ext = calc(account=account, amount_int=amount_int)
    data = {
        "csrf_token": account.csrf_token,
        "preview": "",
        "currency_id": SETTINGS["currency_id"],
        "ext_currency_id": SETTINGS["ext_currency_id"],
        "wallet": SETTINGS["wallet"],
        "amount_ext": amount_ext
    }
    global fake_balance
    r = account.method("post", "https://funpay.com/withdraw/withdraw", headers, data).json()
    amount_int = float(r["amount_int"])
    fake_balance -= float(amount_int)
    logger.info(
        f"{LOGGER_PREFIX} Вывел {amount_int} {SETTINGS['currency_id']} на {SETTINGS['wallet']} ({amount_ext} {SETTINGS['ext_currency_id']})")
    logger.info(f"{LOGGER_PREFIX} Новый фейк баланс: {fake_balance}")
    return amount_int


listenForMoney = False
listenForMoneyToWithdraw = False
listenForMoneyKeepOnBalance = False
lastCall = None
fake_balance = 0
fake_balance_update_time = 0


def get_balance(cardinal: Cardinal) -> float:
    cardinal.account.get()
    cardinal.balance = cardinal.get_balance()
    curr_id = SETTINGS["currency_id"]
    global fake_balance, fake_balance_update_time
    fake_balance = {
        "rub": cardinal.balance.total_rub,
        "usd": cardinal.balance.total_usd,
        "eur": cardinal.balance.total_eur
    }[curr_id]
    fake_balance_update_time = time.time()
    logger.info(f"{LOGGER_PREFIX} Обновил баланс с обновлением информации: {fake_balance} {curr_id}")
    return fake_balance


def get_currency() -> str:
    match_case = {"rub": "₽",
                  "usd": "$",
                  "eur": "€"}
    curr_id = SETTINGS["currency_id"]
    return match_case[curr_id]


def init(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot

    if exists("storage/cache/auto_withdraw.json"):
        with open("storage/cache/auto_withdraw.json", "r", encoding="utf-8") as f:
            global SETTINGS
            SETTINGS = json.loads(f.read())
            if "currency_name" not in SETTINGS:
                SETTINGS["currency_name"] = "-"
                DATA_DATA = json.loads(
                    bs(cardinal.account.method("get", "https://funpay.com/account/balance", {}, {}).text,
                       "html.parser").find("div", {"class": "withdraw-box"})["data-data"])
                if SETTINGS["currency_id"] in DATA_DATA["currencies"]:
                    SETTINGS["currency_name"] = DATA_DATA["currencies"][SETTINGS["currency_id"]]["unit"]
            if "ext_currency_name" not in SETTINGS:
                SETTINGS["ext_currency_name"] = "-"
                DATA_DATA = json.loads(
                    bs(cardinal.account.method("get", "https://funpay.com/account/balance", {}, {}).text,
                       "html.parser").find("div", {"class": "withdraw-box"})["data-data"])
                if SETTINGS["ext_currency_id"] in DATA_DATA["extCurrencies"]:
                    SETTINGS["ext_currency_name"] = DATA_DATA["extCurrencies"][
                                                        "card_rub" if SETTINGS["ext_currency_id"] == "card_uah" else
                                                        SETTINGS["ext_currency_id"]]["name"] + (
                                                        " UA" if SETTINGS["ext_currency_id"] == "card_uah" else "")
            if "wallet" not in SETTINGS or SETTINGS["wallet"] == "none":
                SETTINGS["wallet"] = "-"

    tg_bot.static_keyboards.SETTINGS_SECTIONS_2 = SETTINGS_SECTIONS_2

    def menuPage(call: telebot.types.CallbackQuery):
        bot.edit_message_text("Выбери категорию настроек.", call.message.chat.id, call.message.id,
                              reply_markup=MAIN3PAGE)
        bot.answer_callback_query(call.id)

    def withdrawMenu(call: telebot.types.CallbackQuery):
        if SETTINGS["auth_user_id"] == "0":
            bot.edit_message_text(
                f"Вы хотите использовать пользователя {call.from_user.username} ({call.from_user.id}) для настройки авто-вывода?",
                call.message.chat.id, call.message.id, reply_markup=AUTO_WITHDRAW_MENU_NOT_AUTH)
        else:
            global DATA_DATA
            global listenForMoney, listenForMoneyToWithdraw, lastCall, listenForMoneyKeepOnBalance
            if SETTINGS["auth_user_id"] == call.from_user.id:
                if call.data == CBT_WITHDRAW_MENU:

                    listenForMoney = False
                    listenForMoneyToWithdraw = False
                    listenForMoneyKeepOnBalance = False
                    bot.edit_message_text(
                        f"В данном разделе вы можете изменить настройки авто-вывода.\n\n<b>Текущий способ вывода:</b> <code>{SETTINGS['ext_currency_name']}</code>\n<b>Текущая валюта:</b> <code>{SETTINGS['currency_name']}</code>\n<b>Текущая карта:</b> <code>{SETTINGS['wallet']}</code>\n<b>Кол-во денег для вывода:</b> <code>{SETTINGS['amount_int']}</code>\n<b>Оставлять на балансе при автовыводе:</b> <code>{SETTINGS['keep_on_balance']}</code>\n",
                        call.message.chat.id, call.message.id, reply_markup=AUTO_WITHDRAW_MENU_AUTH)
                elif call.data == f"{CBT_WITHDRAW_MENU}:1:0":
                    KEYBOARD = K()
                    DATA_DATA = json.loads(
                        bs(cardinal.account.method("get", "https://funpay.com/account/balance", {}, {}).text,
                           "html.parser").find("div", {"class": "withdraw-box"})["data-data"])
                    for curr in DATA_DATA["currencies"]:
                        KEYBOARD.add(
                            B(DATA_DATA["currencies"][curr]["unit"], callback_data=f"{CBT_WITHDRAW_MENU}:1:1:{curr}"))

                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    bot.edit_message_text(f"Выберите валюту.", call.message.chat.id, call.message.id,
                                          reply_markup=KEYBOARD)
                elif f"{CBT_WITHDRAW_MENU}:1:1:" in call.data:
                    curr = call.data.replace(f"{CBT_WITHDRAW_MENU}:1:1:", "")
                    SETTINGS["currency_id"] = curr
                    SETTINGS["currency_name"] = DATA_DATA["currencies"][curr]["unit"]
                    KEYBOARD = K()
                    for channel in DATA_DATA["currencies"][curr]["channels"]:
                        KEYBOARD.add(
                            B(channel["name"], callback_data=f"{CBT_WITHDRAW_MENU}:1:2:{channel['extCurrency']}"))
                    if SETTINGS["currency_id"] == "rub":
                        KEYBOARD.add(B("Банковская карта UA", callback_data=f"{CBT_WITHDRAW_MENU}:1:2:card_uah"))
                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    bot.edit_message_text(f"Выберите способ вывода.", call.message.chat.id, call.message.id,
                                          reply_markup=KEYBOARD)
                elif f"{CBT_WITHDRAW_MENU}:1:2:" in call.data:
                    SETTINGS["ext_currency_id"] = call.data.replace(f"{CBT_WITHDRAW_MENU}:1:2:", "")
                    SETTINGS["ext_currency_name"] = DATA_DATA["extCurrencies"][
                                                        "card_rub" if SETTINGS["ext_currency_id"] == "card_uah" else
                                                        SETTINGS["ext_currency_id"]]["name"] + (
                                                        " UA" if SETTINGS["ext_currency_id"] == "card_uah" else "")
                    KEYBOARD = K()
                    for wallet in DATA_DATA["extCurrencies"][
                        "card_rub" if SETTINGS["ext_currency_id"] == "card_uah" else SETTINGS["ext_currency_id"]][
                        "wallets"]:
                        KEYBOARD.add(B(wallet, callback_data=f"{CBT_WITHDRAW_MENU}:1:3:{wallet}"))

                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    bot.edit_message_text("Выберите карту (если её нету здесь тогда добавьте карту на сайте funpay).",
                                          call.message.chat.id, call.message.id, reply_markup=KEYBOARD)
                elif f"{CBT_WITHDRAW_MENU}:1:3:" in call.data:
                    SETTINGS["wallet"] = call.data.replace(f"{CBT_WITHDRAW_MENU}:1:3:", "")
                    bot.edit_message_text("Успешно.", call.message.chat.id, call.message.id,
                                          reply_markup=K().add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU)))

                    with open("storage/cache/auto_withdraw.json", "w", encoding="utf-8") as f:
                        f.write(json.dumps(SETTINGS, indent=4, ensure_ascii=False))
                elif call.data == f"{CBT_WITHDRAW_MENU}:2":
                    KEYBOARD = K()
                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    lastCall = call
                    listenForMoney = True
                    bot.edit_message_text(
                        "Введите сумму для автовывода (минимальное значение кол-ва денег для вывода). Или введите <code>0</code> - чтобы выключить.\nДля успешного автовывода баланс должен быть больше, чем сумма остатка на балансе и кол-ва денег для вывода.",
                        call.message.chat.id, call.message.id, reply_markup=KEYBOARD)
                    tg.set_state(call.message.chat.id, call.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)
                elif call.data == f"{CBT_WITHDRAW_MENU}:keep":
                    KEYBOARD = K()
                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    lastCall = call
                    listenForMoneyKeepOnBalance = True
                    bot.edit_message_text("Введите сумму, которая будет оставаться на балансе при автовыводе.",
                                          call.message.chat.id, call.message.id, reply_markup=KEYBOARD)
                    tg.set_state(call.message.chat.id, call.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)
                elif call.data == f"{CBT_WITHDRAW_MENU}:3":
                    KEYBOARD = K()
                    KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                    lastCall = call
                    listenForMoneyToWithdraw = True
                    tg.set_state(call.message.chat.id, call.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)

                    bot.edit_message_text(
                        f"Введите сумму которую нужно вывести. Ваш баланс ({get_currency()}): <code>{get_balance(cardinal)}</code>",
                        call.message.chat.id, call.message.id, reply_markup=KEYBOARD)
            else:
                bot.edit_message_text(f"Вам запрещено открывать настройки авто-вывода!", call.message.chat.id,
                                      call.message.id, reply_markup=AUTO_WITHDRAW_MENU_AUTH_FAILED)
        bot.answer_callback_query(call.id)

    def acceptUser(call: telebot.types.CallbackQuery):
        SETTINGS["auth_user_id"] = call.from_user.id
        call.data = CBT_WITHDRAW_MENU
        withdrawMenu(call)

    def textListen(message: telebot.types.Message):
        tg.clear_state(message.chat.id, SETTINGS["auth_user_id"])

        global listenForMoney, listenForMoneyToWithdraw, lastCall, listenForMoneyKeepOnBalance
        if listenForMoney or listenForMoneyKeepOnBalance:
            try:
                if float(message.text) < 0:
                    raise ValueError
                if listenForMoney:
                    SETTINGS["amount_int"] = float(message.text)
                else:
                    SETTINGS["keep_on_balance"] = float(message.text)
                listenForMoney = False
                listenForMoneyKeepOnBalance = False
                bot.send_message(message.chat.id, "Успешно.")
                with open("storage/cache/auto_withdraw.json", "w", encoding="utf-8") as f:
                    f.write(json.dumps(SETTINGS, indent=4, ensure_ascii=False))
                bot.delete_message(message.chat.id, message.id)
                lastCall.data = CBT_WITHDRAW_MENU
                withdrawMenu(lastCall)

            except ValueError:
                KEYBOARD = K()
                KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                bot.delete_message(message.chat.id, message.id)
                bot.edit_message_text("Сумма введена неверно. Или введите <code>0</code> - чтобы выключить.",
                                      lastCall.message.chat.id, lastCall.message.id, reply_markup=KEYBOARD)
                tg.set_state(message.chat.id, lastCall.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)
        elif listenForMoneyToWithdraw:
            try:
                if float(message.text) <= 0 or float(message.text) > get_balance(cardinal):
                    raise ValueError

                if SETTINGS["wallet"] != "-":
                    withdraw(cardinal.account, float(message.text))
                    bot.send_message(message.chat.id, "Запрос отправлен.")
                listenForMoneyToWithdraw = False
                bot.delete_message(message.chat.id, message.id)
                lastCall.data = CBT_WITHDRAW_MENU
                withdrawMenu(lastCall)
            except KeyError:
                KEYBOARD = K()
                KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                bot.delete_message(message.chat.id, message.id)
                bot.edit_message_text(
                    f"Сумма введена неверно. Возможно, Вы пытаетесь вывести меньше минимальной суммы вывода.",
                    lastCall.message.chat.id, lastCall.message.id, reply_markup=KEYBOARD)
                tg.set_state(message.chat.id, lastCall.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)
            except:
                KEYBOARD = K()
                KEYBOARD.add(B("◀️ Назад", callback_data=CBT_WITHDRAW_MENU))
                bot.delete_message(message.chat.id, message.id)
                bot.edit_message_text(
                    f"Сумма введена неверно. Ваш баланс ({get_currency()}): <code>{get_balance(cardinal)}</code>",
                    lastCall.message.chat.id, lastCall.message.id, reply_markup=KEYBOARD)
                tg.set_state(message.chat.id, lastCall.message.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER)

    tg.cbq_handler(menuPage, lambda c: c.data == CBT_MAIN3)
    tg.cbq_handler(withdrawMenu, lambda c: CBT_WITHDRAW_MENU in c.data)
    tg.cbq_handler(acceptUser, lambda c: c.data == CBT_WITHDRAW_ACCEPT_USER_AUTH)
    tg.msg_handler(textListen,
                   func=lambda msg: tg.check_state(msg.chat.id, SETTINGS["auth_user_id"], CBT_TEXT_LISTENER))


def message_hook(cardinal: Cardinal, event: NewMessageEvent):
    if event.message.type not in [MessageTypes.ORDER_CONFIRMED, MessageTypes.ORDER_CONFIRMED_BY_ADMIN]:
        return
    if bs(event.message.html, "html.parser").find("a").text == cardinal.account.username:
        return
    global fake_balance, fake_balance_update_time
    id = RegularExpressions().ORDER_ID.findall(str(event.message))[0][1:]
    # todo нужно бы проверку на валюту заказа добавить, но чилл

    fake_balance += cardinal.account.get_order_shortcut(id).price
    logger.info(f"{LOGGER_PREFIX} Обновил баланс без обновления информации: {fake_balance}")
    if SETTINGS["amount_int"] != 0 and SETTINGS["wallet"] != "-" and \
            (fake_balance >= SETTINGS["amount_int"] + SETTINGS["keep_on_balance"] or
             time.time() - fake_balance_update_time > 4 * 3600) and \
            (balance := get_balance(cardinal)) >= SETTINGS["amount_int"] + SETTINGS["keep_on_balance"]:
        withdraw(cardinal.account, balance - SETTINGS["keep_on_balance"])


def message_hook_with_thread(c: Cardinal, e: NewMessageEvent):
    Thread(target=message_hook, args=(c, e), daemon=True).start()


BIND_TO_PRE_INIT = [init]
BIND_TO_NEW_MESSAGE = [message_hook_with_thread]
BIND_TO_DELETE = None
