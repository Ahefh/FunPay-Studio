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
import logging
import os
import re
import threading
import time
from html import unescape
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Callable

import telebot
from bs4 import BeautifulSoup
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B

from FunPayAPI.account import Account
from FunPayAPI.common.enums import MessageTypes
from FunPayAPI.types import Order, OrderShortcut, Message
from locales.localizer import Localizer
from tg_bot import CBT, static_keyboards as skb, utils as tg_utils

if TYPE_CHECKING:
    from cardinal import Cardinal

NAME = "List Old Orders Plugin"
VERSION = "0.1.0"
DESCRIPTION = "Собирает открытые заказы в 2 списка для подтверждения через поддержку"
CREDITS = "yuepi-FPS"
UUID = "a31cfa24-5ac8-4efb-8c61-7dec3544aa32"
SETTINGS_PAGE = True
PLUGIN_FOLDER = f"storage/plugins/List Old Orders - {UUID}/"
BIND_TO_DELETE = None

logger = logging.getLogger("FPS.list_old_orders")
LOGGER_PREFIX = "[OLD ORDERS]"
localizer = Localizer()
_ = localizer.translate

OLD_ORDER_SECONDS = 3600 * 24
SUPPORT_SYSTEM_AUTHOR_ID = 500
TG_MESSAGE_LIMIT = 4096
MAX_HISTORY_PAGES = 40

CBT_ASK_PATTERN = "OldOrders2.AskPattern"
CBT_PATTERN_TYPE = "OldOrders2.PatternType"
CBT_DEL_PATTERN = "OldOrders2.DelPattern"
CBT_REVIEW = "OldOrders2.Review"


def get_orders_page(acc: Account, start_from: str | None, subcs: dict | None, locale) -> tuple[
        str | None, list[OrderShortcut], str, dict]:
    attempts = 3
    while attempts:
        try:
            result = acc.get_sales(start_from=start_from or None, state="paid", locale=locale, subcategories=subcs)
            break
        except Exception:
            attempts -= 1
            logger.debug("TRACEBACK", exc_info=True)
            time.sleep(1)
    else:
        raise RuntimeError("Не удалось получить страницу заказов")

    next_from, orders, locale, subcs = result
    old_orders = []
    for order in orders:
        parser = BeautifulSoup(order.html, "lxml")
        time_text = parser.find("div", {"class": "tc-date-time"}).text
        if any(marker in time_text for marker in ("сегодня", "сьогодні", "today")):
            continue
        if (datetime.now() - order.date).total_seconds() < OLD_ORDER_SECONDS:
            continue
        old_orders.append(order)
    return next_from, old_orders, locale, subcs


def get_all_old_orders(acc: Account) -> list[OrderShortcut]:
    start_from = ""
    locale = None
    subcs = None
    old_orders = []
    while start_from is not None:
        start_from, page_orders, locale, subcs = get_orders_page(acc, start_from, subcs, locale)
        old_orders.extend(page_orders)
        time.sleep(1)
    return old_orders


def get_full_orders_batch(acc: Account, order_ids: list[str],
                          on_batch: Callable[[int, int], None] | None = None) -> dict[str, Order]:
    result: dict[str, Order] = {}
    for i, offset in enumerate(range(0, len(order_ids), 10)):
        batch = order_ids[offset:offset + 10]
        logger.debug(f"{LOGGER_PREFIX} Получаю пачку заказов {batch}")
        for attempt in range(1, 6):
            try:
                time.sleep(attempt)
                result.update(acc.get_orders_by_ids(*batch))
                break
            except Exception:
                logger.warning(f"{LOGGER_PREFIX} Не удалось получить пачку заказов {batch}, попытка {attempt}")
                logger.debug("TRACEBACK", exc_info=True)
        else:
            logger.error(f"{LOGGER_PREFIX} Не удалось получить пачку заказов {batch} после всех попыток")
        if on_batch and i % 5 == 0:
            on_batch(min(offset + 10, len(order_ids)), len(order_ids))
    return result


def get_chat(acc: Account, chat_id: str | int, buyer_username: str, last_message_id: int | None) -> list[Message]:
    logger.debug(f"{LOGGER_PREFIX} Получаю историю чата {chat_id}")
    for attempt in range(1, 6):
        try:
            time.sleep(attempt)
            return acc.get_chat_history(chat_id, last_message_id, buyer_username)
        except Exception:
            logger.warning(f"{LOGGER_PREFIX} Не удалось получить историю чата {chat_id}, попытка {attempt}")
            logger.debug("TRACEBACK", exc_info=True)
    raise RuntimeError(f"Не удалось получить историю чата {chat_id}")


def get_chats(acc: Account, chats_data: dict[str, str]) -> dict[str, list[Message]]:
    logger.debug(f"{LOGGER_PREFIX} Получаю историю чатов {list(chats_data)}")
    for attempt in range(1, 6):
        try:
            time.sleep(attempt)
            return acc.get_chats_histories(chats_data)
        except Exception:
            logger.warning(f"{LOGGER_PREFIX} Не удалось получить историю чатов, попытка {attempt}")
            logger.debug("TRACEBACK", exc_info=True)
    raise RuntimeError(f"Не удалось получить историю чатов {list(chats_data)}")


def locate_order_window(acc: Account, chat_msgs: dict[str | int, list[Message]],
                        order: OrderShortcut) -> tuple[list[Message], int | None, int | None]:
    chat_id = order.chat_id
    for _page in range(MAX_HISTORY_PAGES):
        msgs = chat_msgs.get(chat_id, [])
        start_id = end_id = None
        for i, msg in enumerate(msgs):
            if start_id is None:
                if msg.author_id == 0 and msg.type == MessageTypes.ORDER_PURCHASED \
                        and msg.text and order.id in msg.text:
                    start_id = i
            elif end_id is None and msg.author_id == 0 and msg.type == MessageTypes.ORDER_PURCHASED:
                end_id = i
                break
        if start_id is not None:
            return msgs, start_id, end_id
        if not msgs:
            return msgs, None, None

        older = get_chat(acc, chat_id, order.buyer_username, msgs[0].id)
        if not older or older[-1].id == msgs[0].id:
            break
        chat_msgs[chat_id] = older + msgs

    logger.warning(f"{LOGGER_PREFIX} Не нашёл сообщение о покупке заказа #{order.id} в истории чата {chat_id}")
    return chat_msgs.get(chat_id, []), None, None


class OldOrdersPlugin:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, cardinal: Cardinal):
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        self.cardinal = cardinal
        self.tg = cardinal.telegram
        self.tgbot = self.tg.bot if self.tg else None

        self.success_patterns: list[dict] = []
        self.pending_patterns: dict[tuple[int, int], str] = {}
        self.review_sessions: dict[int, dict] = {}
        self.review_lock = threading.Lock()

    def load_settings(self):
        path = os.path.join(PLUGIN_FOLDER, "settings.json")
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())
        if "success_patterns" in data:
            self.success_patterns = data["success_patterns"]
        elif data.get("success_pattern"):
            self.success_patterns = [{
                "pattern": data["success_pattern"],
                "is_regex": data.get("success_pattern_is_regex", False),
            }]

    def save_settings(self):
        os.makedirs(PLUGIN_FOLDER, exist_ok=True)
        data = {"success_patterns": self.success_patterns}
        with open(os.path.join(PLUGIN_FOLDER, "settings.json"), "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))

    def matches_success_pattern(self, text: str | None) -> bool:
        if not text:
            return False
        for entry in self.success_patterns:
            pattern = entry.get("pattern")
            if not pattern:
                continue
            if entry.get("is_regex"):
                try:
                    if re.search(pattern, text):
                        return True
                except re.error as e:
                    logger.error(f"{LOGGER_PREFIX} Некорректная регулярка \"{pattern}\" в настройках плагина: {e}")
                continue
            if pattern in text:
                return True
        return False

    def settings_kb(self, offset: int) -> K:
        kb = K()
        for i, entry in enumerate(self.success_patterns):
            label = entry.get("pattern", "")
            if len(label) > 25:
                label = label[:25] + "…"
            type_mark = "regex" if entry.get("is_regex") else "подстрока"
            kb.add(B(f"🗑 [{type_mark}] {label}", callback_data=f"{CBT_DEL_PATTERN}:{offset}:{i}"))
        kb.add(B("➕ Добавить паттерн успешной сдачи", callback_data=f"{CBT_ASK_PATTERN}:{offset}"))
        kb.add(B(_("gl_back"), callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:{offset}"))
        return kb

    def open_settings_menu(self, c: telebot.types.CallbackQuery):
        offset = int(c.data.split(":")[-1])
        text = (
            "<b>⚙️ List Old Orders</b>\n\n"
            "Паттерны (подстроки или регулярки) ищутся среди ВАШИХ сообщений в рамках заказа - "
            "среди последних подряд идущих (если после них покупатель что-то написал, совпадение "
            "не считается). Если совпал хотя бы один - заказ считается точно выполненным "
            "(покупатель просто забыл нажать «Подтвердить выполнение заказа»).\n\n"
            "Пока список пуст, такие заказы будут уходить в ручной разбор по команде /old_orders.\n\n"
            "Нажми на паттерн в списке ниже, чтобы удалить его."
        )
        self.tgbot.edit_message_text(text, c.message.chat.id, c.message.id, reply_markup=self.settings_kb(offset))

    def act_ask_pattern(self, c: telebot.types.CallbackQuery):
        offset = int(c.data.split(":")[-1])
        result = self.tgbot.send_message(
            c.message.chat.id,
            "Отправь текст или регулярное выражение сообщения об успешной сдаче заказа.\n\n"
            "Например, подстрока: <code>Заказ передан</code>\n"
            "Или регулярка: <code>передан|отправлен</code>\n\n"
            "После отправки я спрошу, что именно это - подстрока или регулярка.",
            reply_markup=skb.CLEAR_STATE_BTN()
        )
        self.tg.set_state(c.message.chat.id, result.id, c.from_user.id, CBT_ASK_PATTERN, {"offset": offset})
        self.tgbot.answer_callback_query(c.id)

    def on_ask_pattern_message(self, m: telebot.types.Message):
        state = self.tg.get_state(m.chat.id, m.from_user.id)["data"]
        offset = state["offset"]
        self.tg.clear_state(m.chat.id, m.from_user.id, True)

        pattern_text = m.text.strip()
        if not pattern_text:
            self.tgbot.reply_to(m, "⚠️ Пустой паттерн, ничего не сохранено.")
            return

        self.pending_patterns[(m.chat.id, m.from_user.id)] = pattern_text
        kb = K().row(
            B("🔤 Подстрока", callback_data=f"{CBT_PATTERN_TYPE}:{offset}:0"),
            B(".* Regex", callback_data=f"{CBT_PATTERN_TYPE}:{offset}:1"),
        )
        self.tgbot.reply_to(
            m,
            f"Паттерн: <code>{tg_utils.escape(pattern_text)}</code>\n\nЭто подстрока или регулярное выражение?",
            reply_markup=kb
        )

    def on_pattern_type_chosen(self, c: telebot.types.CallbackQuery):
        _prefix, offset, is_regex_flag = c.data.split(":")
        offset, is_regex = int(offset), bool(int(is_regex_flag))
        key = (c.message.chat.id, c.from_user.id)
        pattern_text = self.pending_patterns.pop(key, None)
        if pattern_text is None:
            self.tgbot.answer_callback_query(c.id, "Паттерн не найден, попробуй добавить заново.", show_alert=True)
            return

        if is_regex:
            try:
                re.compile(pattern_text)
            except re.error as e:
                self.tgbot.answer_callback_query(c.id, f"Некорректная регулярка: {e}", show_alert=True)
                return

        self.success_patterns.append({"pattern": pattern_text, "is_regex": is_regex})
        self.save_settings()
        self.tgbot.answer_callback_query(c.id, "✅ Добавлено")
        back_cb = f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"
        type_label = "regex" if is_regex else "подстрока"
        self.tgbot.edit_message_text(
            f"✅ Паттерн добавлен ({type_label}): <code>{tg_utils.escape(pattern_text)}</code>",
            c.message.chat.id, c.message.id,
            reply_markup=K().add(B(_("gl_back"), callback_data=back_cb))
        )

    def del_pattern(self, c: telebot.types.CallbackQuery):
        _prefix, offset, index = c.data.split(":")
        offset, index = int(offset), int(index)
        if 0 <= index < len(self.success_patterns):
            self.success_patterns.pop(index)
            self.save_settings()
        c.data = f"{CBT.PLUGIN_SETTINGS}:{UUID}:{offset}"
        self.open_settings_menu(c)

    def classify_order(self, full_order: Order, full_history: list[Message], own_window: list[Message],
                       acc_id: int) -> Literal["first", "second", "third"]:
        for msg in full_history:
            if msg.type == MessageTypes.ORDER_REOPENED:
                return "second"
            if msg.is_employee and msg.author_id != SUPPORT_SYSTEM_AUTHOR_ID:
                return "second"

        for msg in reversed(own_window):
            if msg.author_id not in (acc_id, 0) and (not full_order.review or full_order.review.stars != 5):
                return "third"
            if msg.author_id == acc_id and self.matches_success_pattern(msg.text) \
                    and (not full_order.review or full_order.review.stars == 5):
                return "first"
        if own_window and full_order.order_secrets and (not full_order.review or full_order.review.stars == 5):
            return "first"
        return "third"

    def send_orders(self, m: telebot.types.Message):
        bot = self.tgbot
        acc = self.cardinal.account
        status_msg = bot.reply_to(m, "🔍 Этап 1/4: ищу просроченные заказы (это может занять какое-то время)...")

        def report(text: str):
            try:
                bot.edit_message_text(text, status_msg.chat.id, status_msg.id)
            except Exception:
                pass

        try:
            orders = get_all_old_orders(acc)
        except Exception:
            logger.error(f"{LOGGER_PREFIX} Не удалось получить список заказов")
            logger.debug("TRACEBACK", exc_info=True)
            bot.edit_message_text("❌ Не удалось получить список заказов.", status_msg.chat.id, status_msg.id)
            return

        if not orders:
            bot.edit_message_text("✅ Просроченных заказов нет.", status_msg.chat.id, status_msg.id)
            return

        chat_buyers: dict[str | int, str] = {}
        for order in orders:
            chat_buyers.setdefault(order.chat_id, order.buyer_username)

        chat_msgs: dict[str | int, list[Message]] = {}
        chat_ids = list(chat_buyers)
        report(f"💬 Этап 2/4: получаю историю чатов (0/{len(chat_ids)})...")
        for i, offset in enumerate(range(0, len(chat_ids), 10)):
            batch = {cid: chat_buyers[cid] for cid in chat_ids[offset:offset + 10]}
            try:
                chat_msgs.update(get_chats(acc, batch))
            except Exception:
                logger.error(f"{LOGGER_PREFIX} Не удалось получить историю части чатов")
                logger.debug("TRACEBACK", exc_info=True)
            if i % 5 == 0:
                report(f"💬 Этап 2/4: получаю историю чатов ({min(offset + 10, len(chat_ids))}/{len(chat_ids)})...")

        report(f"🧾 Этап 3/4: получаю данные заказов (0/{len(orders)})...")
        full_orders = get_full_orders_batch(
            acc, [order.id for order in orders],
            on_batch=lambda done, total: report(f"🧾 Этап 3/4: получаю данные заказов ({done}/{total})..."))

        first: list[str] = []
        second: list[str] = []
        third_context: dict[str, tuple[OrderShortcut, list[Message]]] = {}
        prev_time = None
        for j, order in enumerate(orders):
            if not prev_time or time.time() - prev_time > 10:
                prev_time = time.time()
                report(f"🧮 Этап 4/4: классифицирую заказы ({j + 1}/{len(orders)})...")

            own_window: list[Message] = chat_msgs.get(order.chat_id, [])
            try:
                full_order = full_orders.get(order.id)
                if full_order is None:
                    raise RuntimeError(f"Заказ #{order.id} отсутствует в пакетном ответе")
                msgs, start_id, end_id = locate_order_window(acc, chat_msgs, order)
                full_history = msgs[start_id:] if start_id is not None else []
                own_window = msgs[start_id:end_id] if start_id is not None else []
                bucket = self.classify_order(full_order, full_history, own_window, acc.id)
            except Exception:
                logger.error(f"{LOGGER_PREFIX} Ошибка при обработке заказа #{order.id}")
                logger.debug("TRACEBACK", exc_info=True)
                bucket = "third"

            if bucket == "first":
                first.append(order.id)
            elif bucket == "second":
                second.append(order.id)
            else:
                third_context[order.id] = (order, own_window)

        third = list(third_context)
        logger.debug(f"{LOGGER_PREFIX} 1) {', '.join(first)}")
        logger.debug(f"{LOGGER_PREFIX} 2) {', '.join(second)}")
        logger.debug(f"{LOGGER_PREFIX} 3) {', '.join(third)}")

        bot.edit_message_text(
            f"Готово: всего {len(orders)}, точно выполнено {len(first)}, есть проблема {len(second)}, "
            f"нужно разобрать вручную {len(third)}.",
            status_msg.chat.id, status_msg.id
        )

        if third:
            self.start_review(m.chat.id, first, second, third_context, third)
        else:
            self.send_final_lists(m.chat.id, first, second)

    def start_review(self, tg_chat_id: int, first: list[str], second: list[str],
                     context: dict[str, tuple[OrderShortcut, list[Message]]], queue: list[str]):
        with self.review_lock:
            if tg_chat_id in self.review_sessions:
                self.tgbot.send_message(tg_chat_id, "ℹ️ Предыдущий незавершённый разбор отменён.")
            self.review_sessions[tg_chat_id] = {
                "token": f"{int(time.time() * 1000) % 1000000:06d}",
                "first": first,
                "second": second,
                "context": context,
                "queue": queue,
                "current": None,
                "history": [],
            }
            self.tgbot.send_message(tg_chat_id,
                                    f"🕵️ Осталось разобрать вручную: {len(queue)}. Показываю диалоги по очереди.")
            self.advance_review(tg_chat_id)

    def advance_review(self, tg_chat_id: int):
        session = self.review_sessions.get(tg_chat_id)
        if not session:
            return
        if not session["queue"]:
            self.finish_review(tg_chat_id)
            return
        order_id = session["queue"].pop(0)
        session["current"] = order_id
        order, history = session["context"][order_id]
        self.send_review_card(tg_chat_id, session["token"], order, history, can_go_back=bool(session["history"]))

    def send_review_card(self, tg_chat_id: int, token: str, order: OrderShortcut, history: list[Message],
                         can_go_back: bool = False):
        header = (
            f"🧾 Заказ #{order.id}\n"
            f"Покупатель: {tg_utils.escape(order.buyer_username)}\n"
            f"Товар: {tg_utils.escape(order.description)}\n"
            f"Сумма: {order.price} {order.currency.name}\n"
            f"Дата: {order.date.strftime('%d.%m.%Y %H:%M')}\n"
            f"https://funpay.com/orders/{order.id}/\n"
            f"— — —\n"
        )
        lines = self.format_dialogue_lines(history)

        cb = f"{CBT_REVIEW}:{token}"
        kb = K()
        kb.row(
            B("✅ Список 1 (выполнен)", callback_data=f"{cb}:first:{order.id}"),
            B("⚠️ Список 2 (проблема)", callback_data=f"{cb}:second:{order.id}"),
        )
        kb.add(B("⏭ Пропустить (никуда не относить)", callback_data=f"{cb}:skip:{order.id}"))
        if can_go_back:
            kb.add(B("⬅️ Назад (отменить прошлый ответ)", callback_data=f"{cb}:back:{order.id}"))

        try:
            self.send_dialogue(tg_chat_id, header, lines, reply_markup=kb)
        except Exception:
            logger.error(f"{LOGGER_PREFIX} Не удалось отправить карточку заказа #{order.id}")
            logger.debug("TRACEBACK", exc_info=True)
            self.tgbot.send_message(tg_chat_id, header + "<i>⚠️ Не удалось показать диалог, открой заказ по ссылке.</i>",
                                    reply_markup=kb)

    def format_dialogue_lines(self, history: list[Message]) -> list[str]:
        lines = []
        last: dict = {}
        for msg in history:
            line = tg_utils.format_message_line(self.cardinal, msg, last)
            if not line:
                continue
            lines.append(line)
            last = {"author_id": msg.author_id, "by_bot": msg.by_bot, "badge": msg.badge, "by_vertex": msg.by_vertex}
        return lines

    def on_review_decision(self, c: telebot.types.CallbackQuery):
        with self.review_lock:
            self._on_review_decision(c)

    def _on_review_decision(self, c: telebot.types.CallbackQuery):
        _prefix, token, action, order_id = c.data.split(":", 3)
        tg_chat_id = c.message.chat.id
        session = self.review_sessions.get(tg_chat_id)
        if not session or session["token"] != token or session["current"] != order_id:
            self.tgbot.answer_callback_query(c.id, "Эта карточка уже неактуальна.")
            try:
                self.tgbot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=None)
            except Exception:
                pass
            return

        if action == "back":
            if not session["history"]:
                self.tgbot.answer_callback_query(c.id, "Это первый заказ разбора, назад некуда.", show_alert=True)
                return
            prev_order_id, prev_action = session["history"].pop()
            if prev_action == "first":
                session["first"].remove(prev_order_id)
            elif prev_action == "second":
                session["second"].remove(prev_order_id)
            session["queue"].insert(0, order_id)
            session["queue"].insert(0, prev_order_id)
        else:
            session["history"].append((order_id, action))
            if action == "first":
                session["first"].append(order_id)
            elif action == "second":
                session["second"].append(order_id)

        self.tgbot.answer_callback_query(c.id)
        try:
            self.tgbot.edit_message_reply_markup(c.message.chat.id, c.message.id, reply_markup=None)
        except Exception:
            pass
        self.advance_review(tg_chat_id)

    def finish_review(self, tg_chat_id: int):
        session = self.review_sessions.pop(tg_chat_id, None)
        if not session:
            return
        self.tgbot.send_message(tg_chat_id, "✅ Разбор завершён.")
        self.send_final_lists(tg_chat_id, session["first"], session["second"])

    def send_chunked(self, tg_chat_id: int, text: str, reply_markup=None):
        bot = self.tgbot
        while len(text) > TG_MESSAGE_LIMIT:
            cut = text.rfind(",", 0, TG_MESSAGE_LIMIT)
            if cut <= 0:
                cut = TG_MESSAGE_LIMIT
            bot.send_message(tg_chat_id, text[:cut])
            text = text[cut:].lstrip(",")
        bot.send_message(tg_chat_id, text, reply_markup=reply_markup)

    def send_dialogue(self, tg_chat_id: int, header: str, lines: list[str], reply_markup=None):
        bot = self.tgbot
        if not lines:
            bot.send_message(tg_chat_id, header + "<i>Историю чата с момента покупки найти не удалось.</i>",
                             reply_markup=reply_markup)
            return

        chunks: list[tuple[str, bool]] = []
        current = header
        current_has_lines = False

        def flush():
            nonlocal current, current_has_lines
            chunks.append((current, True))
            current, current_has_lines = header, False

        for line in lines:
            if len(header) + len(line) > TG_MESSAGE_LIMIT:
                if current_has_lines:
                    flush()
                plain = unescape(re.sub(r"<[^>]+>", "", line))
                chunks.append((plain[:TG_MESSAGE_LIMIT], False))
                continue
            piece = line if not current_has_lines else "\n\n" + line
            if current_has_lines and len(current) + len(piece) > TG_MESSAGE_LIMIT:
                flush()
                piece = line
            current += piece
            current_has_lines = True
        if current_has_lines:
            flush()

        for i, (text, is_html) in enumerate(chunks):
            kwargs = {"reply_markup": reply_markup} if i == len(chunks) - 1 else {}
            if not is_html:
                kwargs["parse_mode"] = None
            bot.send_message(tg_chat_id, text, **kwargs)

    def send_final_lists(self, tg_chat_id: int, first: list[str], second: list[str]):
        bot = self.tgbot
        if first:
            text = "1) " + ", ".join(f"#{order_id}" for order_id in first)
            self.send_chunked(tg_chat_id, text)
        else:
            bot.send_message(tg_chat_id, "✅ Список «покупатель забыл подтвердить» пуст.")

        if second:
            text = "2) " + ", ".join(f"#{order_id}" for order_id in second)
            self.send_chunked(tg_chat_id, text)
        else:
            bot.send_message(tg_chat_id, "⚠️ Список «проблема» пуст.")

    def reg_tg_handlers(self):
        self.tg.cbq_handler(self.open_settings_menu, lambda c: c.data.startswith(f"{CBT.PLUGIN_SETTINGS}:{UUID}:"))
        self.tg.cbq_handler(self.act_ask_pattern, lambda c: c.data.startswith(f"{CBT_ASK_PATTERN}:"))
        self.tg.msg_handler(self.on_ask_pattern_message,
                            func=lambda m: self.tg.check_state(m.chat.id, m.from_user.id, CBT_ASK_PATTERN))
        self.tg.cbq_handler(self.on_pattern_type_chosen, lambda c: c.data.startswith(f"{CBT_PATTERN_TYPE}:"))
        self.tg.cbq_handler(self.del_pattern, lambda c: c.data.startswith(f"{CBT_DEL_PATTERN}:"))
        self.tg.cbq_handler(self.on_review_decision, lambda c: c.data.startswith(f"{CBT_REVIEW}:"))
        self.tg.msg_handler(self.send_orders, commands=["old_orders"])


def pre_init(c: Cardinal):
    if not c.telegram:
        return
    plugin = OldOrdersPlugin(c)
    plugin.load_settings()
    plugin.reg_tg_handlers()
    c.add_telegram_commands(UUID, [
        ("old_orders", "заказы для подтверждения через тп", True)
    ])


BIND_TO_PRE_INIT = [pre_init]
