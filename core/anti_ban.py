"""
FunPay Studio — Smart Anti-Ban & Human Emulation
Модуль защиты от блокировок и алгоритмического детекта ботов.
Официальный проект: https://t.me/funpaystudio
Каталог плагинов: https://t.me/fps_plugins1
"""

import random
import time
import logging

logger = logging.getLogger("FPS.anti_ban")

class AntiBanGuard:
    """
    Эмулирует человеческое поведение при работе с биржей FunPay:
    — Размывает точные тайминги автоподнятия лотов (± 90–240 секунд)
    — Защищает от детекта циклов запросов
    """
    @staticmethod
    def calculate_jitter_delay(base_seconds: int = 14400, jitter_range: int = 240) -> int:
        """
        Добавляет случайный разброс к интервалу автоподнятия (по умолчанию 4 часа ± 4 минуты),
        чтобы поднятия лотов не происходили строго секунда в секунду, как у тупых ботов.
        """
        offset = random.randint(-jitter_range, jitter_range)
        target = max(60, base_seconds + offset)
        logger.debug(f"[Anti-Ban] Рандомизация интервала: базовый {base_seconds}s -> с джиттером {target}s")
        return target

    @staticmethod
    def human_typing_delay(text_len: int, min_delay: float = 0.8, max_delay: float = 2.5) -> float:
        """
        Рассчитывает естественную задержку перед ответом, имитируя скорость набора текста человеком.
        """
        chars_factor = min(text_len * 0.02, 1.5)
        delay = round(random.uniform(min_delay, max_delay) + chars_factor, 2)
        return delay
