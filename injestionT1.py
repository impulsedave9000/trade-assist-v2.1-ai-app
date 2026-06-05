import json
import os
from datetime import datetime, timedelta

class DataVacuum:
    def __init__(self, pair="AUDUSD"):
        self.pair = pair.upper()
        self.file_path = "market_state.json"
        
    def check_time_gate(self) -> bool:
        """
        Enforces rule 2b: Returns True if file is missing or data is older than 5 minutes.
        Returns False to halt the ingestion cycle.
        """
        if not os.path.exists(self.file_path):
            return True
            
        try:
            with open(self.file_path, "r") as f:
                current_data = json.load(f)
                
            last_timestamp_str = current_data.get("timestamp", "")
            if not last_timestamp_str:
                return True
                
            last_time = datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
            time_difference = datetime.now() - last_time
            
            # If less than 5 minutes have passed, trigger the lock
            if time_difference < timedelta(minutes=5):
                print(f"[!] Time Gate Active: Data is only {time_difference.seconds}s old. Halting.")
                return False
        except Exception as e:
            print(f"[-] Error reading time gate, forcing override: {e}")
            return True
            
        return True

    def run_ingestion_cycle(self):
        """Executes the mechanical ingestion of the 4 key data points."""
        print(f"[+] Activating Vacuum for {self.pair}...")
        
        # 1. Fetch Spot Price (Pure Float Setup)
        spot_price_feed = 0.66520 
        
        # 2. Flow Data (Single Source Proxy Baseline)
        flow_data_feed = {
            "volume_buy_pct": 58,
            "volume_sell_pct": 42,
            "liquidity_absorb_pct": 62,
            "liquidity_distribute_pct": 38
        }
        
        # 3. Macro Layer (Limited to 1 Core News/Desk Sentiment Block to prevent bloat)
        macro_feed = {
            "primary_driver": {
                "name": "RBA Hawkish Stance (Single Source Desk Feed)",
                "bullish_pct": 65,
                "bearish_pct": 35
            },
            "secondary_driver": {
                "name": "US Dollar Index Profit Taking",
                "bullish_pct": 55,
                "bearish_pct": 45
            }
        }
        
        # 4. Raw Unfiltered Ladder Stock
        levels_feed = [
            {"price": 0.66850, "timeframe": "H1", "label": "Session Liquidity Ceiling"},
            {"price": 0.66200, "timeframe": "D1", "label": "Daily Structural Demand"},
            {"price": 0.68100, "timeframe": "W1", "label": "Extreme Macro Supply Pool"} # > 120 pips away
        ]
        
        # Construct the payload manifest
        manifest = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pair": self.pair,
            "spot_price": spot_price_feed,
            "flow_data": flow_data_feed,
            "macro_data": macro_feed,
            "raw_price_levels": levels_feed
        }
        
        # Overwrite the json file cleanly
        with open(self.file_path, "w") as f:
            json.dump(manifest, f, indent=4)
        print(f"[+] Engine Intake Clear. {self.file_path} updated successfully.")
        return "Success"

    def execute(self) -> str:
        if self.check_time_gate():
            return self.run_ingestion_cycle()
        else:
            return "Skipped: Data is less than 5 minutes old."

if __name__ == "__main__":
    vacuum = DataVacuum()
    vacuum.execute()