import json
import urllib.request
from datetime import datetime

class ReportEngine:
    def __init__(self, data_path, live_pair=None, live_bias=None):
        # 1. Start with your exact core data structure as the sterile baseline
        self.data = {
            "spot_price": 0.65420,
            "flow_data": {
                "volume_buy_pct": 65, "volume_sell_pct": 35,
                "liquidity_absorb_pct": 30, "liquidity_distribute_pct": 70
            },
            "macro_data": {
                "primary_driver": { "name": "RBA Hawkish Hold", "bullish_pct": 70, "bearish_pct": 10 },
                "secondary_driver": { "name": "DXY Profit Taking", "bullish_pct": 60, "bearish_pct": 20 }
            },
            "price_levels": {
                "supply": [
                    {"price": 0.65920, "timeframe": "H1", "label": "Unmitigated Order Block", "probability": "HIGH", "icon": "🔥"},
                    {"price": 0.65670, "timeframe": "D1", "label": "Daily Range High", "probability": "MED", "icon": "💧"}
                ],
                "demand": [
                    {"price": 0.65170, "timeframe": "H1", "label": "Resting Bid Wall", "probability": "HIGH", "icon": "🔥"},
                    {"price": 0.64920, "timeframe": "W1", "label": "Weekly Key Support", "probability": "LOW", "icon": "❄"}
                ]
            }
        }

        # 🌐 PROGRAMMATIC EXTRACTOR: Reach out to the live world dynamically
        try:
            pair_ticker = live_pair if live_pair else "AUDUSD"
            # Target a clean, zero-auth public financial tracking matrix
            url = f"https://api.exchangerate-api.com/v4/latest/USD"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                web_data = json.loads(response.read().decode())
                
                if "rates" in web_data:
                    usd_aud = web_data["rates"].get("AUD", 1.528)
                    # Dynamically calculate the live spot exchange rate based on currency selection
                    current_live_spot = round(1 / usd_aud, 5) if pair_ticker == "AUDUSD" else 0.65420
                    
                    # Overwrite the static memory snapshot with actual market coordinates
                    self.data["spot_price"] = current_live_spot
        except Exception as e:
            # If the network environment timeouts, gracefully keep going with baseline matrix
            pass

        # Establish dynamic parameters for your math models
        self.pair = live_pair if live_pair else "AUDUSD"
        self.user_bias = live_bias if live_bias else "NEUTRAL"
        self.spot = self.data.get("spot_price", 0.65420)

    def generate_bar(self, left_pct, right_pct, left_emoji="🔴", right_emoji="🟢"):
        total = left_pct + right_pct
        if total == 0:
            return f"[{left_emoji * 5}{right_emoji * 5}]"
        left_count = int(round((left_pct / total) * 10))
        right_count = 10 - left_count
        return f"[{left_emoji * left_count}{right_emoji * right_count}]"

    def run_ta_math(self):
        md = self.data["macro_data"]
        econ_bull = md["primary_driver"].get("bullish_pct", 0.0)
        econ_bear = md["primary_driver"].get("bearish_pct", 0.0)
        econ_neut = max(0.0, 100.0 - econ_bull - econ_bear)
        
        sent_bull = md["secondary_driver"].get("bullish_pct", 0.0)
        sent_bear = md["secondary_driver"].get("bearish_pct", 0.0)
        sent_neut = max(0.0, 100.0 - sent_bull - sent_bear)
        
        macro_bull = (econ_bull * 0.60) + (sent_bull * 0.40)
        macro_bear = (econ_bear * 0.60) + (sent_bear * 0.40)
        macro_neut = (econ_neut * 0.60) + (sent_neut * 0.40)
        
        user_bull = 100.0 if self.user_bias.upper() == "BULLISH" else 0.0
        user_bear = 100.0 if self.user_bias.upper() == "BEARISH" else 0.0
        user_neut = 100.0 if self.user_bias.upper() == "NEUTRAL" else 0.0
        
        blend_bull = (macro_bull * 0.85) + (user_bull * 0.15)
        blend_bear = (macro_bear * 0.85) + (user_bear * 0.15)
        blend_neut = (macro_neut * 0.85) + (user_neut * 0.15)
        
        rbull = int(round(blend_bull))
        rbear = int(round(blend_bear))
        rneut = int(round(blend_neut))
        
        diff = 100 - (rbull + rbear + rneut)
        rneut += diff
        
        if max(rbull, rbear) <= rneut:
            final_bias = "Neutral / Range-bound"
            final_emoji = "⚪"
            final_score = rneut
        elif rbull > rbear:
            final_bias = "Bullish"
            final_emoji = "🟢"
            final_score = rbull
        else:
            final_bias = "Bearish"
            final_emoji = "🔴"
            final_score = rbear
            
        return {
            "bullish": rbull, "neutral": rneut, "bearish": rbear,
            "final_bias": final_bias, "final_emoji": final_emoji, "final_score": final_score
        }

    def run_ta2_math(self):
        fd = self.data["flow_data"]
        md = self.data["macro_data"]

        flow_bull = (fd["volume_buy_pct"] + fd["liquidity_absorb_pct"]) / 2.0
        flow_bear = (fd["volume_sell_pct"] + fd["liquidity_distribute_pct"]) / 2.0
        flow_neutral = 100.0 - flow_bull - flow_bear

        macro_bull = (md["primary_driver"]["bullish_pct"] * 0.70) + (md["secondary_driver"]["bullish_pct"] * 0.30)
        macro_bear = (md["primary_driver"]["bearish_pct"] * 0.70) + (md["secondary_driver"]["bearish_pct"] * 0.30)
        macro_neutral = 100.0 - macro_bull - macro_bear

        blend_bull = (flow_bull * 0.50) + (macro_bull * 0.50)
        blend_bear = (flow_bear * 0.50) + (macro_bear * 0.50)
        blend_neutral = 100.0 - blend_bull - blend_bear

        vd_net = fd["volume_buy_pct"] - fd["volume_sell_pct"]
        lf_net = fd["liquidity_absorb_pct"] - fd["liquidity_distribute_pct"]

        resolution_type = "TRUE TREND Expansion"
        
        if (vd_net > 20 and lf_net < -20) or (vd_net < -20 and lf_net > 20):
            resolution_type = "ABSORPTION TRAP"
            if blend_bull > blend_bear:
                blend_bull = max(0.0, blend_bull - 15.0)
            else:
                blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 15.0
            
        elif abs(vd_net) <= 10 and abs(lf_net) <= 10:
            resolution_type = "VACUUM DRIFT / LIQUIDITY VACUUM"
            blend_bull = max(0.0, blend_bull - 15.0)
            blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 30.0
            
        elif abs(vd_net) <= 10 and abs(lf_net) > 20:
            resolution_type = "STRUCTURAL HOLD"

        rbull = int(round(blend_bull))
        rbear = int(round(blend_bear))
        rneut = int(round(blend_neutral))
        
        diff = 100 - (rbull + rbear + rneut)
        rneut += diff

        final_bias = "Neutral / Range-bound"
        final_emoji = "⚪"
        final_score = rneut

        if rbull > rneut and rbull >= rbear:
            final_bias = "Bullish"
            final_emoji = "🟢"
            final_score = rbull
        elif rbear > rneut and rbear >= rbull:
            final_bias = "Bearish"
            final_emoji = "🔴"
            final_score = rbear

        return {
            "vd_net": vd_net, "lf_net": lf_net, "res_type": resolution_type,
            "blend_bull": rbull, "blend_bear": rbear, "blend_neutral": rneut,
            "final_bias": final_bias, "final_emoji": final_emoji, "final_score": final_score
        }

    def compile_price_ladder(self):
        supply = sorted(self.data["price_levels"]["supply"], key=lambda x: x["price"], reverse=True)
        demand = sorted(self.data["price_levels"]["demand"], key=lambda x: x["price"], reverse=True)

        supply_lines = []
        for s in supply:
            pips = int(round((s["price"] - self.spot) * 10000))
            sign = "+" if pips >= 0 else ""
            line = f'> {s["price"]:.5f} ▲ {s["timeframe"]} {s["label"]} [ {sign}{pips}pips ] | **Prob: {s["probability"]}** {s["icon"]} **Comment: [LLM_INSERT_FLOW_COMMENT_{s["price"]:.5f}]**'
            supply_lines.append(line)

        demand_lines = []
        for d in demand:
            pips = int(round((d["price"] - self.spot) * 10000))
            sign = "" if pips <= 0 else "+"
            line = f'> {d["price"]:.5f} ▼ {d["timeframe"]} {d["label"]} [ {pips}pips ] | **Prob: {d["probability"]}** {d["icon"]} **Comment: [LLM_INSERT_FLOW_COMMENT_{d["price"]:.5f}]**'
            demand_lines.append(line)

        return "\n\n".join(supply_lines), "\n\n".join(demand_lines)

    def generate_report_skeleton(self, report_mode="TA2"):
        sup_ladder, dem_ladder = self.compile_price_ladder()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d | %H:%M:%S")

        if report_mode.upper() == "TA":
            m = self.run_ta_math()
            return f"""**ASSIST TRADER V1.2**\n**{self.pair} ({self.pair})**\n**TIMESTAMP:** {timestamp} (UTC+8)\n**PRICE SOURCE:** {self.spot:.5f}\n\n**YOUR BIAS: {self.user_bias} [🟢/⚪/🔴] (Weight: 15%)**\n**PRIMARY BIAS:** 🟢 {m["bullish"]}% | ⚪ {m["neutral"]}% | 🔴 {m["bearish"]}% \n**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} {m["final_score"]}%..."""
        else:
            m = self.run_ta2_math()
            vol_bar = self.generate_bar(self.data["flow_data"]["volume_sell_pct"], self.data["flow_data"]["volume_buy_pct"])
            liq_bar = self.generate_bar(self.data["flow_data"]["liquidity_absorb_pct"], self.data["flow_data"]["liquidity_distribute_pct"], "🟢", "🔴")

            return f"""**ASSIST TRADER V2.1**\n**{self.pair} ({self.pair})**\n**TIMESTAMP:** {timestamp} (UTC+8)\n**PRICE SOURCE:** {self.spot:.5f}\n**YOUR BIAS: {self.user_bias}**\n**FLOW STATE:** {m["res_type"]}\n**CONVICTION MATRIX:** 🟢 {m["blend_bull"]}% | ⚪ {m["blend_neutral"]}% | 🔴 {m["blend_bear"]}% \n**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} {m["final_score"]}%...\n\n### **📊 MODULE 1: DUAL FLOW ANALYSIS**\n\n**VOLUME DELTA (H1):**\nㅤㅤㅤㅤ{self.data["flow_data"]["volume_sell_pct"]}% {vol_bar} {self.data["flow_data"]["volume_buy_pct"]}% \nㅤㅤㅤㅤSELLㅤㅤㅤ[NET: {"BULLISH" if m["vd_net"] >=0 else "BEARISH"} {m["vd_net"]:+}%]ㅤㅤBUY\n\n**LIQUIDITY FLOW (H1):**\nㅤㅤㅤㅤ{self.data["flow_data"]["liquidity_absorb_pct"]}% {liq_bar} {self.data["flow_data"]["liquidity_distribute_pct"]}% \nㅤㅤㅤABSORBㅤㅤ[NET: {"BULLISH" if m["lf_net"] >=0 else "BEARISH"} {m["lf_net"]:+}%]ㅤDISTRIBUTE\n\n**▸ FLOW INTERPRETATION:**\n- **Delta Signal:** [LLM_INSERT_DELTA_SIGNAL_AGGRESSION_OR_EXHAUSTION]\n- **Liquidity Signal:** [LLM_INSERT_LIQUIDITY_SIGNAL_WALLS_OR_VACUUMS]\n- **Conflict Resolution:** {m["res_type"]}\n\n### **🌐 MODULE 2: MACRO LAYERING**\n\n**PRIMARY DRIVER: {self.data["macro_data"]["primary_driver"]["name"]}**\n> [LLM_INSERT_FACTOR_1_STRUCTURAL_T1]\n> ✅ **[IMPACT]: [LLM_INSERT_IMPACT_EMOJI_1]**\n>\n> *Mentor Commentary: [LLM_INSERT_COMMENTARY_1_T2]*\n\n**SECONDARY DRIVER: {self.data["macro_data"]["secondary_driver"]["name"]}**\n> [LLM_INSERT_FACTOR_2_STRUCTURAL_T1]\n> ✅ **[IMPACT]: [LLM_INSERT_IMPACT_EMOJI_2]**\n>\n> *Mentor Commentary: [LLM_INSERT_COMMENTARY_2_T2]*\n\n**▸ LAYER SYNTHESIS:**\n> [LLM_INSERT_SYNTHESIS_SUMMARY_T1]\n>\n> *Mentor Commentary: [LLM_INSERT_SYNTHESIS_MENTOR_COMMENTARY_T2]*\n\n### **📈 MODULE 3: DYNAMIC PRICE LADDER**\n\n▸ SUPPLY ZONES (RESISTANCE)\n{sup_ladder}\n\n📍 **SPOT: {self.spot:.5f}** | **ZONE: [LLM_INSERT_ACTIVE_MARKET_ZONE_METRIC]**\n\n{dem_ladder}\n▸ DEMAND ZONES (SUPPORT)\n\n### **⚡ MODULE 4: EXECUTION LOGIC & RISK**\n\n**✅ SCENARIO A: STRUCTURE BULLISH PLAY**\n- **Trigger:** [LLM_INSERT_BULLISH_TRIGGER_H1_PA_CLOSE_RULE]\n- **Target:** [LLM_INSERT_BULLISH_TARGET_LEVEL] | **Risk:** [LLM_INSERT_BULLISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BULL_PROB]%\n- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BULL_STOP_SHIELDING_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BULL_STOP_PHYSICS]\n\n**❌ SCENARIO B: STRUCTURE BEARISH PLAY**\n- **Trigger:** [LLM_INSERT_BEARISH_TRIGGER_H1_PA_CLOSE_RULE]\n- **Target:** [LLM_INSERT_BEARISH_TARGET_LEVEL] | **Risk:** [LLM_INSERT_BEARISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BEAR_PROB]%\n- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BEAR_STOP_SHIELDING_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BEAR_STOP_PHYSICS]\n\n### **🛡️ DEVIL'S ADVOCATE (V2.1 ENHANCED)**\n>\n> * **The Pretension vs. Reality Check:** [LLM_INSERT_PRETENSION_V_REALITY]\n> * **The Threat to Your Bias:** "If you go {self.user_bias}: [LLM_INSERT_THREAT_WARNING_TRAP_AND_CATALYST]."\n> * **The Panic Mitigation:** "If you see [LLM_INSERT_PANIC_LEVEL_BREAK]: [LLM_INSERT_MITIGATION_RULES_TO_PREVENT_PANIC]."\n> * **Core Truth:** [LLM_INSERT_CORE_TRUTH_PASSIVE_VS_ACTIVE_DEFENSE]"""