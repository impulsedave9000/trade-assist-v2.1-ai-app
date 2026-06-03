import streamlit as st
import json
from google import genai
from google.genai import types
from engine import ReportEngine

st.set_page_config(page_title="FX Report Engine", layout="wide")

st.title("📈 Forex Quantitative Engine (v2.1)")

# Sidebar for Setup & API Key
st.sidebar.header("🔑 Authentication")
api_key = st.sidebar.text_input("Gemini API Key", type="password", value=st.session_state.get("api_key", ""))
if api_key:
    st.session_state["api_key"] = api_key

# 1. Inputs (Replaces manual JSON editing)
st.subheader("📊 Live Market Inputs")
col1, col2 = st.columns(2)

with col1:
    pair = st.text_input("Currency Pair", "AUDUSD")
    spot_price = st.number_input("Current Spot Price", value=0.65420, format="%.5f")
    user_bias = st.selectbox("Your Bias", ["BULLISH", "BEARISH", "NEUTRAL"])

with col2:
    vol_buy = st.slider("Volume Buy %", 0, 100, 65)
    vol_sell = 100 - vol_buy
    st.caption(f"Volume Sell: {vol_sell}%")
    
    liq_absorb = st.slider("Liquidity Absorb %", 0, 100, 30)
    liq_dist = 100 - liq_absorb
    st.caption(f"Liquidity Distribute: {liq_dist}%")

# Create temporary JSON state
state = {
    "pair": pair,
    "spot_price": spot_price,
    "user_bias": user_bias,
    "model_type": "ta2",
    "flow_data": {
        "volume_buy_pct": vol_buy,
        "volume_sell_pct": vol_sell,
        "liquidity_absorb_pct": liq_absorb,
        "liquidity_distribute_pct": liq_dist
    },
    "macro_data": {
        "primary_driver": {
            "name": st.text_input("Primary Driver", "RBA Hawkish Hold"),
            "bullish_pct": st.slider("Primary Bullish %", 0, 100, 80),
            "bearish_pct": 0 # Handled programmatically
        },
        "secondary_driver": {
            "name": st.text_input("Secondary Driver", "DXY Profit Taking"),
            "bullish_pct": st.slider("Secondary Bullish %", 0, 100, 60),
            "bearish_pct": 0
        }
    },
    "price_levels": {
        "supply": [
            {"price": spot_price + 0.0050, "timeframe": "H1", "label": "Unmitigated OB", "probability": "HIGH", "icon": "🔥"},
            {"price": spot_price + 0.0025, "timeframe": "D1", "label": "Daily Range High", "probability": "MED", "icon": "💧"}
        ],
        "demand": [
            {"price": spot_price - 0.0025, "timeframe": "H1", "label": "Resting Bid Wall", "probability": "HIGH", "icon": "🔥"},
            {"price": spot_price - 0.0050, "timeframe": "W1", "label": "Weekly Key Support", "probability": "LOW", "icon": "❄"}
        ]
    }
}

# Math adjustments for JSON format
state["macro_data"]["primary_driver"]["bearish_pct"] = 100 - state["macro_data"]["primary_driver"]["bullish_pct"]
state["macro_data"]["secondary_driver"]["bearish_pct"] = 100 - state["macro_data"]["secondary_driver"]["bullish_pct"]

# Save temporary state file
with open("temp_state.json", "w") as f:
    json.dump(state, f)

if st.button("⚡ Generate Report"):
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    else:
        with st.spinner("Processing local math and querying Gemini..."):
            engine = ReportEngine("temp_state.json")
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
            
            st.session_state["report"] = response.text

# 2. Display Report & Chat
if "report" in st.session_state:
    st.markdown("### 📋 Generated Report")
    st.markdown(st.session_state["report"])
    
    st.markdown("---")
    st.subheader("💬 Discuss Setup with Mentor")
    
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
        
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["text"])
            
    user_query = st.chat_input("Ask a question about this setup...")
    if user_query:
        st.session_state["chat_history"].append({"role": "user", "text": user_query})
        with st.chat_message("user"):
            st.write(user_query)
            
        # Call API for discussion
        client = genai.Client(api_key=api_key)
        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction="Discuss the report objectively. Keep answers brief, direct, and structured."
            )
        )
        chat.send_message(f"Context report:\n{st.session_state['report']}")
        
        # Pull history if needed or just send the current query
        res = chat.send_message(user_query)
        
        st.session_state["chat_history"].append({"role": "assistant", "text": res.text})
        with st.chat_message("assistant"):
            st.write(res.text)