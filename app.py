import json
import os
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from google import genai
from google.genai import types

# Page setup
st.set_page_config(page_title="AI Disaster Response Hub", layout="wide")

# Initialize Gemini Client
@st.cache_resource
def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error("Please set GEMINI_API_KEY in environment variables.")
        return None
    return genai.Client()

client = get_gemini_client()

# Session State for tracking reports
if "reports" not in st.session_state:
    st.session_state.reports = [
        {
            "id": 1,
            "category": "Medical",
            "urgency": "High",
            "summary": "Elderly person needs oxygen cylinder support immediately.",
            "location": "North Zone",
            "lat": 17.4065,
            "lon": 78.4772,
            "raw": "Urgent medical needed near Old City, oxygen low."
        },
        {
            "id": 2,
            "category": "Food/Water",
            "urgency": "Medium",
            "summary": "Water supply contaminated, clean drinking water requested for 20 households.",
            "location": "East Sector",
            "lat": 17.4350,
            "lon": 78.5000,
            "raw": "Pani ka dikkat hai east sector me, clean water delivery target."
        }
    ]

# AI Triage Function using Gemini 2.5 Flash
def analyze_crisis_report(text_input):
    if not client:
        return None
    
    prompt = f"""
    You are an emergency triage AI assistant for local disaster response.
    Analyze the following user input (it may be in English or local mixed language):
    
    "{text_input}"

    Return a JSON object strictly matching this schema:
    {{
        "category": "Medical" | "Food/Water" | "Rescue" | "Infrastructure" | "Other",
        "urgency": "High" | "Medium" | "Low",
        "summary": "1-2 sentence concise summary of the issue",
        "location_hint": "Extracted location name or 'Unknown'",
        "suggested_action": "Immediate action required for dispatchers"
    }}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        return json.loads(response.text)
    except Exception:
        return None

# App UI Header
st.title("🚨 Community AI Emergency & Disaster Response Hub")
st.caption("Real-time AI triage and incident mapping for local communities")

col_input, col_map = st.columns([1, 1.2])

with col_input:
    st.subheader("📥 Submit Emergency Report")
    
    report_text = st.text_area(
        "Describe the emergency (Multilingual text accepted):",
        placeholder="e.g., Heavy waterlogging near Sector 4 market. Bridge damaged, 5 people stranded needing rescue.",
        height=120
    )
    
    c1, c2 = st.columns(2)
    lat_in = c1.number_input("Latitude", value=17.4150, format="%.4f")
    lon_in = c2.number_input("Longitude", value=78.4850, format="%.4f")

    if st.button("Submit & Analyze with AI", type="primary", use_container_width=True):
        if report_text.strip():
            with st.spinner("AI Processing Triage & Categorization..."):
                result = analyze_crisis_report(report_text)
                
                if result:
                    new_entry = {
                        "id": len(st.session_state.reports) + 1,
                        "category": result.get("category", "Other"),
                        "urgency": result.get("urgency", "Medium"),
                        "summary": result.get("summary", report_text),
                        "location": result.get("location_hint", "Submitted Area"),
                        "lat": lat_in,
                        "lon": lon_in,
                        "raw": report_text,
                        "action": result.get("suggested_action", "")
                    }
                    st.session_state.reports.insert(0, new_entry)
                    st.success("Report Triage Complete & Dispatched!")
                    st.json(result)
                else:
                    st.error("Failed to analyze report.")
        else:
            st.warning("Please enter details about the emergency.")

with col_map:
    st.subheader("🗺️ Live Incident & Crisis Map")
    
    m = folium.Map(location=[17.4150, 78.4850], zoom_start=12)
    color_map = {"High": "red", "Medium": "orange", "Low": "green"}
    
    for item in st.session_state.reports:
        marker_color = color_map.get(item["urgency"], "blue")
        popup_content = f"""
        <b>[{item['urgency']} Urgency] {item['category']}</b><br/>
        <b>Summary:</b> {item['summary']}<br/>
        """
        folium.Marker(
            location=[item["lat"], item["lon"]],
            popup=folium.Popup(popup_content, max_width=250),
            tooltip=f"{item['category']} ({item['urgency']})",
            icon=folium.Icon(color=marker_color, icon="info-sign")
        ).add_to(m)
    
    st_folium(m, width=650, height=420)

st.divider()
st.subheader("📋 Active Incident Feed")

if st.session_state.reports:
    df = pd.DataFrame(st.session_state.reports)
    st.dataframe(
        df[["id", "urgency", "category", "summary", "location"]],
        use_container_width=True,
        hide_index=True
    )