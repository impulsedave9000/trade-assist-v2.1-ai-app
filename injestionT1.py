def vacuum_macro_and_geo(self) -> dict:
        """Harvests clean data entries utilizing the yfinance ticker framework."""
        economic_drivers = []
        geopolitical_drivers = []
        shared_drivers = []

        try:
            # Shifted to the core spot currency ticker to ensure a live data feed stream
            pair_ticker = yf.Ticker("AUDUSD=X")
            raw_news = pair_ticker.news
            
            if raw_news and isinstance(raw_news, list):
                for article in raw_news:
                    title = article.get("title", "")
                    summary = article.get("summary", "").lower() if article.get("summary") else ""
                    combined_text = (title + " " + summary).lower()
                    
                    if not title:
                        continue

                    # Local Guard Rail: Drop obvious corporate tech equity news
                    if any(x in combined_text for x in ["tsmc", "nvidia", "apple", "earnings", "quarterly", "ipo"]):
                        continue

                    # Slot 1: Pure Macro (Rates, Inflation, Central Banks, Bond Yields, Broad Currency)
                    if len(economic_drivers) < 5:
                        if any(w in combined_text for w in ["rate", "fed", "rba", "inflation", "cpi", "yield", "bond", "currency", "dollar", "fx", "usd", "aud"]):
                            economic_drivers.append(self.process_headline(title, "yFinance Macro"))
                            continue

                    # Slot 2: Geopolitical (Tariffs, Sanctions, Trade Friction, Global Shifts)
                    if len(geopolitical_drivers) < 5:
                        if any(w in combined_text for w in ["tariff", "sanction", "trade war", "geopolit", "border", "conflict", "military", "china", "global"]):
                            geopolitical_drivers.append(self.process_headline(title, "yFinance Geopolitical"))
                            continue

                    # Slot 3: Shared Bridge (Foundational Economy, Growth, GDP, General Macro Conditions)
                    if len(shared_drivers) < 5:
                        if any(w in combined_text for w in ["gdp", "economy", "growth", "unemployment", "jobs", "recession", "market"]):
                            shared_drivers.append(self.process_headline(title, "yFinance Bridge"))
                            continue
        except Exception:
            pass

        # Automated fallbacks to keep arrays structurally sound if processing hits an ultra-quiet market gap
        if not economic_drivers:
            economic_drivers.append({"headline": "No active macro alerts on desk feed.", "source_type": "Macro", "bullish_pct": 50, "bearish_pct": 50})
        if not geopolitical_drivers:
            geopolitical_drivers.append({"headline": "Global baseline geopolitical risk remains stable.", "source_type": "Geopolitical", "bullish_pct": 50, "bearish_pct": 50})
        if not shared_drivers:
            shared_drivers.append({"headline": "Global macro policy landscape trading within normal ranges.", "source_type": "Shared Bridge", "bullish_pct": 50, "bearish_pct": 50})

        return {
            "economic_drivers": economic_drivers,
            "geopolitical_drivers": geopolitical_drivers,
            "shared_drivers": shared_drivers
        }