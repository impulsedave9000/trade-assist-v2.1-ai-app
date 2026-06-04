# engine.py
import json
from datetime import datetime

class ReportEngine:
    def __init__(self, data_path, live_pair=None, live_bias=None):
        with open(data_path, 'r', encoding="utf-8") as f:
            self.data = json.load(f)
        
        # Override JSON files dynamically if the user updates variables in Streamlit UI
        self.pair = live_pair if live_pair else self.data.get("pair", "UNKNOWN")
        self.user_bias = live_bias if live_bias else self.data.get("user_bias", "NEUTRAL")
        self.spot = self.data.get("spot_price", 0.0)

    def generate_bar(self, left_pct, right_pct, left_emoji="🔴", right_emoji="🟢"):
        """Generates an un-dilutable, fixed 10-character visual bar for mobile rendering layouts."""
        total = left_pct + right_pct
        if total == 0:
            return f"[{left_emoji * 5}{right_emoji * 5}]"
        left_count = int(round((left_pct / total) * 10))
        right_count = 10 - left_count
        return f"[{left_emoji * left_count}{right_emoji * right_count}]"

    def run_ta_math(self):
        """
        Executes v1.2 Math Pipeline: 85% Macro / 15% User Bias Split
        Macro uses a strict 60% Econ / 40% Sentiment configuration
        """
        md = self.data["macro_data"]
        
        # Extract Econ & Sentiment raw internal weights
        econ_bull = md["primary_driver"].get("bullish_pct", 0.0)
        econ_bear = md["primary_driver"].get("bearish_pct", 0.0)
        econ_neut = max(0.0, 100.0 - econ_bull - econ_bear)
        
        sent_bull = md["secondary_driver"].get("bullish_pct", 0.0)
        sent_bear = md["secondary_driver"].get("bearish_pct", 0.0)
        sent_neut = max(0.0, 100.0 - sent_bull - sent_bear)
        
        # Composite Blend Calculations
        macro_bull = (econ_bull * 0.60) + (sent_bull * 0.40)
        macro_bear = (econ_bear * 0.60) + (sent_bear * 0.40)
        macro_neut = (econ_neut * 0.60) + (sent_neut * 0.40)
        
        # Isolate User Bias Vector Values
        user_bull = 100.0 if self.user_bias.upper() == "BULLISH" else 0.0
        user_bear = 100.0 if self.user_bias.upper() == "BEARISH" else 0.0
        user_neut = 100.0 if self.user_bias.upper() == "NEUTRAL" else 0.0
        
        # Apply 85/15 Integration Weight Allocation
        blend_bull = (macro_bull * 0.85) + (user_bull * 0.15)
        blend_bear = (macro_bear * 0.85) + (user_bear * 0.15)
        blend_neut = (macro_neut * 0.85) + (user_neut * 0.15)
        
        # Deterministic Whole-Integer Pre-Rounding Matrix Shield
        rbull = int(round(blend_bull))
        rbear = int(round(blend_bear))
        rneut = int(round(blend_neut))
        
        diff = 100 - (rbull + rbear + rneut)
        rneut += diff
        
        # Enforce Step 6: Neutral Dominance Rule Check
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
        """
        Executes v2.1 Math Pipeline: Strict 50% Flow Score / 50% Macro Score Split
        Processes Systemic Standoff Conflict Matrix Shifts automatically
        """
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

        resolution_type = "TRUE TREND Expansion"
        
        # Scenario 1: Absorption Trap
        if (vd_net > 20 and lf_net < -20) or (vd_net < -20 and lf_net > 20):
            resolution_type = "ABSORPTION TRAP"
            if blend_bull > blend_bear:
                blend_bull = max(0.0, blend_bull - 15.0)
            else:
                blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 15.0
            
        # Scenario 3: Vacuum Drift
        elif abs(vd_net) <= 10 and abs(lf_net) <= 10:
            resolution_type = "VACUUM DRIFT / LIQUIDITY VACUUM"
            blend_bull = max(0.0, blend_bull - 15.0)
            blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 30.0
            
        # Scenario 2: Structural Hold
        elif abs(vd_net) <= 10 and abs(lf_net) > 20:
            resolution_type = "STRUCTURAL HOLD"

        # Deterministic Rounding (Guarantees calculation safety)
        rbull = int(round(blend_bull))
        rbear = int(round(blend_bear))
        rneut = int(round(blend_neutral))
        
        diff = 100 - (rbull + rbear + rneut)
        rneut += diff

        # 5. Neutral Dominance Rule Check (Enforced on clean whole integers)
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
        """Processes ladder calculations, measures dynamic pip offsets, and locks layout sorting."""
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
        """Compiles clean skeletons, mapping the pre-calculated numbers securely as frozen parameters."""
        sup_ladder, dem_ladder = self.compile_price_ladder()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d | %H:%M:%S")

        if report_mode.upper() == "TA":
            m = self.run_ta_math()
            return f"""**ASSIST TRADER V1.2**
**{self.pair} ({self.pair})**
**TIMESTAMP:** {timestamp} (UTC+8)
**PRICE SOURCE:** {self.spot:.5f}

**YOUR BIAS: {self.user_bias} [🟢/⚪/🔴] (Weight: 15%)**
**PRIMARY BIAS:** 🟢 {m["bullish"]}% | ⚪ {m["neutral"]}% | 🔴 {m["bearish"]}%
**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} {m["final_score"]}%

---

**⬛ 1. MACRO SNAPSHOT**

**PULSE SUMMARY:**
[LLM_INSERT_PULSE_SUMMARY_1_2_SENTENCES]

**I. ECONOMICS:** [🟢/⚪/🔴] (Score: {m["bullish"]} vs {m["bearish"]})

> **PRIMARY FUNDAMENTAL DRIVER: {self.data["macro_data"]["primary_driver"]["name"]}**
>
> *[LLM_INSERT_PRIMARY_DRIVER_STRUCTURAL_ANALYSIS_TIER_1]*
>
> *Mentor Commentary: [LLM_INSERT_PRIMARY_DRIVER_MENTOR_COMMENTARY_TIER_2]*
> ✅ [POST] | {timestamp} | [🟢/⚪/🔴]

**II. GEOPOLITICS / SENTIMENT:** [🟢/⚪/🔴]

> **SECONDARY MARKET CONDITION DRIVER: {self.data["macro_data"]["secondary_driver"]["name"]}**
>
> *[LLM_INSERT_SECONDARY_DRIVER_STRUCTURAL_ANALYSIS_TIER_1]*
>
> *Mentor Commentary: [LLM_INSERT_SECONDARY_DRIVER_MENTOR_COMMENTARY_TIER_2]*
> ✅ [POST] | Ongoing | [🟢/⚪/🔴]

---

**⬛ 2. MASTER PRICE LADDER**

▸ SUPPLY ZONES (RESISTANCE)
{sup_ladder}

📍 **SPOT: {self.spot:.5f}**

{dem_ladder}
▸ DEMAND ZONES (SUPPORT)

---

**⬛ 3. SUMMARY CHECKLIST**

> **Conviction:** [🟢/⚪/🔴] [LLM_INSERT_CONVICTION_LEVEL_LOW_MED_HIGH]
>
> **Actionable:** [LLM_INSERT_ACTIONABLE_RULES_TRIGGERS_INVALIDATION]
>
> **Logic:** [LLM_INSERT_SHORT_RECAP_STRUCTURAL_MACRO_ALIGNMENT]

---

**🛡️ DEVIL'S ADVOCATE BRIEFING:**
> *Mentor Commentary: [LLM_INSERT_UNFILTERED_ADVERSARIAL_CRITIQUE_AND_TRAP_WARNING]*
"""

        else:  # Default to TA2
            m = self.run_ta2_math()
            vol_bar = self.generate_bar(self.data["flow_data"]["volume_sell_pct"], self.data["flow_data"]["volume_buy_pct"])
            liq_bar = self.generate_bar(self.data["flow_data"]["liquidity_absorb_pct"], self.data["flow_data"]["liquidity_distribute_pct"], "🟢", "🔴")

            return f"""**ASSIST TRADER V2.1**
**{self.pair} ({self.pair})**
**TIMESTAMP:** {timestamp} (UTC+8)
**PRICE SOURCE:** {self.spot:.5f}
**YOUR BIAS: {self.user_bias}**
**FLOW STATE:** {m["res_type"]}
**CONVICTION MATRIX:** 🟢 {m["blend_bull"]}% | ⚪ {m["blend_neutral"]}% | 🔴 {m["blend_bear"]}%
**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} {m["final_score"]}%

---

### **📊 MODULE 1: DUAL FLOW ANALYSIS**

**VOLUME DELTA (H1):**
ㅤㅤㅤㅤ{self.data["flow_data"]["volume_sell_pct"]}% {vol_bar} {self.data["flow_data"]["volume_buy_pct"]}%
ㅤㅤㅤㅤSELLㅤㅤㅤ[NET: {"BULLISH" if m["vd_net"] >=0 else "BEARISH"} {m["vd_net"]:+}%]ㅤㅤBUY

**LIQUIDITY FLOW (H1):**
ㅤㅤㅤㅤ{self.data["flow_data"]["liquidity_absorb_pct"]}% {liq_bar} {self.data["flow_data"]["liquidity_distribute_pct"]}%
ㅤㅤㅤABSORBㅤㅤ[NET: {"BULLISH" if m["lf_net"] >=0 else "BEARISH"} {m["lf_net"]:+}%]ㅤDISTRIBUTE
                                            
**▸ FLOW INTERPRETATION:**
- **Delta Signal:** [LLM_INSERT_DELTA_SIGNAL_AGGRESSION_OR_EXHAUSTION]
- **Liquidity Signal:** [LLM_INSERT_LIQUIDITY_SIGNAL_WALLS_OR_VACUUMS]
- **Conflict Resolution:** {m["res_type"]}

---

### **🌐 MODULE 2: MACRO LAYERING**

**PRIMARY DRIVER: {self.data["macro_data"]["primary_driver"]["name"]}**

> [LLM_INSERT_FACTOR_1_STRUCTURAL_T1]
> ✅ **[IMPACT]: [LLM_INSERT_IMPACT_EMOJI_1]**
>
> *Mentor Commentary: [LLM_INSERT_COMMENTARY_1_T2]*

**SECONDARY DRIVER: {self.data["macro_data"]["secondary_driver"]["name"]}**

> [LLM_INSERT_FACTOR_2_STRUCTURAL_T1]
> ✅ **[IMPACT]: [LLM_INSERT_IMPACT_EMOJI_2]**
>
> *Mentor Commentary: [LLM_INSERT_COMMENTARY_2_T2]*

**▸ LAYER SYNTHESIS:**
> [LLM_INSERT_SYNTHESIS_SUMMARY_T1]
>
> *Mentor Commentary: [LLM_INSERT_SYNTHESIS_MENTOR_COMMENTARY_T2]*

---

### **📈 MODULE 3: DYNAMIC PRICE LADDER**

▸ SUPPLY ZONES (RESISTANCE)
{sup_ladder}

📍 **SPOT: {self.spot:.5f}** | **ZONE: [LLM_INSERT_ACTIVE_MARKET_ZONE_METRIC]**

{dem_ladder}
▸ DEMAND ZONES (SUPPORT)

---

### **⚡ MODULE 4: EXECUTION LOGIC & RISK**

**✅ SCENARIO A: STRUCTURE BULLISH PLAY**
- **Trigger:** [LLM_INSERT_BULLISH_TRIGGER_H1_PA_CLOSE_RULE]
- **Target:** [LLM_INSERT_BULLISH_TARGET_LEVEL] | **Risk:** [LLM_INSERT_BULLISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BULL_PROB]%
- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BULL_STOP_SHIELDING_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BULL_STOP_PHYSICS]

**❌ SCENARIO B: STRUCTURE BEARISH PLAY**
- **Trigger:** [LLM_INSERT_BEARISH_TRIGGER_H1_PA_CLOSE_RULE]
- **Target:** [LLM_INSERT_BEARISH_TARGET_LEVEL] | **Risk:** [LLM_INSERT_BEARISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BEAR_PROB]%
- **Stop-Loss Vulnerability Status:** [LLM_CHECK_BEAR_STOP_SHIELDING_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_EXPLAIN_BEAR_STOP_PHYSICS]

---

### **🛡️ DEVIL'S ADVOCATE (V2.1 ENHANCED)**
>
> * **The Pretension vs. Reality Check:** [LLM_INSERT_PRETENSION_V_REALITY]
> * **The Threat to Your Bias:** "If you go {self.user_bias}: [LLM_INSERT_THREAT_WARNING_TRAP_AND_CATALYST]."
> * **The Panic Mitigation:** "If you see [LLM_INSERT_PANIC_LEVEL_BREAK]: [LLM_INSERT_MITIGATION_RULES_TO_PREVENT_PANIC]."
> * **Core Truth:** [LLM_INSERT_CORE_TRUTH_PASSIVE_VS_ACTIVE_DEFENSE]
"""