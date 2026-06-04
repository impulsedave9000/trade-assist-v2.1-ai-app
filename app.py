import streamlit as st
import datetime
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
# 🎛️ LEFT MASTER COLUMN (PANE 1 & PANE 2 - FIXING VARIABLE ORDER)
# ====================================================
with master_left:
    
    # 🔑 PANE 1: AUTHENTICATION (Defined first so Python sees it, but hidden inside a collapsed expander)
    with st.expander("🔑 Authentication", expanded=False):
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
        if api_key:
            st.session_state["api_key"] = api_key

    # 👑 PANE 2: MENTOR CHAT (Right at the top of your visual workflow)
    st.markdown("### 💬 Mentor Chat")
    
    # Creates a fixed-height scrollable window specifically for the chat
    chat_container = st.container(height=350)
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
            # Give the mentor context of the most recent report generated
            latest_report = st.session_state["report_stream"][-1]
            client = genai.Client(api_key=api_key)
            chat = client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction="Discuss the report objectively. Keep answers brief, direct, and structured."
                )
            )
            chat.send_message(f"Context report:\n{latest_report}")
            res = chat.send_message(user_query)
            st.session_state["chat_history"].append({"role": "assistant", "text": res.text})
        else:
            st.session_state["chat_history"].append({"role": "assistant", "text": "Please generate a market report first so I have data to analyze with you."})
        st.rerun()

    st.markdown("---")

    # 📊 PANE 3: LIVE MARKET INPUTS & ACTION BUTTON
    st.markdown("### ⚙️ Strategy Console")
    pair = st.text_input("Currency Pair", "AUDUSD").strip().upper()
    user_bias = st.selectbox("Your Bias", ["NEUTRAL", "BULLISH", "BEARISH"])
    
    generate_btn = st.button("⚡ Generate & Append Report", use_container_width=True)

    if generate_btn:
        if not api_key:
            st.error("Please expand '🔑 Authentication' at the top and enter your Gemini API Key.")
        else:
            with st.spinner("Processing engine state..."):
                try:
                    engine = ReportEngine("market_state.json")
                    skeleton = engine.generate_report_skeleton()
                    
                    client = genai.Client(api_key=api_key)
                    system_instruction = """
                    You are a Senior, cold-blooded Quantitative Forex Analyst and trading mentor.
                    Fill out the bracketed placeholders exactly. Do not alter the calculations, percentages, graphic bars, or ladders.
                    """
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=f"Populate this skeleton:\n\n{skeleton}",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.2
                        )
                    )
                    
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_report_block = f"## ⏱️ Report Generated at {timestamp}\n{response.text}\n\n---"
                    
                    st.session_state["report_stream"].append(new_report_block)
                    st.success(f"Appended {pair} Report to Stream!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Engine Error: {e}")

    st.markdown("---")

    # 🔑 PANE 3: AUTHENTICATION (Moved to the bottom since it's "set-and-forget")
    with st.expander("🔑 Authentication", expanded=False):  # Set expanded=False to keep it collapsed and clean
        api_key = st.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
        if api_key:
            st.session_state["api_key"] = api_key

# ====================================================
# 📜 RIGHT MASTER COLUMN (PANE 3: THE REPORT STREAM)
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
            st.info("No reports generated yet. Use the Control Panel on the left to trigger your quantitative engine.")
        else:
            # Display reports in reverse chronological order (newest at the top)
            # Switch to `for report in st.session_state["report_stream"]:` if you want oldest first!
            for report in reversed(st.session_state["report_stream"]):
                st.markdown(report)