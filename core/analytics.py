"""
FunPay Studio — Financial Analytics
Модуль учета выручки, чистой прибыли, конверсии и выполненных заказов.
Официальный проект: https://t.me/funpaystudio
Каталог плагинов: https://t.me/fps_plugins1
"""

import os
import json
import time
from datetime import datetime

class SalesAnalytics:
    def __init__(self, data_file: str = "storage/analytics.json"):
        self.data_file = data_file
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"orders": [], "total_revenue": 0.0, "total_profit": 0.0}

    def _save(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def record_order(self, order_id: str, title: str, revenue: float, cost: float = 0.0):
        profit = revenue - cost
        entry = {
            "order_id": order_id,
            "title": title,
            "revenue": round(revenue, 2),
            "cost": round(cost, 2),
            "profit": round(profit, 2),
            "timestamp": int(time.time()),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.data["orders"].append(entry)
        self.data["total_revenue"] = round(self.data["total_revenue"] + revenue, 2)
        self.data["total_profit"] = round(self.data["total_profit"] + profit, 2)
        self._save()

    def get_summary_today(self) -> dict:
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_orders = [o for o in self.data["orders"] if o.get("date", "").startswith(today_str)]
        revenue = sum(o["revenue"] for o in today_orders)
        profit = sum(o["profit"] for o in today_orders)
        return {
            "count": len(today_orders),
            "revenue": round(revenue, 2),
            "profit": round(profit, 2)
        }
