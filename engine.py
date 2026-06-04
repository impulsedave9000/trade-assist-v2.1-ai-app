import json
from datetime import datetime

class ReportEngine:
    def __init__(self, data_dict, live_pair=None, live_bias=None):
        self.data = data_dict
        self.pair = live_pair if live_pair else "AUDUSD"
        self.user_bias = live_bias if live_bias else "NEUTRAL"
        self.spot = self.data.get("spot_price", 0.0)
        
        # Dual-Time Staleness Whistle-Blower Setup
        self.quote_time_str = self.data.get("quote_time_utc", "")
        self.time_delta_mins = 0.0
        if self.quote_time_str:
            try:
                quote_dt = datetime.strptime(self.quote_time_str, "%Y-%m-%d %H:%M:%S")
                current_dt = datetime.utcnow()
                self.time_delta_mins = abs((current_dt - quote_dt).total_seconds()) / 60.0
            except Exception:
                self.time_delta_mins = 0.0

    def generate_bar(self, left_pct, right_pct):
        """Strict Part 4, Rule 7: Always exactly 10 characters using only Red and Green"""
        total = left_pct + right_pct
        if total == 0:
            return "[🔴🔴🔴🔴🔴 Greenland]"
        left_count = int(round((left_pct / total) * 10))
        left_count = max(0, min(10, left_count))
        right_count = 10 - left_count
        return f"[{'🔴' * left_count}{'🟢' * right_count}]"

    def get_staleness_banner(self):
        """Generates concise warnings directly below the main header text"""
        if self.time_delta_mins > 30.0:
            return f"⚠️ **CRITICAL FLAG: LAGGING TAPE DETECTED ({int(self.time_delta_mins)} MINS OLD)**\n> *Notice: Institutional data stream exceeds your macro threshold. Cross-reference manually with your active execution terminal.*\n\n"
        elif self.time_delta_mins >= 5.0:
            return f"⚠️ **WARNING: AGING TAPE ALERT ({int(self.time_delta_mins)} MINS OLD)**\n> *Notice: Resting limit blocks may have shifted relative to H1 chart close.*\n\n"
        return ""

    def run_ta_math(self):
        md = self.data.get("macro_data", {})
        econ = md.get("primary_driver", {})
        sent = md.get("secondary_driver", {})

        econ_bull = econ.get("bullish_pct", 0.0)
        econ_bear = econ.get("bearish_pct", 0.0)
        econ_neut = max(0.0, 100.0 - econ_bull - econ_bear)
        
        sent_bull = sent.get("bullish_pct", 0.0)
        sent_bear = sent.get("bearish_pct", 0.0)
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

    def run_ta_math(self):
        md = self.data.get("macro_data", {}) if self.data.get("macro_data") else {}
        econ = md.get("primary_driver", {}) if md.get("primary_driver") else {}
        sent = md.get("secondary_driver", {}) if md.get("secondary_driver") else {}

        # Hardened Float Extraction Safety Gates
        econ_bull = float(econ.get("bullish_pct") or 0.0)
        econ_bear = float(econ.get("bearish_pct") or 0.0)
        econ_neut = max(0.0, 100.0 - econ_bull - econ_bear)
        
        sent_bull = float(sent.get("bullish_pct") or 0.0)
        sent_bear = float(sent.get("bearish_pct") or 0.0)
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
        fd = self.data.get("flow_data", {}) if self.data.get("flow_data") else {}
        md = self.data.get("macro_data", {}) if self.data.get("macro_data") else {}

        # Hardened Float Extraction Safety Gates
        vol_buy = float(fd.get("volume_buy_pct") or 50.0)
        vol_sell = float(fd.get("volume_sell_pct") or 50.0)
        liq_abs = float(fd.get("liquidity_absorb_pct") or 50.0)
        liq_dist = float(fd.get("liquidity_distribute_pct") or 50.0)

        flow_bull = (vol_buy + liq_abs) / 2.0
        flow_bear = (vol_sell + liq_dist) / 2.0
        flow_neutral = 100.0 - flow_bull - flow_bear

        prim = md.get("primary_driver", {}) if md.get("primary_driver") else {}
        sec = md.get("secondary_driver", {}) if md.get("secondary_driver") else {}
        
        macro_bull = (float(prim.get("bullish_pct") or 0.0) * 0.70) + (float(sec.get("bullish_pct") or 0.0) * 0.30)
        macro_bear = (float(prim.get("bearish_pct") or 0.0) * 0.70) + (float(sec.get("bearish_pct") or 0.0) * 0.30)
        macro_neutral = 100.0 - macro_bull - macro_bear

        blend_bull = (flow_bull * 0.50) + (macro_bull * 0.50)
        blend_bear = (flow_bear * 0.50) + (macro_bear * 0.50)
        blend_neutral = 100.0 - blend_bull - blend_bear

        vd_net = vol_buy - vol_sell
        lf_net = liq_abs - liq_dist

        resolution_type = "TRUE TREND"
        
        if (vd_net > 20 and lf_net < -20) or (vd_net < -20 and lf_net > 20):
            resolution_type = "ABSORPTION TRAP"
            if blend_bull > blend_bear:
                blend_bull = max(0.0, blend_bull - 15.0)
            else:
                blend_bear = max(0.0, blend_bear - 15.0)
            blend_neutral += 15.0
        elif abs(vd_net) <= 10 and abs(lf_net) <= 10:
            resolution_type = "VACUUM DRIFT"
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
            "vd_net": vd_net, "lf_net": lf_net, "res_type": resolution_type,
            "blend_bull": rbull, "blend_bear": rbear, "blend_neutral": rneut,
            "final_bias": final_bias, "final_emoji": final_emoji, "final_score": final_score
        }

    def compile_price_ladder_v12(self):
        supply = sorted(self.data.get("price_levels", {}).get("supply", []), key=lambda x: x["price"], reverse=True)
        demand = sorted(self.data.get("price_levels", {}).get("demand", []), key=lambda x: x["price"], reverse=True)

        supply_lines = []
        for s in supply:
            pips = int(round((s["price"] - self.spot) * 10000))
            if abs(pips) <= 120:
                sign = "+" if pips >= 0 else ""
                supply_lines.append(f'> {s["price"]:.5f} ▲ {s["timeframe"]} {s["label"]} [{sign}{pips}pips]')

        demand_lines = []
        for d in demand:
            pips = int(round((d["price"] - self.spot) * 10000))
            if abs(pips) <= 120:
                demand_lines.append(f'> {d["price"]:.5f} ▼ {d["timeframe"]} {d["label"]} [{pips}pips]')

        return "\n".join(supply_lines), "\n".join(demand_lines)

    def compile_price_ladder_v21(self):
        supply = sorted(self.data.get("price_levels", {}).get("supply", []), key=lambda x: x["price"], reverse=True)
        demand = sorted(self.data.get("price_levels", {}).get("demand", []), key=lambda x: x["price"], reverse=True)

        supply_lines = []
        for s in supply:
            pips = int(round((s["price"] - self.spot) * 10000))
            if abs(pips) <= 120:
                sign = "+" if pips >= 0 else ""
                prob = s.get("probability", "MED")
                icon = "🔥" if prob == "HIGH" else ("💧" if prob == "MED" else "❄️")
                comment = s.get("flow_note", "Resting Limits")
                supply_lines.append(f'> {s["price"]:.5f} ▲ {s["timeframe"]} {s["label"]} [ {sign}{pips}pips ] | **Prob: [{prob}]** {icon} **Comment: [{comment}]**')

        demand_lines = []
        for d in demand:
            pips = int(round((d["price"] - self.spot) * 10000))
            if abs(pips) <= 120:
                prob = d.get("probability", "MED")
                icon = "🔥" if prob == "HIGH" else ("💧" if prob == "MED" else "❄️")
                comment = d.get("flow_note", "Resting Bids")
                demand_lines.append(f'> {d["price"]:.5f} ▼ {d["timeframe"]} {d["label"]} [ {pips}pips ] | **Prob: [{prob}]** {icon} **Comment: [{comment}]**')

        return "\n".join(supply_lines), "\n".join(demand_lines)

    def generate_report_skeleton(self, report_mode="TA2"):
        timestamp_local = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")
        warning_banner = self.get_staleness_banner()

        if report_mode.upper() == "TA":
            m = self.run_ta_math()
            sup_ladder, dem_ladder = self.compile_price_ladder_v12()
            
            return f"""**ASSIST TRADER V1.2**
**{self.pair} ({self.pair})**
**TIMESTAMP:** {timestamp_local} (UTC+8)
**PRICE SOURCE:** {self.spot:.5f}

**YOUR BIAS: {self.user_bias} [{"🟢" if "BULL" in self.user_bias.upper() else ("🔴" if "BEAR" in self.user_bias.upper() else "⚪")}] (Weight: 15%)**
**PRIMARY BIAS:** 🟢 {m["bullish"]}% | ⚪ {m["neutral"]}% | 🔴 {m["bearish"]}%
**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} [{m["final_score"]}%]

---

{warning_banner}**⬛ 1. MACRO SNAPSHOT**

**PULSE SUMMARY:**
[LLM_INSERT_PULSE_SUMMARY_1_TO_2_SENTENCES]

**I. ECONOMICS:** [LLM_INSERT_ECON_STATUS_EMOJI] (Score: [LLM_INSERT_ECON_SCORE_0_100])

> **[LLM_INSERT_ECON_FACTOR_1_TITLE]**
>
> *Mentor Commentary: [LLM_INSERT_ECON_FACTOR_1_MENTOR_COMMENTARY]*
> ✅ [POST] | [LLM_INSERT_ECON_FACTOR_1_TIMESTAMP] | [LLM_INSERT_ECON_FACTOR_1_EMOJI] [[LLM_INSERT_ECON_FACTOR_1_WEIGHT]%]

> **[LLM_INSERT_ECON_FACTOR_2_TITLE]**
>
> *Mentor Commentary: [LLM_INSERT_ECON_FACTOR_2_MENTOR_COMMENTARY]*
> ✅ [POST] | [LLM_INSERT_ECON_FACTOR_2_TIMESTAMP] | [LLM_INSERT_ECON_FACTOR_2_EMOJI] [[LLM_INSERT_ECON_FACTOR_2_WEIGHT]%]

**II. GEOPOLITICS / SENTIMENT:** [LLM_INSERT_SENT_STATUS_EMOJI] (Score: [LLM_INSERT_SENT_SCORE_0_100])

> **[LLM_INSERT_SENT_FACTOR_1_TITLE]**
>
> *Mentor Commentary: [LLM_INSERT_SENT_FACTOR_1_MENTOR_COMMENTARY]*
> ✅ [POST] | [LLM_INSERT_SENT_FACTOR_1_TIMESTAMP] | [LLM_INSERT_SENT_FACTOR_1_EMOJI] [[LLM_INSERT_SENT_FACTOR_1_WEIGHT]%]

> **[LLM_INSERT_SENT_FACTOR_2_TITLE]**
>
> *Mentor Commentary: [LLM_INSERT_SENT_FACTOR_2_MENTOR_COMMENTARY]*
> ✅ [POST] | [LLM_INSERT_SENT_FACTOR_2_TIMESTAMP] | [LLM_INSERT_SENT_FACTOR_2_EMOJI] [[LLM_INSERT_SENT_FACTOR_2_WEIGHT]%]

---

**⬛ 2. MASTER PRICE LADDER**

**I. HTF MAP:**

> **Weekly (W1):** [LLM_CURATE_IMPACTFUL_W1_LEVELS_WITH_CONVICTION_LABELS]

> **Daily (D1):** [LLM_CURATE_IMPACTFUL_D1_LEVELS_WITH_CONVICTION_LABELS]

> **Hourly (H1):** [LLM_CURATE_IMPACTFUL_H1_LEVELS_WITH_CONVICTION_LABELS]

**II. ACTIVE LADDER:**
{sup_ladder}
> 📍 SPOT: {self.spot:.5f}
{dem_ladder}

---

**⬛ 3. SUMMARY CHECKLIST**

> **Conviction:** [LLM_INSERT_CONVICTION_EMOJI] [Low / Medium / High]
>
> **Actionable:** [LLM_INSERT_ACTIONABLE_RULES_AND_LEVELS]
>
> **Logic:** [LLM_INSERT_SHORT_RECAP_ALIGNMENT_OR_CONFLICT]

---

**🛡️ DEVIL'S ADVOCATE BRIEFING:**
> *Mentor Commentary: [LLM_INSERT_DEVILS_ADVOCATE_UNFILTERED_MENTOR_CRITIQUE]*"""

        else:
            m = self.run_ta2_math()
            sup_ladder, dem_ladder = self.compile_price_ladder_v21()
            
            vol_sell = self.data.get("flow_data", {}).get("volume_sell_pct", 50)
            vol_buy = self.data.get("flow_data", {}).get("volume_buy_pct", 50)
            liq_abs = self.data.get("flow_data", {}).get("liquidity_absorb_pct", 50)
            liq_dist = self.data.get("flow_data", {}).get("liquidity_distribute_pct", 50)
            
            vol_bar = self.generate_bar(vol_sell, vol_buy)
            liq_bar = self.generate_bar(liq_abs, liq_dist)

            return f"""**ASSIST TRADER V2.1**
**{self.pair} ({self.pair})**
**TIMESTAMP:** {timestamp_local} (UTC+8)
**PRICE SOURCE:** {self.spot:.5f}

**YOUR BIAS: {self.user_bias}**
**FLOW STATE:** {m["res_type"]}
**CONVICTION MATRIX:** 🟢 {m["blend_bull"]}% | ⚪ {m["blend_neutral"]}% | 🔴 {m["blend_bear"]}%
**CONFLUENCED BIAS:** {m["final_bias"]} {m["final_emoji"]} [{m["final_score"]}%]

---

{warning_banner}### **📊 MODULE 1: DUAL FLOW ANALYSIS**

**VOLUME DELTA (H1):**
{vol_sell}% {vol_bar} {vol_buy}%
SELL ㅤㅤ [NET: {"BULLISH" if m["vd_net"] >=0 else "BEARISH"} {m["vd_net"]:+}%] ㅤ BUY

**LIQUIDITY FLOW (H1):**
{liq_abs}% {liq_bar} {liq_dist}%
ABSORB  [NET: {"BULLISH" if m["lf_net"] >=0 else "BEARISH"} {m["lf_net"]:+}%] ㅤ DISTRIBUTE
(BULL)                                            (BEAR)

**▸ FLOW INTERPRETATION:**
- **Delta Signal:** [LLM_INSERT_DELTA_SIGNAL_AGGRESSION_OR_EXHAUSTION]
- **Liquidity Signal:** [LLM_INSERT_LIQUIDITY_SIGNAL_WALLS_OR_VACUUMS]
- **Conflict Resolution:** {m["res_type"]}

---

### **🌐 MODULE 2: MACRO LAYERING**

**PRIMARY DRIVER: {self.data.get("macro_data", {}).get("primary_driver", {}).get("name", "Interest Rate Divergence")}**

>**[LLM_INSERT_MACRO_FACTOR_1_NAME]**
>[LLM_INSERT_MACRO_FACTOR_1_TEXT]
>✅ [IMPACT]: [LLM_INSERT_MACRO_FACTOR_1_EMOJI] [[LLM_INSERT_MACRO_FACTOR_1_WEIGHT]%]
>
>*Mentor Commentary: [LLM_INSERT_MACRO_FACTOR_1_MENTOR_COMMENTARY]*

>**[LLM_INSERT_MACRO_FACTOR_2_NAME]**
>[LLM_INSERT_MACRO_FACTOR_2_TEXT]
>✅ [IMPACT]: [LLM_INSERT_MACRO_FACTOR_2_EMOJI] [[LLM_INSERT_MACRO_FACTOR_2_WEIGHT]%]
>
>*Mentor Commentary: [LLM_INSERT_MACRO_FACTOR_2_MENTOR_COMMENTARY]*

**SECONDARY DRIVER: MARKET CONDITIONS**

>**[LLM_INSERT_MACRO_FACTOR_3_NAME]**
>[LLM_INSERT_MACRO_FACTOR_3_TEXT]
>✅ [IMPACT]: [LLM_INSERT_MACRO_FACTOR_3_EMOJI] [[LLM_INSERT_MACRO_FACTOR_3_WEIGHT]%]
>
>*Mentor Commentary: [LLM_INSERT_MACRO_FACTOR_3_MENTOR_COMMENTARY]*

>**[LLM_INSERT_MACRO_FACTOR_4_NAME]**
>[LLM_INSERT_MACRO_FACTOR_4_TEXT]
>✅ [IMPACT]: [LLM_INSERT_MACRO_FACTOR_4_EMOJI] [[LLM_INSERT_MACRO_FACTOR_4_WEIGHT]%]
>
>*Mentor Commentary: [LLM_INSERT_MACRO_FACTOR_4_MENTOR_COMMENTARY]*

**▸ LAYER SYNTHESIS:**
>[LLM_INSERT_MACRO_LAYER_SYNTHESIS_SUMMARY]
>*Mentor Commentary: [LLM_INSERT_MACRO_SYNTHESIS_MENTOR_TRANSLATION_PLAIN_ENGLISH]*

---

### **📈 MODULE 3: DYNAMIC PRICE LADDER**

▸ SUPPLY ZONES (RESISTANCE)
{sup_ladder}

📍 **SPOT: {self.spot:.5f}** | **ZONE: [LLM_INSERT_ACTIVE_MARKET_ZONE_POSITION]**

{dem_ladder}
▸ DEMAND ZONES (SUPPORT)

---

### **⚡ MODULE 4: EXECUTION LOGIC & RISK**

**✅ SCENARIO A: STRUCTURE BULLISH PLAY**
- **Trigger:** [LLM_INSERT_BULLISH_TRIGGER_CONDITIONS]
- **Target:** [LLM_INSERT_BULLISH_TARGET_PRICE] | **Risk:** [LLM_INSERT_BULLISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BULLISH_PROBABILITY]%
- **Stop-Loss Vulnerability Status:** [LLM_INSERT_BULLISH_SL_STATUS_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_INSERT_BULLISH_SL_STRUCTURAL_PHYSICS]

**❌ SCENARIO B: STRUCTURE BEARISH PLAY**
- **Trigger:** [LLM_INSERT_BEARISH_TRIGGER_CONDITIONS]
- **Target:** [LLM_INSERT_BEARISH_TARGET_PRICE] | **Risk:** [LLM_INSERT_BEARISH_FLOW_RISK] | **Probability:** [LLM_INSERT_BEARISH_PROBABILITY]%
- **Stop-Loss Vulnerability Status:** [LLM_INSERT_BEARISH_SL_STATUS_SHIELDED_OR_EXPOSED] relative to USER_SL (25 pips) | **Note:** [LLM_INSERT_BEARISH_SL_STRUCTURAL_PHYSICS]

---

### **🛡️ DEVIL'S ADVOCATE (V2.1 ENHANCED)**
>
> * **The Pretension vs. Reality Check:** [LLM_INSERT_WHAT_MARKET_IS_FAKING_VS_WHAT_BIG_BOYS_ARE_DOING]
> * **The Threat to Your Bias:** "If you go {self.user_bias}: [LLM_INSERT_EXACT_TRAP_AND_CATALYST_WARNING]."
> * **The Panic Mitigation:** "If you see [LLM_INSERT_PANIC_INVALIDATION_LEVEL]: [LLM_INSERT_EXACT_RULES_TO_PREVENT_EMOTIONAL_PANIC]."
> * **Core Truth:** [LLM_INSERT_SUMMARY_OF_PASSIVE_VS_ACTIVE_LIMIT_DEFENSE]"""