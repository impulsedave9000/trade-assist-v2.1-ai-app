import json
from datetime import datetime

class ReportEngine:
    def __init__(self, data_path):
        with open(data_path, 'r',encoding="utf-8") as f:
            self.data = json.load(f)
        self.spot = self.data["spot_price"]

    def generate_bar(self, left_pct, right_pct, left_emoji="🔴", right_emoji="🟢"):
        """Generates a strict 10-character bar. No white circles."""
        total = left_pct + right_pct
        if total == 0:
            return left_emoji * 5 + right_emoji * 5
        left_count = round((left_pct / total) * 10)
        right_count = 10 - left_count
        return f"[{left_emoji * left_count}{right_emoji * right_count}]"

    def run_ta2_math(self):
        fd = self.data["flow_data"]
        md = self.data["macro_data"]

        # 1. Flow Score Calculation
        flow_bull = (fd["volume_buy_pct"] + fd["liquidity_absorb_pct"]) / 2.0
        flow_bear = (fd["volume_sell_pct"] + fd["liquidity_distribute_pct"]) / 2.0
        flow_neutral = 100.0 - flow_bull - flow_bear

        # 2. Macro Score Calculation (70% Primary / 30% Secondary)
        macro_bull = (md["primary_driver"]["bullish_pct"] * 0.70) + (md["secondary_driver"]["bullish_pct"] * 0.30)
        macro_bear = (md["primary_driver"]["bearish_pct"] * 0.70) + (md["secondary_driver"]["bearish_pct"] * 0.30)
        macro_neutral = 100.0 - macro_bull - macro_bear

        # 3. Blended Conviction Matrix
        blend_bull = (flow_bull * 0.50) + (macro_bull * 0.50)
        blend_bear = (flow_bear * 0.50) + (macro_bear * 0.50)
        blend_neutral = 100.0 - blend_bull - blend_bear

        # 4. Conflict Resolution Check (Flow Standoff Scenarios)
        vd_net = fd["volume_buy_pct"] - fd["volume_sell_pct"]
        lf_net = fd["liquidity_absorb_pct"] - fd["liquidity_distribute_pct"]

        resolution_type = "TRUE TREND"
        # Scenario 1: Absorption Trap
        if (vd_net > 20 and lf_net < -20) or (vd_net < -20 and lf_net > 20):
            resolution_type = "ABSORPTION TRAP"
            dominant = "bull" if blend_bull > blend_bear else "bear"
            if dominant == "bull":
                blend_bull = max(0.0, blend_bull - 15.0)
            else:
                blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 15.0
        # Scenario 3: Vacuum Drift
        elif abs(vd_net) <= 10 and abs(lf_net) <= 10:
            resolution_type = "VACUUM DRIFT"
            blend_bull = max(0.0, blend_bull - 15.0)
            blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 30.0
        # Scenario 2: Structural Hold
        elif abs(vd_net) <= 10 and (abs(lf_net) > 20):
            resolution_type = "STRUCTURAL HOLD"

        # 5. Neutral Dominance Rule Check
        final_bias = "Neutral"
        final_emoji = "⚪"
        final_score = blend_neutral

        if blend_bull > blend_neutral and blend_bull >= blend_bear:
            final_bias = "Bullish"
            final_emoji = "🟢"
            final_score = blend_bull
        elif blend_bear > blend_neutral and blend_bear >= blend_bull:
            final_bias = "Bearish"
            final_emoji = "🔴"
            final_score = blend_bear

        return {
            "flow_bull": flow_bull, "flow_bear": flow_bear, "flow_neutral": flow_neutral,
            "vd_net": vd_net, "lf_net": lf_net, "res_type": resolution_type,
            "blend_bull": round(blend_bull, 1), "blend_bear": round(blend_bear, 1), "blend_neutral": round(blend_neutral, 1),
            "final_bias": final_bias, "final_emoji": final_emoji, "final_score": round(final_score, 1)
        }

    def compile_price_ladder(self):
        # Sort supply levels descending (furthest to closest)
        supply = sorted(self.data["price_levels"]["supply"], key=lambda x: x["price"], reverse=True)
        # Sort demand levels descending (closest to furthest)
        demand = sorted(self.data["price_levels"]["demand"], key=lambda x: x["price"], reverse=True)

        supply_lines = []
        for s in supply:
            pips = round((s["price"] - self.spot) * 10000)
            sign = "+" if pips >= 0 else ""
            line = f'> {s["price"]:.5f} ▲ {s["timeframe"]} {s["label"]} [ {sign}{pips}pips ] | **Prob: {s["probability"]}** {s["icon"]} **Comment: [LLM_INSERT_FLOW_COMMENT_{s["price"]}]**'
            supply_lines.append(line)

        demand_lines = []
        for d in demand:
            pips = round((d["price"] - self.spot) * 10000)
            sign = "" if pips <= 0 else "+"
            line = f'> {d["price"]:.5f} ▼ {d["timeframe"]} {d["label"]} [ {pips}pips ] | **Prob: {d["probability"]}** {d["icon"]} **Comment: [LLM_INSERT_FLOW_COMMENT_{d["price"]}]**'
            demand_lines.append(line)

        return "\n\n".join(supply_lines), "\n\n".join(demand_lines)

    def generate_report_skeleton(self):
        m = self.run_ta2_math()
        sup_ladder, dem_ladder = self.compile_price_ladder()
        
        # Build strict graphic bars
        vol_bar = self.generate_bar(self.data["flow_data"]["volume_sell_pct"], self.data["flow_data"]["volume_buy_pct"])
        liq_bar = self.generate_bar(self.data["flow_data"]["liquidity_absorb_pct"], self.data["flow_data"]["liquidity_distribute_pct"], "🟢", "🔴")

        timestamp = datetime.utcnow().strftime("%Y-%m-%d | %H:%M:%S")

        report = f"""**ASSIST TRADER V2.1**\n\n
**{self.data["pair"]} ({self.data["pair"]})**\n\n
**TIMESTAMP:** {timestamp} (UTC+8)\n\n
\n\n
**PRICE SOURCE:** {self.spot}
**YOUR BIAS: {self.data["user_bias"]}**
          **FLOW STATE:** [LLM_INSERT_FLOW_STATE]\n\n
**CONVICTION MATRIX:** 🟢 {m["blend_bull"]}% | ⚪ {m["blend_neutral"]}% | 🔴 {m["blend_bear"]}%\n\n
**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} {m["final_score"]}%

---

### **📊 MODULE 1: DUAL FLOW ANALYSIS**

**VOLUME DELTA (H1):**
{self.data["flow_data"]["volume_sell_pct"]}% {vol_bar} {self.data["flow_data"]["volume_buy_pct"]}%
SELL ㅤㅤ [NET: {"BULLISH" if m["vd_net"] >=0 else "BEARISH"} {m["vd_net"]:+}%] ㅤ BUY

**LIQUIDITY FLOW (H1):**
{self.data["flow_data"]["liquidity_absorb_pct"]}% {liq_bar} {self.data["flow_data"]["liquidity_distribute_pct"]}%
ABSORB  [NET: {"BULLISH" if m["lf_net"] >=0 else "BEARISH"} {m["lf_net"]:+}%] ㅤ DISTRIBUTE
(BULL)                                            (BEAR)

**▸ FLOW INTERPRETATION:**
- **Delta Signal:** [LLM_INSERT_DELTA_SIGNAL]
- **Liquidity Signal:** [LLM_INSERT_LIQUIDITY_SIGNAL]
- **Conflict Resolution:** {m["res_type"]}

---

### **🌐 MODULE 2: MACRO LAYERING**

**PRIMARY DRIVER: {self.data["macro_data"]["primary_driver"]["name"]}**

> [LLM_INSERT_FACTOR_1_STRUCTURAL]
> ✅ [IMPACT]: [LLM_INSERT_IMPACT_1]
>
> *[LLM_INSERT_COMMENTARY_1]*

**SECONDARY DRIVER: {self.data["macro_data"]["secondary_driver"]["name"]}**

> [LLM_INSERT_FACTOR_2_STRUCTURAL]
> ✅ [IMPACT]: [LLM_INSERT_IMPACT_2]
>
> *[LLM_INSERT_COMMENTARY_2]*

**▸ LAYER SYNTHESIS:**
> [LLM_INSERT_SYNTHESIS_SUMMARY]
>
> *[LLM_INSERT_SYNTHESIS_MENTOR_COMMENTARY]*

---

### **📈 MODULE 3: DYNAMIC PRICE LADDER**

▸ SUPPLY ZONES (RESISTANCE)

{sup_ladder}

📍 **SPOT: {self.spot}** | **ZONE: [LLM_INSERT_ACTIVE_ZONE]**

{dem_ladder}

▸ DEMAND ZONES (SUPPORT)

---

### **⚡ MODULE 4: EXECUTION LOGIC & RISK**

**✅ SCENARIO A: STRUCTURE BULLISH PLAY**
- **Trigger:** [LLM_INSERT_BULLISH_TRIGGER]
- **Target:** [LLM_INSERT_BULLISH_TARGET] | **Risk:** [LLM_INSERT_BULLISH_RISK] | **Probability:** [LLM_INSERT_BULL_PROB]%
- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BULL_STOP_SHIELDING] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BULL_STOP_PHYSICS]

**❌ SCENARIO B: STRUCTURE BEARISH PLAY**
- **Trigger:** [LLM_INSERT_BEARISH_TRIGGER]
- **Target:** [LLM_INSERT_BEARISH_TARGET] | **Risk:** [LLM_INSERT_BEARISH_RISK] | **Probability:** [LLM_INSERT_BEAR_PROB]%
- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BEAR_STOP_SHIELDING] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BEAR_STOP_PHYSICS]

---

### **🛡️ DEVIL'S ADVOCATE (V2.1 ENHANCED)**
>
> * **The Pretension vs. Reality Check:** [LLM_INSERT_PRETENSION]
> * **The Threat to Your Bias:** "If you go {self.data["user_bias"]}: [LLM_INSERT_THREAT_WARNING]."
> * **The Panic Mitigation:** "If you see [LLM_INSERT_PANIC_LEVEL]: [LLM_INSERT_MITIGATION_RULES]."
> * **Core Truth:** [LLM_INSERT_CORE_TRUTH]

"""
        return report

# Usage
engine = ReportEngine("market_state.json")
print(engine.generate_report_skeleton())