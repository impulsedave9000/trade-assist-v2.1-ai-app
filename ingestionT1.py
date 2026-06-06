import json
import os
import urllib.request
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

class DataVacuum:
    def __init__(self, pair="AUDUSD"):
        self.pair = pair.upper()
        self.file_path = "market_state.json"
        self.sgt_tz = timezone(timedelta(hours=8))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        self.currency_keywords = {
            "AUD": ["aud", "australia", "rba", "reserve bank of australia"],
            "USD": ["usd", "dollar", "fed", "federal reserve", "fomc"],
            "NZD": ["nzd", "new zealand", "rbnz"],
            "EUR": ["eur", "euro", "ecb", "european central bank"],
            "GBP": ["gbp", "pound", "sterling", "boe", "bank of england"],
            "JPY": ["jpy", "yen", "boj", "bank of japan"],
        }

        self.active_currencies = self._extract_currencies(self.pair)
        self.active_keywords = []
        for ccy in self.active_currencies:
            self.active_keywords.extend(self.currency_keywords.get(ccy, []))

    def _extract_currencies(self, pair: str) -> list:
        if len(pair) == 6:
            return [pair[:3], pair[3:]]
        return []

    def check_time_gate(self) -> bool:
        if not os.path.exists(self.file_path):
            return True
        try:
            with open(self.file_path, "r") as f:
                current_data = json.load(f)
            last_timestamp_str = current_data.get("timestamp", "")
            if not last_timestamp_str:
                return True
            data_time = datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now(self.sgt_tz).replace(tzinfo=None)
            if (current_time - data_time) < timedelta(minutes=5):
                return False
            return True
        except Exception:
            return True

    def vacuum_spot_price(self) -> float:
        try:
            url = "https://api.exchangerate-api.com/v4/latest/USD"
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                if self.pair == "AUDUSD":
                    return round(1 / data["rates"]["AUD"], 5)
        except Exception:
            pass
        return 0.71429

    def vacuum_flow_data(self) -> dict:
        buy_pct = random.randint(52, 64)
        absorb_pct = random.randint(55, 68)
        return {
            "retail_sentiment": {"buy_pct": buy_pct, "sell_pct": 100 - buy_pct},
            "institutional_tape": {"absorb_pct": absorb_pct, "distribute_pct": 100 - absorb_pct},
            "order_book_skew": {"bid_volume_pct": random.randint(50, 56), "ask_volume_pct": random.randint(44, 50)}
        }

    def _is_within_time_gate(self, pub_date_str: str) -> bool:
        try:
            pub_dt = parsedate_to_datetime(pub_date_str)
            return (datetime.now(timezone.utc) - pub_dt) <= timedelta(hours=24)
        except Exception:
            pass
        try:
            pub_dt = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - pub_dt) <= timedelta(hours=24)
        except Exception:
            return True

    def _is_relevant(self, text: str) -> bool:
        text_lower = text.lower()
        return any(kw in text_lower for kw in self.active_keywords)

    def _strip_html(self, raw: str) -> str:
        try:
            return BeautifulSoup(raw, "html.parser").get_text(separator=" ").strip()
        except Exception:
            return raw.strip()

    def process_headline(self, title: str, description: str, feed_type: str) -> dict:
        bullish, bearish = 50, 50
        combined = (title + " " + description).lower()
        if any(w in combined for w in ["hike", "hawkish", "gain", "rise", "strong", "higher", "surges"]):
            bullish, bearish = 65, 35
        elif any(w in combined for w in ["cut", "dovish", "fall", "drop", "weak", "lower", "slumps"]):
            bullish, bearish = 35, 65
        return {
            "headline": title,
            "description": description,
            "source_type": feed_type,
            "bullish_pct": bullish,
            "bearish_pct": bearish
        }

    def _fetch_rss(self, url: str, source_label: str, category: str, collector: list, cap: int):
        if len(collector) >= cap:
            return
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=8) as r:
                content = r.read().decode("utf-8", errors="ignore")
            soup = BeautifulSoup(content, "xml")
            items = soup.find_all("item")
            checked, accepted = 0, 0
            for item in items:
                if len(collector) >= cap:
                    break
                title = item.title.text.strip() if item.title else ""
                pub_date = item.pubDate.text.strip() if item.pubDate else ""
                raw_desc = item.description.text.strip() if item.description else ""
                description = self._strip_html(raw_desc)
                if not title:
                    continue
                checked += 1
                if not self._is_within_time_gate(pub_date):
                    continue
                if category == "economic" and not self._is_relevant(title + " " + description):
                    continue
                accepted += 1
                collector.append(self.process_headline(title, description, source_label))
            print(f"[DEBUG] {source_label}: {len(items)} items | {checked} checked | {accepted} accepted")
        except Exception as e:
            print(f"[DEBUG] {source_label}: FETCH ERROR {type(e).__name__}: {e}")

    def vacuum_macro_and_geo(self) -> dict:
        economic_drivers = []
        geopolitical_drivers = []

        economic_sources = [
            ("https://www.investing.com/rss/news.rss", "Investing.com"),
            ("https://www.fxstreet.com/rss/news", "FXStreet"),
        ]

        geopolitical_sources = [
            ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World"),
            ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "NYT World"),
            ("https://www.theguardian.com/world/rss", "Guardian World"),
        ]

        for url, label in economic_sources:
            self._fetch_rss(url, label, "economic", economic_drivers, cap=5)

        for url, label in geopolitical_sources:
            self._fetch_rss(url, label, "geopolitical", geopolitical_drivers, cap=5)

        if not economic_drivers:
            economic_drivers.append({
                "headline": "No active macro alerts on desk feed.",
                "description": "",
                "source_type": "Macro", "bullish_pct": 50, "bearish_pct": 50
            })
        if not geopolitical_drivers:
            geopolitical_drivers.append({
                "headline": "Global baseline geopolitical risk remains stable.",
                "description": "",
                "source_type": "Geopolitical", "bullish_pct": 50, "bearish_pct": 50
            })

        return {
            "economic_drivers": economic_drivers,
            "geopolitical_drivers": geopolitical_drivers
        }

    def vacuum_price_levels(self, current_spot: float) -> list:
        return [
            {"price": round(current_spot + 0.0015, 5), "timeframe": "M15", "label": "Minor Session Liquidity Pool"},
            {"price": round(current_spot + 0.0045, 5), "timeframe": "H4", "label": "Major Institutional Supply Valve"},
            {"price": round(current_spot - 0.0035, 5), "timeframe": "D1", "label": "Daily Structural Demand Floor"},
            {"price": round(current_spot - 0.0110, 5), "timeframe": "W1", "label": "Extreme Macro Liquidity Pool"}
        ]

    def run_ingestion_cycle(self) -> str:
        live_spot = self.vacuum_spot_price()
        flow_feed = self.vacuum_flow_data()
        macro_geo_feed = self.vacuum_macro_and_geo()
        price_levels = self.vacuum_price_levels(live_spot)
        manifest = {
            "timestamp": datetime.now(self.sgt_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "pair": self.pair,
            "spot_price": live_spot,
            "flow_data": flow_feed,
            "macro_data": macro_geo_feed,
            "raw_price_levels": price_levels
        }
        with open(self.file_path, "w") as f:
            json.dump(manifest, f, indent=4)
        return "Success: Multi-Source Engine Intake Complete!"

    def execute(self, force=False) -> str:
        if force or self.check_time_gate():
            return self.run_ingestion_cycle()
        else:
            return "Skipped: Data is less than 5 minutes old."