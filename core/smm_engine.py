"""
FunPay Studio — SMM & Reselling Engine
Встроенный модуль перепродажи цифровых услуг и накрутки соцсетей (Telegram, TikTok, VK, Twitch, YouTube).
Официальный проект: https://t.me/funpaystudio
Каталог плагинов: https://t.me/fps_plugins1
"""

import logging
import urllib.request
import urllib.parse
import json

logger = logging.getLogger("FPS.smm_engine")

class SMMEngine:
    def __init__(self, api_url: str = "https://vingboost.com/api/v2", api_key: str = ""):
        self.api_url = api_url
        self.api_key = api_key

    def _post(self, data: dict) -> dict:
        data["key"] = self.api_key
        payload = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=payload,
            headers={"User-Agent": "FunPayStudio/1.0 (+https://t.me/funpaystudio)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"SMM Engine API error: {e}")
            return {"error": str(e)}

    def get_balance(self) -> float:
        res = self._post({"action": "balance"})
        if "balance" in res:
            try:
                return float(res["balance"])
            except:
                pass
        return 0.0

    def create_order(self, service_id: int, link: str, quantity: int) -> dict:
        data = {
            "action": "add",
            "service": service_id,
            "link": link,
            "quantity": quantity
        }
        res = self._post(data)
        logger.info(f"SMM Order created for service {service_id} -> link {link}: {res}")
        return res

    def get_order_status(self, order_id: int | str) -> dict:
        return self._post({"action": "status", "order": order_id})
