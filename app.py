import streamlit as st
import datetime

import sys
import importlib

from google import genai
from google.genai import types
from engine import ReportEngine





# 1. Force the app into ultra-wide mode to support 3 columns comfortably
st.set_page_config(page_title="FX Quant Command Center", layout="wide")

st.title("📈 Forex Quantitative Engine (v2.1)")

# Initialize session states so data persists across refreshes
if "report_stream" not in st.session_state:
    st.session_state["report_stream"] = []  # Keeps a rolling history of all generated reports
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []   # Keeps mentor conversation separate

# ----------------------------------------------------
# 🖥️ 3-PANE LAYOUT CONFIGURATION
# ----------------------------------------------------
# Creates two main master columns: Left Controls/Chat (40% width) and Right Report Stream (60% width)
master_left, master_right = st.columns([2, 3])

# ====================================================
# 🎛️ LEFT MASTER COLUMN (CHANNELS PUSHED TO TOP)
# ====================================================
with master_left:
    
    # 🔑 PANE 1: AUTHENTICATION & CONFIG
    with st.expander("🔑 Authentication & Engine Config", expanded=False):
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
        if api_key:
            st.session_state["api_key"] = api_key
            
        # 🎚️ The AI Studio Thinking Slider
        # 0 means normal fast mode, steps up by 1024 tokens up to 8192
        thinking_budget = st.slider("🧠 Mentor Thinking Budget", min_value=0, max_value=8192, value=0, step=1024)
        
        # 🛠️ NEW: MANUAL ENGINE MAINTENANCE (Placed perfectly right under config)
    st.markdown("### 🛠️ Engine Maintenance")
    if st.button("🔄 Force Hard Code & Cache Reset", use_container_width=True):
        st.cache_data.clear()
        st.cache_resource.clear()
        if 'engine' in sys.modules:
            del sys.modules['engine']
        st.session_state["report_stream"] = []  # Wipes out stale UI reports hanging out in memory
        st.success("Cache obliterated & timeline cleared! Ready for fresh data feed...")
        st.rerun()

    # 👑 PANE 2: MENTOR CHAT (Right at the top of your visual workflow)
    st.markdown("### 💬 Mentor Chat")
    
    # Creates a fixed-height scrollable window specifically for the chat
    chat_container = st.container(height=350)
    with chat_container:
        if not st.session_state["chat_history"]:
            st.info("Ask a question below to start discussing your current setup.(Gemini 2.0 flash)")
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.write(msg["text"])
                
    user_query = st.chat_input("Ask a question about this setup...")
    if user_query:
        st.session_state["chat_history"].append({"role": "user", "text": user_query})
        
        if st.session_state["report_stream"]:
            latest_report = st.session_state["report_stream"][-1]
            client = genai.Client(api_key=api_key)
            
            # 🛠️ Dynamically build config based on your slider
            if thinking_budget > 0:
                config_args = types.GenerateContentConfig(
                    system_instruction="Discuss the report objectively. Keep answers brief, direct, and structured.",
                    thinking_config=types.ThinkingConfig(thinking_budget=thinking_budget)
                )
            else:
                # Standard fast execution mode
                config_args = types.GenerateContentConfig(
                    system_instruction="Discuss the report objectively. Keep answers brief, direct, and structured."
                )

            chat = client.chats.create(
                model="gemini-2.0-flash", 
                config=config_args
            )
            
            chat.send_message(f"Context report:\n{latest_report}")
            res = chat.send_message(user_query)
            st.session_state["chat_history"].append({"role": "mentor", "text": res.text})
        st.rerun()

    st.markdown("---")

    # 📊 PANE 3: LIVE MARKET INPUTS & ACTION BUTTON
    st.markdown("### ⚙️ Strategy Console")
    regular_pairs = ["AUDUSD","NZDUSD", "EURUSD", "GBPUSD", "USDCAD"]
    selected_option = st.selectbox("Currency Pair", regular_pairs + ["OTHER / CUSTOM"])
    if selected_option == "OTHER / CUSTOM":
        pair = st.text_input("Enter Custom Pair (e.g., EURGBP)", "").strip().upper()
    else:
        pair = selected_option.strip().upper()
    
    # Locate this section under '### ⚙️ Strategy Console' in your app.py
    user_bias = st.selectbox("Your Bias", ["NEUTRAL", "BULLISH", "BEARISH"])
    
    # NEW: Mode select toggle dropdown to choose between architecture lenses
    report_mode = st.selectbox("Select Report Execution Engine", ["Assist Trader v1.xx (ta)", "Assist Trader v2.xx (ta2)"])
    mode_tag = "TA" if "v1.xx" in report_mode else "TA2"
    
    generate_btn = st.button("⚡ Generate & Append Report", use_container_width=True)

    if generate_btn:
        if not api_key:
            st.error("Please expand '🔑 Authentication' at the top and enter your Gemini API Key.")
        else:
            with st.spinner("Processing engine state..."):
                try:
                   
                    from engine import ReportEngine
                    
                    # 🔍 DIAGNOSTIC CHECK: Read the raw data file directly from disk
                    with open("market_state.json", "r") as f:
                    raw_json_data = f.read()
                    st.sidebar.warning("📦 Raw JSON File Content Data:")
                    st.sidebar.code(raw_json_data, language="json")
                    # Instantiate Engine passing the dynamic inputs directly from the Streamlit UI frame
                    engine_instance = ReportEngine("market_state.json", live_pair=pair, live_bias=user_bias)
                    skeleton = engine_instance.generate_report_skeleton(report_mode=mode_tag)
                    
                    client = genai.Client(api_key=api_key)				
                    
                    # 🛡️ THE DEFINITIVE ANTI-ASSUMPTION GUARDRAIL SYSTEM
                    # Replace your old system_instruction string block with this exact configuration
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
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Populate this skeleton:\n\n{skeleton}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2
                        )
                    )
                    formatted_report = response.text.replace("\n", "  \n")
                    
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_report_block = f"## ⏱️ Report Generated at {timestamp}\n{formatted_report}\n\n---"
                    
                    st.session_state["report_stream"].append(new_report_block)
                    st.success(f"Appended {pair} Report to Stream!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Engine Error: {e}")

# ====================================================
# 📜 RIGHT MASTER COLUMN (PANE 4: THE REPORT STREAM)
# ====================================================
with master_right:
    st.markdown("### 📋 Historical Report Timeline")
    
    # Clear Stream Button if you want to wipe the slate clean
    if st.button("🗑️ Clear Timeline"):
        st.session_state["report_stream"] = []
        st.rerun()

    # Creates a dedicated, tall, independently scrollable viewport for the reports
    stream_container = st.container(height=750)
    with stream_container:
        if not st.session_state["report_stream"]:
            st.info("No reports generated yet. Use the Strategy Console on the left to trigger your quantitative engine.")
        else:
            # Display reports in reverse chronological order (newest at the top)
            for report in reversed(st.session_state["report_stream"]):
                st.markdown(report)