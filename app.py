import streamlit as st
import datetime
import sys
import json
import importlib
from google import genai
from google.genai import types

st.set_page_config(page_title="FX Quant Command Center", layout="wide")
st.title("📈 Forex Quantitative Engine (v2.1)")

if "report_stream" not in st.session_state:
    st.session_state["report_stream"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

master_left, master_right = st.columns([2, 3])

with master_left:
    # 🔑 COLLAPSIBLE CONTROL PANE: Keeps mobile screen vertical clean
    with st.expander("🔑 Authentication & Engine Config", expanded=False):
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
        if api_key:
            st.session_state["api_key"] = api_key
        
        # 🎛️ INTENSITY DIAL: Lets trader toggle security stance instantly
        val_mode = st.radio("Validation Guardrail Stance", ["Strict Accuracy Hold", "Flexible Base-Fill Mode"], index=0)
        
        st.markdown("---")
        if st.button("🔄 Force Core Memory & Cache Reset", use_container_width=True):
            st.cache_data.clear()
            st.cache_resource.clear()
            if 'engine' in sys.modules:
                del sys.modules['engine']
            st.session_state["report_stream"] = []
            st.success("Memory scrubbed successfully!")
            st.rerun()

    st.markdown("### 💬 Mentor Chat")
    chat_container = st.container(height=300)
    with chat_container:
        if not st.session_state["chat_history"]:
            st.info("Ask a question below to start discussing your current setup.")
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])
                
    user_query = st.chat_input("Ask a question about this setup...")
    if user_query:
        st.session_state["chat_history"].append({"role": "user", "text": user_query})
        if st.session_state["report_stream"]:
            latest_report = st.session_state["report_stream"][-1]
            client = genai.Client(api_key=api_key)
            config_args = types.GenerateContentConfig(
                system_instruction="Discuss the report objectively. Keep answers brief, direct, and structured.",
            )
            chat = client.chats.create(model="gemini-2.0-flash", config=config_args)
            chat.send_message(f"Context report:\n{latest_report}")
            res = chat.send_message(user_query)
            st.session_state["chat_history"].append({"role": "mentor", "text": res.text})
        st.rerun()

    st.markdown("---")

    st.markdown("### ⚙️ Strategy Console")
    regular_pairs = ["AUDUSD", "NZDUSD", "EURUSD", "GBPUSD", "USDCAD"]
    selected_option = st.selectbox("Currency Pair", regular_pairs + ["OTHER / CUSTOM"])
    pair = st.text_input("Enter Custom Pair", "").strip().upper() if selected_option == "OTHER / CUSTOM" else selected_option.strip().upper()
    
    user_bias = st.selectbox("Your Bias", ["NEUTRAL", "BULLISH", "BEARISH"])
    report_mode = st.selectbox("Select Report Execution Engine", ["Assist Trader v1.xx (ta)", "Assist Trader v2.xx (ta2)"])
    mode_tag = "TA" if "v1.xx" in report_mode else "TA2"
    
    generate_btn = st.button("⚡ Generate & Append Report", use_container_width=True)

    if generate_btn:
        if not api_key:
            st.error("Please expand '🔑 Authentication' at the top and enter your Gemini API Key.")
        else:
            with st.spinner("Executing real-time grounding matrix retrieval..."):
                try:
                    client = genai.Client(api_key=api_key)
                    
                    search_prompt = """
Execute a real-time web search query for current market conditions regarding the currency pair. 
Return your findings strictly as a single, unquoted raw JSON dictionary. 
Do not wrap it in markdown block code wrappers.

JSON Schema Required:
{
    "spot_price": 0.71320,
    "quote_time_utc": "YYYY-MM-DD HH:MM:SS",
    "flow_data": {
        "volume_buy_pct": 50,
        "volume_sell_pct": 50,
        "liquidity_absorb_pct": 50,
        "liquidity_distribute_pct": 50
    },
    "macro_data": {
        "primary_driver": {
            "name": "Central Bank Interest Rate Divergence",
            "bullish_pct": 30,
            "bearish_pct": 30
        },
        "secondary_driver": {
            "name": "Global Risk Sentiment Dynamics",
            "bullish_pct": 20,
            "bearish_pct": 20
        }
    },
    "price_levels": {
        "supply": [
            {"price": 0.71850, "timeframe": "H1", "label": "Order Block Resistance", "probability": "HIGH", "flow_note": "Supply Wall Defended"},
            {"price": 0.72500, "timeframe": "D1", "label": "HTF Technical Cluster", "probability": "MED", "flow_note": "Stale Rest-Lids"}
        ],
        "demand": [
            {"price": 0.71100, "timeframe": "H1", "label": "Dynamic Bid Block", "probability": "HIGH", "flow_note": "Cushion Density Thick"},
            {"price": 0.70400, "timeframe": "W1", "label": "HTF Trend Baseline", "probability": "LOW", "flow_note": "Liquidity Pool Floor"}
        ]
    }
}
""" 
                    
                    search_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=search_prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            tools=[types.Tool(google_search=types.GoogleSearch())]
                        )
                    )
                    
                    clean_json_txt = search_response.text.strip().replace("```json", "").replace("```", "")
                    payload = json.loads(clean_json_txt)
                    
                    # 🛡️ THE DETERMINISTIC STRUCTURAL VALIDATOR
                    errors = []
                    
                    # Check 1: Numeric validations
                    if not isinstance(payload.get("spot_price"), (int, float)) or payload["spot_price"] <= 0:
                        errors.append(f"Invalid or missing spot_price: {payload.get('spot_price')}")
                    
                    fd = payload.get("flow_data", {})
                    v_buy = fd.get("volume_buy_pct", 0)
                    v_sell = fd.get("volume_sell_pct", 0)
                    l_abs = fd.get("liquidity_absorb_pct", 0)
                    l_dist = fd.get("liquidity_distribute_pct", 0)
                    
                    # Check 2: Mathematical 100% Bound Sum Constraints
                    if (v_buy + v_sell) != 100:
                        if "Strict" in val_mode:
                            errors.append(f"Volume Sum Error: Buy ({v_buy}%) + Sell ({v_sell}%) = {v_buy+v_sell}% (Must be 100%)")
                        else:
                            payload["flow_data"]["volume_buy_pct"], payload["flow_data"]["volume_sell_pct"] = 50, 50
                            
                    if (l_abs + l_dist) != 100:
                        if "Strict" in val_mode:
                            errors.append(f"Liquidity Sum Error: Absorb ({l_abs}%) + Distribute ({l_dist}%) = {l_abs+l_dist}% (Must be 100%)")
                        else:
                            payload["flow_data"]["liquidity_absorb_pct"], payload["flow_data"]["liquidity_distribute_pct"] = 50, 50

                    # ☕ EXCEPTION ROUTER: Refuses to pass broken arrays to core calculations
                    if errors:
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_lines = "\n".join([f"* ❌ {err}" for err in errors])
                        coffee_alert = f"""## ⏱️ Evaluation Attempted at {timestamp}
> ### ⚠️ ENGINE WARNING: SYSTEM DETECTED DATA INTEGRITY BREAKDOWN
> * **Status:** Network Search Grounding returned incomplete or unbalanced matrix components.
> * **Action:** To protect capital and maintain absolute math accuracy, the execution engine has aborted.
> * **Reason:** *Patience Advantage Active: Volatility spike or fragmented institutional order tape detected. Chill, have a coffee, and let the market settle.*
>
> ### 📊 GROUNDED META-DATA LOGS:
{log_lines}
---"""
                        st.session_state["report_stream"].append(coffee_alert)
                        st.warning("Data validation failed. Aborted safely to timeline.")
                        st.rerun()

                    # Phase 2: Execution Core (Math Processing via Isolated Python Engine)
                    if 'engine' in sys.modules:
                        del sys.modules['engine']
                    import engine
                    importlib.reload(engine)
                    from engine import ReportEngine
                    
                    engine_instance = ReportEngine(payload, live_pair=pair, live_bias=user_bias)
                    skeleton = engine_instance.generate_report_skeleton(report_mode=mode_tag)
                    
                    # Phase 3: Analytical Population via Strict System Prompts
                    system_instruction = """
                    You are a Senior, cold-blooded Quantitative Forex Analyst and trading mentor operating with a 16-year market perspective (trading since 2008). Your single remaining duty is to populate the string-bracketed placeholders (e.g., [LLM_INSERT_X]) embedded inside the provided skeleton file.
                    CRITICAL OPERATIONAL RULES:
                    1. NO CALCULATION ATTEMPTS: The numerical values, conviction matrices, progress bars, and pip distances are already pre-calculated, frozen, and hardcoded in the skeleton by a sterile Python calculation core. You are strictly forbidden from changing, re-calculating, or shifting any of these fixed coordinates.
                    2. ANTI-SYCOPHANCY RULE: Do not manipulate language to flatter the user's bias ("YOUR BIAS"). If the hardcoded confluenced bias is contradictory to what the user wants, you must expose this trap mercilessly inside the DEVIL'S ADVOCATE briefing module.
                    3. THE TWO-TIER TRANSLATION FRAMEWORK:
                       - Tier 1 Sections (labeled _T1 or _STRUCTURAL): Write in formal, precise, professional quantitative language stripped of standard media fluff.
                       - Tier 2 Commentary Sections (labeled _T2 or _MENTOR): Write in plain-English, casual, direct remarks from an experienced mentor. Translate the raw numbers into physical order book concepts using ONLY our specific vocabulary: "Big Boys" (Institutions), "Retail" (Trapped herd), "Cushions/Floors" (Support), and "Ceilings/Lids/Roadblocks" (Resistance). Always wrap Tier 2 text completely in italics (*text*).
                    4. MOBILE LAYOUT PROTECTION: Keep all bullet points stacked vertically. Never introduce nested list indicators (such as "- -"). Use clean single carriage returns to hold your comments next to the ladder items.
                    5. CAPITAL PROTECTION: The vocabulary in the execution logic scenarios must analyze stop placement relative to the 25-pip stop boundary. Flag whether the stop is "Shielded" behind the big boys' resting limit blocks or completely "Exposed" to quick liquidity sweeps.
                    """
                    
                    report_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Populate this structural template skeleton precisely:\n\n{skeleton}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2
                        )
                    )
                    
                    formatted_report = report_response.text.replace("\n", "  \n")
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_report_block = f"## ⏱️ Report Generated at {timestamp}\n{formatted_report}\n\n---"
                    
                    st.session_state["report_stream"].append(new_report_block)
                    st.success(f"Appended {pair} Report to Stream!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Engine Error: {e}")

with master_right:
    st.markdown("### 📋 Historical Report Timeline")
    if st.button("🗑️ Clear Timeline"):
        st.session_state["report_stream"] = []
        st.rerun()

    stream_container = st.container(height=750)
    with stream_container:
        if not st.session_state["report_stream"]:
            st.info("No reports generated yet. Use the Strategy Console on the left to trigger your quantitative engine.")
        else:
            for report in reversed(st.session_state["report_stream"]):
                st.markdown(report)