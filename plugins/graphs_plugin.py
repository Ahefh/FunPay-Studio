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
from pip._internal.cli.main import main

try:
    import matplotlib
except ImportError:
    main(["install", "-U", "matplotlib==3.8.2"])
    import matplotlib
try:
    import pandas as pd
except ImportError:
    main(["install", "-U", "pandas==2.2.0"])
    import pandas as pd
try:
    import mplcyberpunk
except ImportError:
    main(["install", "-U", "mplcyberpunk==0.7.1"])
    import mplcyberpunk
from datetime import datetime
from typing import TYPE_CHECKING
import io
import numpy as np
from telebot.types import InputMediaPhoto

from tg_bot import CBT

if TYPE_CHECKING:
    from cardinal import Cardinal
from FunPayAPI.updater.events import *
from os.path import exists
import tg_bot.CBT
import telebot
import time
from logging import getLogger

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from telebot.types import InlineKeyboardMarkup as K, InlineKeyboardButton as B

NAME = "Graphs Plugin"
VERSION = "0.0.6"
DESCRIPTION = "Данный плагин рисует графики со статистикой аккаунта."
CREDITS = "yuepi-FPS"
CRD_LINK = "github.com/sidor0912/FunPayStudio"
UUID = "ca9c7e14-706e-4563-9a41-e326a21d8472"
SETTINGS_PAGE = True
SETTINGS = {
    "head": 10,
    "min4line": 13,
    "graph1": True,
    "graph2": True,
    "graph3": True,
    "graph4": True,
    "graph5": True,
    "graph6": True,
    "graph7": True,
    "graph8": True,
    "graph9": True,
    "graph10": True,

}
LOGGER_PREFIX = "[GRAPHS_PLUGIN]"
logger = getLogger("FPS.graphs_plugin")
in_progress = False
CBT_TEXT_CHANGE_COUNT = "graphs_ChangeCount"
CBT_TEXT_EDITED = "graphs_Edited"
CBT_TEXT_SWITCH = "graphs_Switch"


def init_commands(cardinal: Cardinal, *args):
    if not cardinal.telegram:
        return
    tg = cardinal.telegram
    bot = tg.bot
    acc = cardinal.account

    if exists("storage/plugins/graphs_settings.json"):
        with open("storage/plugins/graphs_settings.json", "r", encoding="utf-8") as f:
            global SETTINGS
            settings = json.loads(f.read())
            SETTINGS.update(settings)

    def switch(call: telebot.types.CallbackQuery):
        key = call.data.split(":")[-1]
        SETTINGS[key] = not SETTINGS[key]
        save_config()
        open_settings(call)

    def open_settings(call: telebot.types.CallbackQuery):
        keyboard = K()
        keyboard.add(B(f"Head: {SETTINGS['head']}", callback_data=f"{CBT_TEXT_CHANGE_COUNT}:head"))
        keyboard.add(B(f"Min4Line: {SETTINGS['min4line']}", callback_data=f"{CBT_TEXT_CHANGE_COUNT}:min4line"))
        keyboard.row_width = 2
        for i in range(1, 10, 2):
            keyboard.row(
                B(f"{i} : {'🟢 вкл.' if SETTINGS['graph' + str(i)] else '🔴 выкл.'}",
                  callback_data=f"{CBT_TEXT_SWITCH}:graph{i}"),
                B(f"{i + 1} : {'🟢 вкл.' if SETTINGS['graph' + str(i + 1)] else '🔴 выкл.'}",
                  callback_data=f"{CBT_TEXT_SWITCH}:graph{i + 1}")
            )
        keyboard.add(B("◀️ Назад", callback_data=f"{CBT.EDIT_PLUGIN}:{UUID}:0"))

        bot.edit_message_text("Настройки плагина графиков.\n\n"
                              "<b>Head:</b> Для столбчатых диаграмм отображать первые <u>X</u> значений.\n\n"
                              "<b>Min4Line:</b> Рисовать линейный график, если количество столбцов не менее <u>X</u>.\n"
                              "Номера графиков можно посмотреть в конце подписи к каждому изображению при использовании /graphs",
                              call.message.chat.id, call.message.id,
                              reply_markup=keyboard)
        bot.answer_callback_query(call.id)

    def edit(call: telebot.types.CallbackQuery):
        result = bot.send_message(call.message.chat.id,
                                  f"<b>Текущее значение: </b>{SETTINGS[call.data.split(':')[-1]]}\n\n"
                                  f"Введите новое значение:",
                                  reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN())
        tg.set_state(call.message.chat.id, result.id, call.from_user.id,
                     f"{CBT_TEXT_EDITED}:{call.data.split(':')[-1]}", {"k": call.data.split(':')[-1]})
        bot.answer_callback_query(call.id)

    def save_config():
        with open("storage/plugins/graphs_settings.json", "w", encoding="utf-8") as f:
            global SETTINGS
            f.write(json.dumps(SETTINGS, indent=4, ensure_ascii=False))

    def edited(message: telebot.types.Message):
        text = message.text
        key = tg.user_states[message.chat.id][message.from_user.id]["data"]["k"]
        try:
            count = int(text)
        except:
            bot.reply_to(message, f"Неправильный формат. Попробуйте снова.",
                         reply_markup=tg_bot.static_keyboards.CLEAR_STATE_BTN())
            return
        tg.clear_state(message.chat.id, message.from_user.id, True)
        keyboard = K() \
            .row(B("◀️ Назад", callback_data=f"{CBT.PLUGIN_SETTINGS}:{UUID}"))
        SETTINGS[key] = count
        save_config()
        bot.reply_to(message, f"✅ Успех: {count}", reply_markup=keyboard)

    def orders_generator(days: list(float), new_mes: telebot.types.Message):
        now = datetime.now()
        days.sort()
        max_seconds = days[-1] * 3600 * 24
        next_order_id, all_sales, locale, subcs = acc.get_sales()
        c = 1
        while next_order_id != None and (now - all_sales[-1].date).total_seconds() < max_seconds:
            time.sleep(1)
            for i in range(2, -1, -1):
                try:
                    next_order_id, new_sales, locale, subcs = acc.get_sales(start_from=next_order_id,
                                                                            sudcategories=subcs,
                                                                            locale=locale)
                    break
                except:
                    logger.warning(f"{LOGGER_PREFIX} Не удалось получить заказы. Осталось попыток: {i}")
                    logger.debug("TRACEBACK", exc_info=True)
                    time.sleep(2)
            else:
                raise Exception("Не удалось спарсить")
            all_sales += new_sales
            str4tg = f"Обновляю статистику аккаунта. Запрос N{c}. Последний заказ: <a href='https://funpay.com/orders/{next_order_id}/'>{next_order_id}</a>"
            logger.debug(f"{LOGGER_PREFIX} {str4tg}")
            if c % 5 == 0:
                try:
                    msg = bot.edit_message_text(str4tg, new_mes.chat.id, new_mes.id)
                    logger.debug(f"{LOGGER_PREFIX} Сообщение изменено. {msg}")
                except:
                    logger.warning(f"{LOGGER_PREFIX} Не получилось изменить сообщение.")
                    logger.debug("TRACEBACK", exc_info=True)
            while (days and (now - all_sales[-1].date).total_seconds() > days[0] * 3600 * 24):
                temp_list = [sale for sale in all_sales if (now - sale.date).total_seconds() < days[0] * 3600 * 24]
                bot.edit_message_text(f"Закончил сканировать заказы за последние {days[0]} дн..", new_mes.chat.id,
                                      new_mes.id)
                yield days[0], temp_list
                del days[0]
            c += 1
        all_sales = [sale for sale in all_sales if (now - sale.date).total_seconds() < max_seconds]
        if all_sales and days:
            yield days[0], all_sales

    def get_color(status: OrderStatuses):
        try:
            return ("blue", "green", "orange")[status]
        except:
            return "black"

    def get_text(status: OrderStatuses):
        try:
            return ("Оплачен", "Закрыт", "Возврат")[status]
        except:
            return "Какой-то статус"

    def my_cyberpunk(ax, bars=None):
        # mplcyberpunk.make_lines_glow(ax)
        # mplcyberpunk.add_underglow(ax)
        mplcyberpunk.add_gradient_fill(ax=ax)
        # mplcyberpunk.add_glow_effects(ax, gradient_fill=True)
        # mplcyberpunk.add_gradient_fill(ax)
        try:
            mplcyberpunk.make_scatter_glow(ax)
        except:
            pass
        if bars is not None:
            mplcyberpunk.add_bar_gradient(bars.patches, ax=ax, horizontal=True)

    def df_update_dates(df):
        df['date'] = pd.to_datetime(df['date']).dt.floor('D')  # Округляем до дня

        # Создаем все комбинации дат и статусов
        all_dates = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
        all_statuses = df['status'].unique()
        all_combinations = pd.MultiIndex.from_product([all_dates, all_statuses], names=['date', 'status'])

        # Создаем полный датафрейм с уникальными комбинациями
        full_df = pd.DataFrame(index=all_combinations).reset_index()

        # Объединяем с исходным датафреймом
        result_df = pd.merge(full_df, df, how='left', on=['date', 'status']).fillna(0)
        # Ваш дополненный датафрейм

        df = result_df
        df['date'] = pd.to_datetime(df['date'])

        # Добавляем столбец с годом, месяцем и днем
        df['year'] = df['date'].dt.to_period('Y')
        df['month'] = df['date'].dt.to_period('M')
        df['day'] = df['date'].dt.to_period('d')
        return df

    def draw_price_time(orders_list, currency, min4line: int):
        with plt.style.context('cyberpunk'):
            # Преобразуем список заказов в DataFrame
            data = {
                'date': [order.date for order in orders_list if str(order.currency) == currency],
                'price': [order.price for order in orders_list if str(order.currency) == currency],
                'status': [order.status.value for order in orders_list if str(order.currency) == currency]
            }
            df = pd.DataFrame(data)
            df = df_update_dates(df)

            # Проверяем, все ли данные относятся к одному году или месяцу
            unique_years = df['year'].nunique() > 1
            unique_months = df['month'].nunique() > 1

            # Группируем данные по году, месяцу и дню
            orders_by_year = df.groupby(['year', 'status']).price.sum().unstack(fill_value=0)
            orders_by_month = df.groupby(['month', 'status']).price.sum().unstack(fill_value=0)
            orders_by_day = df.groupby(['day', 'status']).price.sum().unstack(fill_value=0)

            rows = int(unique_years) + int(unique_months) + 1
            # Строим графики
            fig, axs = plt.subplots(rows, 1, figsize=(10, 5 * rows))
            if type(axs) != np.ndarray:
                axs = [axs]
            ord_data = [orders_by_day]
            if unique_months:
                ord_data.append(orders_by_month)
            if unique_years:
                ord_data.append(orders_by_year)

            # Добавляем аннотации и корректные подписи столбцов с цветами
            for ax, orders_data, x_title in zip(axs, ord_data, ['День', "Месяц", "Год"]):
                bars = None
                if len(orders_data) < min4line:
                    colors = {0: 'blue', 1: 'green', 2: 'orange'}
                    labels = {0: 'Оплачен', 1: 'Закрыт', 2: 'Возврат'}
                    # Строим столбчатую диаграмму, если столбцов не более 10
                    bars = orders_data[::-1].plot(kind='barh', stacked=False, ax=ax,
                                                  color=[colors[col] for col in orders_data.columns])

                    # Добавляем подписи над столбцами с суммой
                    for rect in bars.patches:
                        width = rect.get_width()
                        ax.annotate((int(width) if int(width) == width else width.round(2)) if width else "",
                                    xy=(width, rect.get_y() + rect.get_height() / 2),
                                    xytext=(3, 0),  # 3 points horizontal offset
                                    textcoords="offset points",
                                    ha='left', va='center')

                    ax.legend([labels[lb] for lb in orders_data.columns])
                else:
                    # Строим линейный график, если столбцов более 10
                    for status in orders_data.columns:
                        orders_data[status].plot(ax=ax, label=get_text(status), color=get_color(status), marker=".")

                    # Добавляем сетку на линейный график
                    ax.grid(True)

                    ax.legend()
                my_cyberpunk(ax, bars)
                ax.set_title(f'Сумма заказов ({currency}) / {x_title}')
                ax.set_xlabel("")
                ax.set_ylabel(f'')

            plt.tight_layout()
            fig.text(0.01, 0.99, f'FPS {NAME} v{VERSION} by @sidor0912\n{CRD_LINK}', ha='left', va='top',
                     fontsize=10, color='gray', alpha=0.5)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            plt.close(fig)

            return buf

    def draw_k_sales_time(orders_list, min4line: int):
        with plt.style.context('cyberpunk'):
            # Преобразуем список заказов в DataFrame
            data = {
                'date': [order.date for order in orders_list],
                'status': [order.status.value for order in orders_list],
                "add_to_k": [1 for _ in orders_list]
            }
            df = pd.DataFrame(data)
            df = df_update_dates(df)
            # Проверяем, все ли данные относятся к одному году или месяцу
            unique_years = df['year'].nunique() > 1
            unique_months = df['month'].nunique() > 1

            # Группируем данные по году, месяцу и дню
            orders_by_year = df.groupby(['year', 'status']).add_to_k.sum().unstack(fill_value=0)
            orders_by_month = df.groupby(['month', 'status']).add_to_k.sum().unstack(fill_value=0)
            orders_by_day = df.groupby(['day', 'status']).add_to_k.sum().unstack(fill_value=0)

            rows = int(unique_years) + int(unique_months) + 1

            # Строим графики
            fig, axs = plt.subplots(rows, 1, figsize=(10, 5 * rows))
            if type(axs) != np.ndarray:
                axs = [axs]
            ord_data = [orders_by_day]
            if unique_months:
                ord_data.append(orders_by_month)
            if unique_years:
                ord_data.append(orders_by_year)

            # Добавляем аннотации и корректные подписи столбцов с цветами
            for ax, orders_data, x_title in zip(axs, ord_data, ['День', "Месяц", "Год"]):
                bars = None
                if len(orders_data) < min4line:
                    colors = {0: 'blue', 1: 'green', 2: 'orange'}
                    labels = {0: 'Оплачен', 1: 'Закрыт', 2: 'Возврат'}
                    # Строим столбчатую диаграмму, если столбцов не более 10
                    with plt.style.context('cyberpunk'):
                        bars = orders_data[::-1].plot(kind='barh', stacked=False, ax=ax,
                                                      color=[colors[col] for col in orders_data.columns])

                    # Добавляем подписи над столбцами с количеством
                    for rect in bars.patches:
                        width = rect.get_width()
                        ax.annotate((int(width) if int(width) == width else width.round(2)) if width else "",
                                    xy=(width, rect.get_y() + rect.get_height() / 2),
                                    xytext=(3, 0),  # 3 points horizontal offset
                                    textcoords="offset points",
                                    ha='left', va='center')
                    ax.legend([labels[lb] for lb in orders_data.columns])

                else:
                    # Строим линейный график, если столбцов более 10
                    for status in orders_data.columns:
                        orders_data[status].plot(ax=ax, label=get_text(status), color=get_color(status), marker=".")

                    # Добавляем сетку на линейный график
                    ax.grid(True)

                    ax.legend()

                ax.set_title(f'Количество заказов / {x_title}')
                ax.set_xlabel("")
                ax.set_ylabel('')
                my_cyberpunk(ax, bars)
            plt.tight_layout()
            fig.text(0.01, 0.99, f'FPS {NAME} v{VERSION} by @sidor0912\n{CRD_LINK}', ha='left', va='top',
                     fontsize=10, color='gray', alpha=0.5)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            plt.close(fig)

            return buf

    def draw_bar_charts(orders_list, parameter, head: int):
        with plt.style.context('cyberpunk'):
            # Создаем DataFrame из списка заказов
            data = {
                'subcategory_name': [order.subcategory_name for order in orders_list],
                'buyer_username': [order.buyer_username for order in orders_list],
                'game_name': [order.subcategory_name.split(",")[0] for order in orders_list],
                'status': [order.status.value for order in orders_list]
            }
            df = pd.DataFrame(data)

            # Выбираем параметр для группировки
            if parameter == 'subcategory_name':
                group_by_parameter = 'subcategory_name'
                title = 'Количество заказов по подкатегориям'
            elif parameter == 'buyer_username':
                group_by_parameter = 'buyer_username'
                title = 'Количество заказов по никнеймам покупателей'
            elif parameter == 'game_name':
                group_by_parameter = 'game_name'
                title = 'Количество заказов по названиям игр'
            else:
                raise ValueError(f"Неподдерживаемый параметр: {parameter}")

            # Группируем данные, считаем количество заказов и сортируем по убыванию
            orders_by_parameter = df.groupby([group_by_parameter, 'status']).size().unstack(fill_value=0)
            sorted_orders = orders_by_parameter.sum(axis=1).sort_values(ascending=False).index
            orders_by_parameter = orders_by_parameter.loc[sorted_orders]
            # orders_by_parameter = df.groupby([group_by_parameter]).size().sort_values(ascending=False)

            # Получаем только топ-X значений
            top_x_orders = orders_by_parameter.head(head)[::-1]

            # Строим столбчатую диаграмму
            fig, ax = plt.subplots(figsize=(10, 10))
            colors = {0: 'blue', 1: 'green', 2: 'orange'}
            labels = {0: 'Оплачен', 1: 'Закрыт', 2: 'Возврат'}
            bars = top_x_orders.plot(kind='barh', stacked=False, ax=ax,
                                     color=[colors[col] for col in top_x_orders.columns])

            # Добавляем подписи над столбцами с количеством
            for rect in bars.patches:
                width = rect.get_width()
                ax.annotate((int(width) if int(width) == width else width.round(2)) if width else "",
                            xy=(width, rect.get_y() + rect.get_height() / 2),
                            xytext=(3, 0),  # 3 points horizontal offset
                            textcoords="offset points",
                            ha='left', va='center')
            ax.legend([labels[lb] for lb in top_x_orders.columns], loc='lower right')

            ax.set_title(title)
            ax.set_xlabel("")
            ax.set_ylabel('')
            my_cyberpunk(ax, bars)
            plt.tight_layout()
            fig.text(0.01, 0.99, f'FPS {NAME} v{VERSION} by @sidor0912\n{CRD_LINK}', ha='left', va='top',
                     fontsize=10, color='gray', alpha=0.5)
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=300)
            buf.seek(0)
            plt.close(fig)

            return buf

    def draw_combined_charts(orders_list, parameter, head):
        with plt.style.context('cyberpunk'):
            currencies = ['₽', '$', '€']
            non_empty_plots = 0  # Счетчик непустых графиков

            # Создаем общий график
            set_curr = set([str(order.currency) for order in orders_list])
            len_curr = len(set_curr)
            fig, axes = plt.subplots(len_curr, 1, figsize=(10, 5 * (2 if len_curr == 1 else len_curr)))
            if type(axes) != np.ndarray:
                axes = [axes]
            for currency, ax in zip(sorted(list(set_curr)), axes):
                currency_orders = [order for order in orders_list if str(order.currency) == currency]
                # Создаем DataFrame из списка заказов
                data = {
                    'subcategory_name': [order.subcategory_name for order in currency_orders],
                    'buyer_username': [order.buyer_username for order in currency_orders],
                    'game_name': [order.subcategory_name.split(",")[0] for order in currency_orders],
                    'status': [order.status.value for order in currency_orders],
                    'price': [order.price for order in currency_orders]
                }
                df = pd.DataFrame(data)

                # Выбираем параметр для группировки
                if parameter == 'subcategory_name':
                    group_by_parameter = 'subcategory_name'
                    title = f'Сумма цен заказов по подкатегориям ({currency})'
                elif parameter == 'buyer_username':
                    group_by_parameter = 'buyer_username'
                    title = f'Сумма цен заказов по никнеймам покупателей ({currency})'
                elif parameter == 'game_name':
                    group_by_parameter = 'game_name'
                    title = f'Сумма цен заказов по названиям игр ({currency})'
                else:
                    raise ValueError(f"Неподдерживаемый параметр: {parameter}")

                # Группируем данные, считаем сумму цен заказов и сортируем по убыванию
                orders_by_parameter = df.groupby([group_by_parameter, 'status'])['price'].sum().unstack(fill_value=0)
                sorted_orders = orders_by_parameter.sum(axis=1).sort_values(ascending=False).index
                orders_by_parameter = orders_by_parameter.loc[sorted_orders]

                # Получаем только топ-X значений
                top_x_orders = orders_by_parameter.head(head)[::-1]

                # Строим столбчатую диаграмму
                colors = {0: 'blue', 1: 'green', 2: 'orange'}
                labels = {0: 'Оплачен', 1: 'Закрыт', 2: 'Возврат'}
                # Строим столбчатую диаграмму, если столбцов не более 10
                bars = top_x_orders.plot(kind='barh', stacked=False, ax=ax,
                                         color=[colors[col] for col in top_x_orders.columns])

                # Добавляем подписи над столбцами с суммой цен
                for rect in bars.patches:
                    width = rect.get_width()
                    ax.annotate(
                        f"{(int(width) if int(width) == width else width.round(2))} {currency}" if width else "",
                        xy=(width, rect.get_y() + rect.get_height() / 2),
                        xytext=(3, 0),  # 3 points horizontal offset
                        textcoords="offset points",
                        ha='left', va='center')
                ax.legend([labels[lb] for lb in top_x_orders.columns], loc='lower right')

                ax.set_title(title)
                ax.set_xlabel("")
                ax.set_ylabel('')
                my_cyberpunk(ax, bars)
                non_empty_plots += 1

            # Если есть непустые графики, то сохраняем изображение
            if non_empty_plots > 0:

                plt.tight_layout()
                fig.text(0.01, 0.99, f'FPS {NAME} v{VERSION} by @sidor0912\n{CRD_LINK}', ha='left', va='top',
                         fontsize=10, color='gray', alpha=0.5)
                buf = io.BytesIO()
                fig.savefig(buf, format='png', dpi=300)
                buf.seek(0)
                plt.close(fig)

                return buf
            else:
                plt.close()
                return None  # Возвращаем None, если нет непустых графиков

    def get_graphs(m: telebot.types.Message):
        global in_progress
        if in_progress:
            bot.reply_to(m, "Уже запущено. Дождитесь окончания или используйте /restart")
            return
        in_progress = True
        new_mes = bot.reply_to(m, "Сканирую заказы (это может занять какое-то время)...")
        days = list(map(float, m.text.split(" ")[1:]))
        if not days:
            bot.edit_message_text("❌ Неправильный формат сообщения.\n"
                                  "Правильный формат: \n<code>/graphs 7 30 365 9999</code>\n, где числа - количество последних дней",
                                  new_mes.chat.id, new_mes.id)
            in_progress = False
            return
        try:
            for days, orders in orders_generator(days=days, new_mes=new_mes):
                try:
                    global SETTINGS
                    min4line = SETTINGS["min4line"]
                    head = SETTINGS["head"]
                    caption = f"Статистика для <u><b>{acc.username} ({acc.id})</b></u> за последние <u><b>{int(days)}</b></u> дн.\n" \
                              f"Рисовать линейный график, если количество столбцов не менее <u><b>{min4line}</b></u>.\n" \
                              f"Для столбчатых диаграмм отображать первые <u><b>{head}</b></u> значений.\n\n" \
                              f"Сгенерировано с помощью {NAME} v{VERSION} by {CREDITS}"
                    photos = []
                    if SETTINGS[a := "graph1"]:
                        photos.append(InputMediaPhoto(draw_k_sales_time(orders, min4line), caption=f"{caption}\n\n{a}",
                                                      parse_mode="HTML"))
                    currencies = sorted(set([str(i.currency) for i in orders]))
                    list_curr = ["$", "€", "₽"]
                    for curr in currencies:
                        graph_num = list_curr.index(curr) + 2
                        if SETTINGS[a := f"graph{graph_num}"]:
                            photos.append(
                                InputMediaPhoto(draw_price_time(orders, curr, min4line), caption=f"{caption}\n\n{a}",
                                                parse_mode="HTML"))
                    if SETTINGS[a := "graph5"]:
                        photos.append(InputMediaPhoto(draw_bar_charts(orders, parameter="subcategory_name", head=head),
                                                      caption=f"{caption}\n\n{a}", parse_mode="HTML"))
                    if SETTINGS[a := "graph6"]:
                        photos.append(
                            InputMediaPhoto(draw_combined_charts(orders, parameter="subcategory_name", head=head),
                                            caption=f"{caption}\n\n{a}", parse_mode="HTML"))
                    if SETTINGS[a := "graph7"]:
                        photos.append(InputMediaPhoto(draw_bar_charts(orders, parameter="game_name", head=head),
                                                      caption=f"{caption}\n\n{a}", parse_mode="HTML"))
                    if SETTINGS[a := "graph8"]:
                        photos.append(
                            InputMediaPhoto(draw_combined_charts(orders, parameter="game_name", head=head),
                                            caption=f"{caption}\n\n{a}",
                                            parse_mode="HTML"))
                    if SETTINGS[a := "graph9"]:
                        photos.append(InputMediaPhoto(draw_bar_charts(orders, parameter="buyer_username", head=head),
                                                      has_spoiler=True, caption=f"{caption}\n\n{a}", parse_mode="HTML"))

                    if SETTINGS[a := "graph10"]:
                        photos.append(
                            InputMediaPhoto(draw_combined_charts(orders, parameter="buyer_username", head=head),
                                            has_spoiler=True, caption=f"{caption}\n\n{a}", parse_mode="HTML"))

                    bot.send_media_group(new_mes.chat.id, photos)
                    bot.send_message(new_mes.chat.id, f"⬆️ Изображения для {int(days)} дн. ⬆️")

                except:
                    in_progress = False
                    logger.error(f"{LOGGER_PREFIX} Возникла ошибка при генерации изображений.")
                    logger.debug("TRACEBACK", exc_info=True)
                    bot.edit_message_text("❌ Возникла ошибка при генерации изображений.", new_mes.chat.id, new_mes.id)
                    return
        except:
            in_progress = False
            logger.error(f"{LOGGER_PREFIX} ❌ Не удалось получить список заказов.")
            logger.debug("TRACEBACK", exc_info=True)
            bot.edit_message_text("❌ Не удалось получить список заказов.", new_mes.chat.id, new_mes.id)
            return
        in_progress = False
        bot.edit_message_text("😎 Производство графиков завершено.", new_mes.chat.id, new_mes.id)

    tg.msg_handler(get_graphs, commands=["graphs"])
    cardinal.add_telegram_commands(UUID, [
        ("graphs", "Строит графики", True)
    ])
    tg.cbq_handler(edit, lambda c: f"{CBT_TEXT_CHANGE_COUNT}" in c.data)
    tg.cbq_handler(open_settings, lambda c: f"{CBT.PLUGIN_SETTINGS}:{UUID}" in c.data)
    tg.msg_handler(edited, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, f"{CBT_TEXT_EDITED}:head"))
    tg.msg_handler(edited, func=lambda m: tg.check_state(m.chat.id, m.from_user.id, f"{CBT_TEXT_EDITED}:min4line"))
    tg.cbq_handler(switch, lambda c: f"{CBT_TEXT_SWITCH}" in c.data)


BIND_TO_PRE_INIT = [init_commands]
BIND_TO_DELETE = None
