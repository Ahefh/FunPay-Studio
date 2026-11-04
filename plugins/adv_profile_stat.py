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

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.updater.events import *
from FunPayAPI.common.utils import RegularExpressions
from os.path import exists
import tg_bot.CBT
from bs4 import BeautifulSoup as bs
import telebot
import time
from logging import getLogger

NAME = "Advanced Profile Stat"
VERSION = "0.0.12"
DESCRIPTION = "Данный плагин меняет команду /profile.\nБлагодаря ему можно получить более подробную статистику аккаунта."
CREDITS = "yuepi-FPS"
UUID = "6d607fb3-bfa9-43e6-acc2-2bfe05f86abe"
SETTINGS_PAGE = False

ADV_PROFILE_CB = "adv_profile_1"

ORDER_CONFIRMED = {}
LOGGER_PREFIX = "[ADV_PROFILE_STAT]"
logger = getLogger("FPS.adv_profile_stat")


def generate_adv_profile(cardinal: Cardinal, chat_id: int, mess_id: int) -> str:
    global logger
    account = cardinal.account
    bot = cardinal.telegram.bot
    sales = {"day": 0, "week": 0, "month": 0, "all": 0}
    salesPrice = {"day": 0, "week": 0, "month": 0, "all": 0}
    # ключи вида "day_$", "week_₽", "month_€", "all_$" и т.п.
    refunds = {"day": 0, "week": 0, "month": 0, "all": 0}
    refundsPrice = {"day": 0, "week": 0, "month": 0, "all": 0}
    # ключи вида "day_$", "week_₽", "month_€", "all_$" и т.п.
    canWithdraw = {}
    # ключи вида "hour_$", "day_₽", "2day_€" и т.п.
    account.get()

    for order in ORDER_CONFIRMED.copy():
        curr = ORDER_CONFIRMED[order].get("currency", "¤")
        if time.time() - ORDER_CONFIRMED[order]["time"] > 172800:
            del ORDER_CONFIRMED[order]
            continue
        if time.time() - ORDER_CONFIRMED[order]["time"] > 169200:
            key = "hour_" + curr
        elif time.time() - ORDER_CONFIRMED[order]["time"] > 86400:
            key = "day_" + curr
        else:
            key = "2day_" + curr
        canWithdraw[key] = canWithdraw.get(key, 0) + ORDER_CONFIRMED[order]["price"]

    cardinal.balance = cardinal.get_balance()

    next_order_id, all_sales, locale, subcs = account.get_sales()
    c = 1
    while next_order_id is not None:
        for attempts in range(2, -1, -1):
            try:
                time.sleep(1)
                next_order_id, new_sales, locale, subcs = account.get_sales(start_from=next_order_id, locale=locale,
                                                                            sudcategories=subcs)
                break
            except:
                logger.debug(f"{LOGGER_PREFIX} Не удалось получить список заказов (#{next_order_id}). Осталось попыток: {attempts}")
                logger.debug("TRACEBACK", exc_info=True)
        else:
            raise Exception("Не удалось получить список заказов")

        all_sales += new_sales
        str4tg = f"Обновляю статистику аккаунта. Запрос N{c}. Последний заказ: <a href='https://funpay.com/orders/{next_order_id}/'>{next_order_id}</a>"

        if c % 5 == 0 or next_order_id is None:
            try:
                msg = bot.edit_message_text(
                    str4tg if next_order_id is not None else f"Получил {len(all_sales)} продаж, формирую статистику...",
                    chat_id, mess_id)
            except:
                logger.debug(f"{LOGGER_PREFIX} Не получилось изменить сообщение.")
                logger.debug("TRACEBACK", exc_info=True)
        c += 1

    for sale in all_sales:
        try:
            curr = str(sale.currency)
        except:
            curr = "?"
        if sale.status == OrderStatuses.REFUNDED:
            refunds["all"] += 1
            refundsPrice.setdefault("all_" + curr, 0)
            refundsPrice["all_" + curr] += sale.price
        else:
            sales["all"] += 1
            salesPrice.setdefault("all_" + curr, 0)
            salesPrice["all_" + curr] += sale.price
        date = bs(sale.html, "lxml").find("div", {"class": "tc-date-left"}).text

        if "час" in date or "мин" in date or "сек" in date or "годин" in date or "хвилин" in date or "hour" in date or "min" in date or "sec" in date:
            if sale.status == OrderStatuses.REFUNDED:
                refunds["day"] += 1
                refunds["week"] += 1
                refunds["month"] += 1
                refundsPrice.setdefault("day_" + curr, 0)
                refundsPrice["day_" + curr] += sale.price
                refundsPrice.setdefault("week_" + curr, 0)
                refundsPrice["week_" + curr] += sale.price
                refundsPrice.setdefault("month_" + curr, 0)
                refundsPrice["month_" + curr] += sale.price
            else:
                sales["day"] += 1
                sales["week"] += 1
                sales["month"] += 1
                salesPrice.setdefault("day_" + curr, 0)
                salesPrice["day_" + curr] += sale.price
                salesPrice.setdefault("week_" + curr, 0)
                salesPrice["week_" + curr] += sale.price
                salesPrice.setdefault("month_" + curr, 0)
                salesPrice["month_" + curr] += sale.price
        elif "день" in date or "дня" in date or "дней" in date or "дні" in date or "day" in date:
            if sale.status == OrderStatuses.REFUNDED:
                refunds["week"] += 1
                refunds["month"] += 1
                refundsPrice.setdefault("week_" + curr, 0)
                refundsPrice["week_" + curr] += sale.price
                refundsPrice.setdefault("month_" + curr, 0)
                refundsPrice["month_" + curr] += sale.price
            else:
                sales["week"] += 1
                sales["month"] += 1
                salesPrice.setdefault("week_" + curr, 0)
                salesPrice["week_" + curr] += sale.price
                salesPrice.setdefault("month_" + curr, 0)
                salesPrice["month_" + curr] += sale.price
        elif "недел" in date or "тижд" in date or "тижні" in date or "week" in date:
            if sale.status == OrderStatuses.REFUNDED:
                refunds["month"] += 1
                refundsPrice.setdefault("month_" + curr, 0)
                refundsPrice["month_" + curr] += sale.price
            else:
                sales["month"] += 1
                salesPrice.setdefault("month_" + curr, 0)
                salesPrice["month_" + curr] += sale.price

    def format_number(number):
        num_str = f"{number:,}".replace(',', ' ')
        if '.' in num_str:
            integer_part, decimal_part = num_str.split('.')
            decimal_part = decimal_part.rstrip("0")
            decimal_part = f".{decimal_part}" if decimal_part else ""
        else:
            integer_part = num_str
            decimal_part = ""
        # если число 1 000 - 9 999.99
        if integer_part.count(' ') == 1 and len(integer_part) == 5:
            integer_part = integer_part.replace(' ', "")
        return integer_part + decimal_part

    for s in ("hour", "day", "2day"):
        canWithdraw[s] = ", ".join(
            [f"{format_number(round(v, 2))} {k[-1]}" for k, v in sorted(canWithdraw.items()) if k.startswith(s + "_")])
        if not canWithdraw[s]:
            canWithdraw[s] = "0 ¤"

    for s in ("day", "week", "month", "all"):
        refundsPrice[s] = ", ".join(
            [f"{format_number(round(v, 2))} {k[-1]}" for k, v in sorted(refundsPrice.items()) if k.startswith(s + "_")])
        salesPrice[s] = ", ".join(
            [f"{format_number(round(v, 2))} {k[-1]}" for k, v in sorted(salesPrice.items()) if k.startswith(s + "_")])
        if refundsPrice[s] == "":
            refundsPrice[s] = "0 ¤"
        if salesPrice[s] == "":
            salesPrice[s] = "0 ¤"
    logger.debug(f"{LOGGER_PREFIX} salesPrice = {salesPrice}")
    logger.debug(f"{LOGGER_PREFIX} refundsPrice = {refundsPrice}")
    logger.debug(f"{LOGGER_PREFIX} canWithdraw = {canWithdraw}")
    return f"""Статистика аккаунта <b><i>{account.username}</i></b>

<b>ID:</b> <code>{account.id}</code>
<b>Баланс:</b> <code>{format_number(cardinal.balance.total_rub)} ₽, {format_number(cardinal.balance.total_usd)} $, {format_number(cardinal.balance.total_eur)} €</code>
<b>Незавершенных заказов:</b> <code>{account.active_sales}</code>

<b>Доступно для вывода</b>
<b>Сейчас:</b> <code>{format_number(cardinal.balance.available_rub)} ₽, {format_number(cardinal.balance.available_usd)} $, {format_number(cardinal.balance.available_eur)} €</code>
<b>Через час:</b> <code>+{canWithdraw["hour"]}</code>
<b>Через день:</b> <code>+{canWithdraw["day"]}</code>
<b>Через 2 дня:</b> <code>+{canWithdraw["2day"]}</code>

<b>Товаров продано</b>
<b>За день:</b> <code>{format_number(sales["day"])} ({salesPrice["day"]})</code>
<b>За неделю:</b> <code>{format_number(sales["week"])} ({salesPrice["week"]})</code>
<b>За месяц:</b> <code>{format_number(sales["month"])} ({salesPrice["month"]})</code>
<b>За всё время:</b> <code>{format_number(sales["all"])} ({salesPrice["all"]})</code>

<b>Товаров возвращено</b>
<b>За день:</b> <code>{format_number(refunds["day"])} ({refundsPrice["day"]})</code>
<b>За неделю:</b> <code>{format_number(refunds["week"])} ({refundsPrice["week"]})</code>
<b>За месяц:</b> <code>{format_number(refunds["month"])} ({refundsPrice["month"]})</code>
<b>За всё время:</b> <code>{format_number(refunds["all"])} ({refundsPrice["all"]})</code>

<i>Обновлено:</i>  <code>{time.strftime('%H:%M:%S', time.localtime(account.last_update))}</code>"""


def init_commands(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot

    if exists("storage/plugins/advProfileStat.json"):
        with open("storage/plugins/advProfileStat.json", "r", encoding="utf-8") as f:
            global ORDER_CONFIRMED
            try:
                ORDER_CONFIRMED = json.loads(f.read())
            except:
                pass

    def profile(call: telebot.types.CallbackQuery):
        new_msg = bot.reply_to(call.message, "Обновляю статистику аккаунта (это может занять некоторое время)...")

        try:
            bot.edit_message_text(generate_adv_profile(cardinal, new_msg.chat.id, new_msg.id), call.message.chat.id,
                                  call.message.id, reply_markup=telebot.types.InlineKeyboardMarkup().add(
                    telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data=ADV_PROFILE_CB)))
        except Exception as ex:
            bot.edit_message_text(f"❌ Не удалось обновить статистику аккаунта: {ex}", new_msg.chat.id, new_msg.id)
            global logger
            logger.debug("TRACEBACK", exc_info=True)
            bot.answer_callback_query(call.id)
            return

        bot.delete_message(new_msg.chat.id, new_msg.id)

    def refresh_kb():
        return telebot.types.InlineKeyboardMarkup().row(
            telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data=tg_bot.CBT.UPDATE_PROFILE),
            telebot.types.InlineKeyboardButton("▶️ Еще", callback_data=ADV_PROFILE_CB))

    tg_bot.static_keyboards.REFRESH_BTN = refresh_kb
    tg.cbq_handler(profile, lambda c: c.data == ADV_PROFILE_CB)


def message_hook(cardinal: Cardinal, event: NewMessageEvent):
    if event.message.type not in [MessageTypes.ORDER_CONFIRMED, MessageTypes.ORDER_CONFIRMED_BY_ADMIN,
                                  MessageTypes.ORDER_REOPENED, MessageTypes.REFUND, MessageTypes.REFUND_BY_ADMIN]:
        return
    if event.message.type == MessageTypes.ORDER_CONFIRMED and event.message.initiator_id == cardinal.account.id:
        return
    if event.message.type == MessageTypes.REFUND and event.message.initiator_id != cardinal.account.id:
        return

    id = RegularExpressions().ORDER_ID.findall(str(event.message))[0][1:]

    if event.message.type in [MessageTypes.ORDER_REOPENED, MessageTypes.REFUND, MessageTypes.REFUND_BY_ADMIN]:
        if id in ORDER_CONFIRMED:
            del ORDER_CONFIRMED[id]
    else:
        order = cardinal.get_order_from_object(event.message)
        if order is None:
            return
        if order.buyer_id == cardinal.account.id:
            return
        ORDER_CONFIRMED[id] = {"time": int(time.time()), "price": order.sum, "currency": str(order.currency)}
        with open("storage/plugins/advProfileStat.json", "w", encoding="UTF-8") as f:
            f.write(json.dumps(ORDER_CONFIRMED, indent=4, ensure_ascii=False))


BIND_TO_PRE_INIT = [init_commands]
BIND_TO_NEW_MESSAGE = [message_hook]
BIND_TO_DELETE = None
