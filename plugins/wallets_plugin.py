# ==============================================================================
# FunPay Studio (FPS) — Официальный плагин
# Создатель: yuepi-FPS
# Официальный канал: https://t.me/funpaystudio
# Каталог плагинов:   https://t.me/fps_plugins1
# Наш FunPay магазин: https://funpay.com/users/11535828/
# Версия под 2026 год
# ==============================================================================

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from locales.localizer import Localizer

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.updater.events import *
import telebot
import logging

NAME = "Wallets Plugin"
VERSION = "0.0.2"
DESCRIPTION = "Плагин для удаления из профиля неиспользуемых кошельков."

CREDITS = "yuepi-FPS"
UUID = "961a14c9-4f14-47f7-97a5-d9689e39003e"
SETTINGS_PAGE = False
logger = logging.getLogger("FPS.wallets_plugin")
LOGGER_PREFIX = "[WALLETS PLUGIN]"
localizer = Localizer()
_ = localizer.translate


class WalletsPlugin:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WalletsPlugin, cls).__new__(cls)
        return cls._instance

    def __init__(self, crd: Cardinal):
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        self.cardinal = crd
        self.tg = None
        self.tgbot = None
        if self.cardinal.telegram:
            self.tg = self.cardinal.telegram
            self.tgbot = self.tg.bot

    def wallet_priority(self, x, withdraws: dict[str, datetime], mb_del_wallets_data: set[str]):
        dt = withdraws.get(x.data, datetime.fromtimestamp(0))
        delta = (datetime.now() - dt).total_seconds()
        is_sbp = x.data.startswith("+")

        coef = 2 if is_sbp else 1

        # чем МЕНЬШЕ значение — тем быстрее удалится
        return (
            x.data not in mb_del_wallets_data,
            - delta / coef
        )

    def del_last_wallet(self, message: telebot.types.Message | None = None):
        deals_continue = None
        deals_dt = None
        to_parse_deals = True
        only_deals = False

        withdraw_continue = None
        withdraw_dt = None
        to_parse_withdraws = True
        only_withdraws = False

        all_wallets = self.cardinal.account.get_wallets()
        if len(all_wallets) < 50:
            if message:
                self.tgbot.send_message(message.chat.id, "✅ Место есть, удалять ничего не нужно.")
            return
        if message:
            msg = self.tgbot.send_message(message.chat.id, "⏳ Ищу бесполезный кошелёчек...")
        mb_del_wallets_data = {i.data for i in all_wallets[:-5]}
        withdraws = {}
        min_dt = None
        while to_parse_deals or to_parse_withdraws:
            deals = False
            if to_parse_deals and (deals_dt is None or (withdraw_dt is not None and deals_dt > withdraw_dt)): #и время ластового в сделках > ластового в выводах
                deals = True

            # если уже спарсили всё и нужно допарсить до нужной даты другой список
            if (only_deals and not deals) or (only_withdraws and deals):
                min_dt = min(list(withdraws.values()))
                break


            if deals:
                payload = {"userId": self.cardinal.account.id}
                payload["continue"] = deals_continue or ""
                headers = {
                    "accept": "*/*",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-requested-with": "XMLHttpRequest"
                }
                r = self.cardinal.account.method("post", "deal/payouts", headers, payload)
                logger.debug(r.content.decode())

                bs = BeautifulSoup(r.content.decode(), "lxml")
                body = bs.find("tbody")
                if not body:
                    to_parse_deals = False
                    continue
                rows = body.find_all("tr")
                for row in rows:
                    tds = row.find_all("td")
                    date: datetime = utils.parse_funpay_datetime(tds[0].find("div").text.strip())
                    phone = tds[2].find("div").text.strip()
                    if phone not in withdraws:
                        withdraws[phone] = date
                    else:
                        withdraws[phone] = max(withdraws[phone], date)
                    if deals_dt is None or deals_dt > date:
                        deals_dt = date

                input_tag = bs.find("input", {"name": "continue"})
                deals_continue = int(input_tag.get("value")) if input_tag else None
                logger.debug(f"{LOGGER_PREFIX} Некст сделки: {deals_continue}")
                if deals_continue in (None, 0):
                    to_parse_deals = False
            else:
                payload = {"user_id": self.cardinal.account.id, "filter": "withdraw"}
                if withdraw_continue:
                    payload["continue"] = withdraw_continue
                headers = {
                    "accept": "*/*",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "x-requested-with": "XMLHttpRequest"
                }
                r = self.cardinal.account.method("post", "users/transactions", headers, payload)
                bs = BeautifulSoup(r.content.decode(), "lxml")
                rows = bs.find_all("div", class_="tc-item")
                for row in rows:
                    date: datetime = utils.parse_funpay_datetime(row.find("span", class_ = "tc-date-time").text.strip())
                    pm_number = row.find("span", class_ = "tc-payment-number").text.strip()
                    if pm_number not in withdraws:
                        withdraws[pm_number] = date
                    else:
                        withdraws[pm_number] = max(withdraws[pm_number], date)
                    if withdraw_dt is None or withdraw_dt > date:
                        withdraw_dt = date

                input_tag = bs.find("input", {"name": "continue"})
                withdraw_continue = input_tag.get("value") if input_tag else None
                logger.debug(f"{LOGGER_PREFIX} Некст выводы: {withdraw_continue}")
                if withdraw_continue is None:
                    to_parse_withdraws = False

            # нашли вывод для каждого из кошельков
            if len(mb_del_wallets_data - set(withdraws.keys())) == 0:
                #парсили сделки
                if deals:
                    only_withdraws = True
                #парсили выводы
                else:
                    only_deals = True


        all_wallets = sorted(all_wallets, key=lambda x: self.wallet_priority(x, withdraws, mb_del_wallets_data))
        del_wallet = all_wallets.pop(0)
        self.cardinal.account.save_wallets(all_wallets)
        d = f"<code>{withdraws.get(del_wallet.data).strftime('%d.%m.%Y %H:%M')}</code>" if del_wallet.data in withdraws \
            else f"ранее, чем <code>{min_dt.strftime('%d.%m.%Y %H:%M') if min_dt else min_dt}</code>"
        d = f"\n\n<b>📅 Дата последнего вывода:</b> {d}"
        if message:
            self.tgbot.edit_message_text(f"✅ <b>Удален кошелёк:</b> <code>{del_wallet.data}</code>{d}", msg.chat.id, msg.message_id)


    def reg_tg_handlers(self):
        self.tg.msg_handler(self.del_last_wallet, commands = ["del_unused_wallet"])
        self.cardinal.add_telegram_commands(UUID, [
            (f"del_unused_wallet", "Удалить неиспользуемый кошелёк", True),
        ])

def pre_init(c: Cardinal):
    sp = WalletsPlugin(c)
    sp.reg_tg_handlers()

BIND_TO_PRE_INIT = [pre_init]
BIND_TO_DELETE = None
