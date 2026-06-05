import streamlit as st
import json
import os
import requests
from datetime import datetime, timedelta, timezone
from injestionT1 import DataVacuum

sgt_tz = timezone(timedelta(hours=8))

st.set_page_config(page_title="FX Quant Engine - Viewport", layout="wide")
current_time_str = datetime.now(sgt_tz).strftime("%Y-%m-%d %H:%M:%S")

st.title("🎛️ FX Quant Core Engine Controller")
st.caption("Tier 1 Ingestion Viewer — Engine-Head Development Mode")

# Strategy Input Fields
col1, col2 = st.columns(2)
with col1:
    selected_pair = st.text_input("Target Currency Pair", value="AUDUSD")

    # Process Activation Mechanism
    if st.button("⚡ Kick Ingestion Engine In Motion", use_container_width=True):
        vacuum_process = DataVacuum(pair=selected_pair)
        result = vacuum_process.execute(force=True) # change to false to enable 5min limit
        
        # Indented inside the button so it only runs when clicked!
        if "Skipped" in result:
            st.warning(result)
        else:
            st.success(result)

st.divider()

# Preserved Data Layout Visualization
st.subheader("📦 Current Preserved Data Core (`market_state.json`)")
# 1. Local Current Time Display at the Top
st.markdown(f"⏱️ **Local System Time:** `{current_time_str}`")
if os.path.exists("market_state.json"):
    try:
        with open("market_state.json", "r") as f:
            stored_json = json.load(f)
            
        # Extract file timestamp for display
        file_ts_str = stored_json.get("timestamp", "Never")
        
        # Present the live metrics on screen with zero token overhead
        st.metric(
            label=f"Live Spot Price ({stored_json.get('pair', 'N/A')})", 
            value=f"{stored_json.get('spot_price', 0.0):.5f}",
            delta=f"Data Feed Timestamp: {file_ts_str}"
        )
        
        # Present the entire raw data schema explicitly for validation
        st.json(stored_json)
        
    except Exception as e:
        st.error(f"Error reading local data asset: {e}")
else:
    st.info("No database file found. Click the button above to kick the intake into gear.")