import streamlit as st
import pandas as pd
import json
import time
import altair as alt
import pydeck as pdk
import sys
import os
from datetime import datetime

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TARP Project MVP",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #41444e; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    h1, h2, h3 { color: #f0f2f6; }
    .stDataFrame { border: 1px solid #41444e; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- PATH SETUP ---
# Add parent directory to path to import utils and pipeline
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from pipeline_package.grievance_pipeline import GrievanceOrchestrator
    # Import the PDF Generator
    from utils.report_generator import generate_pdf
except ImportError:
    # Fallback for different folder structures
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '4_pipeline'))
    from grievance_pipeline import GrievanceOrchestrator
    # We assume report_generator is in utils/
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
    from report_generator import generate_pdf

# --- SESSION STATE INITIALIZATION ---
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = GrievanceOrchestrator()
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = None
# NEW: Store PDF data in memory so it doesn't disappear on rerun
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 TARP Project MVP")
    st.caption("v4.0 | Official Release Build")
    st.markdown("---")
    st.subheader("System Status")
    st.success("● AI Agents Online")
    st.info("● Connected to Vellore Grid")
    st.markdown("---")
    
    if st.button("🔄 Reset System"):
        st.session_state.batch_data = None
        st.session_state.pdf_data = None
        st.rerun()

# --- MAIN TABS ---
tab_live, tab_batch, tab_map, tab_analytics = st.tabs([
    "🎫 Live Ticket", 
    "📂 Batch & Queue", 
    "🌍 Geospatial Intel", 
    "📈 Global Analytics"
])

# ==========================================
# TAB 1: LIVE TICKET (Multilingual)
# ==========================================
with tab_live:
    st.subheader("Single Report Processing")
    st.caption("Try typing in Hindi, Tamil, Telugu, Spanish, etc.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        text_input = st.text_area("Complaint Narrative", height=150, placeholder="Type in any language (e.g., 'Paani nahi aa raha hai')...")
        if st.button("🚀 Process Ticket", type="primary"):
            if text_input:
                with st.spinner("Translating & Analyzing..."):
                    time.sleep(0.5)
                    result = st.session_state.orchestrator.run_pipeline(text_input)
                    
                    st.divider()
                    
                    # --- TRANSLATION SHOWCASE ---
                    if result.get('is_translated'):
                        st.info(f"🌐 **Translated from {result.get('src_lang', 'Detected Language')}**")
                        c_t1, c_t2 = st.columns(2)
                        c_t1.text_area("Original Input", result.get('original_text'), disabled=True)
                        c_t2.text_area("English Processed", result.get('translated_text'), disabled=True)
                    else:
                        st.success("✅ Language: English (No translation needed)")

                    # --- RESULTS ---
                    p_level = result.get('priority', 'Medium')
                    if p_level == "High":
                        st.error(f"🚨 **CRITICAL ALERT** (CCI: {result.get('cci', 0)})")
                    elif p_level == "Medium":
                        st.warning(f"⚠️ **Medium Priority** (CCI: {result.get('cci', 0)})")
                    else:
                        st.success(f"✅ **Low Priority** (CCI: {result.get('cci', 0)})")
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Category", result.get('category'))
                    m2.metric("Sentiment", f"{result.get('sentiment_score')}")
                    m3.metric("Urgency", "YES" if result.get('is_urgent') else "NO")
                    m4.metric("Risk Score", result.get('cci'))
                    
                    with st.expander("🧠 View AI Reasoning"):
                        st.json(result)

# ==========================================
# TAB 2: BATCH PROCESSING (With PDF Report)
# ==========================================
with tab_batch:
    st.subheader("📂 Bulk Grievance Processor")
    uploaded_file = st.file_uploader("Upload JSON File", type=['json'])
    
    if uploaded_file:
        if st.button("Run Batch Analysis"):
            try:
                data = json.load(uploaded_file)
                st.info(f"Processing {len(data)} complaints...")
                results = []
                progress_bar = st.progress(0)
                
                for i, item in enumerate(data):
                    txt = item.get('text', item.get('complaint', ''))
                    res = st.session_state.orchestrator.run_pipeline(txt)
                    combined = {**item, **res}
                    results.append(combined)
                    progress_bar.progress((i + 1) / len(data))
                
                df = pd.DataFrame(results)
                if 'priority' not in df.columns: df['priority'] = 'Medium'
                if 'cci' not in df.columns: df['cci'] = 0.0
                
                st.session_state.batch_data = df
                st.success("Processing Complete!")
                
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.batch_data is not None:
        # --- PDF REPORT GENERATION ---
        st.markdown("---")
        c_r1, c_r2 = st.columns([3, 1])
        with c_r1:
            st.subheader("📄 Official Reports")
        with c_r2:
            # 1. The Trigger Button
            if st.button("🔄 Generate Daily Briefing"):
                with st.spinner("Compiling official PDF..."):
                    # Generate File
                    temp_path = generate_pdf(st.session_state.batch_data)
                    
                    # Read into Memory (This fixes the disappearing button bug)
                    with open(temp_path, "rb") as f:
                        st.session_state.pdf_data = f.read()
                    
                    # Cleanup
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    st.toast("Report Ready for Download!", icon="✅")

        # 2. The Persistent Download Button
        if st.session_state.pdf_data is not None:
            st.download_button(
                label="📥 Download Official Report (PDF)",
                data=st.session_state.pdf_data,
                file_name=f"VIT_Sentinel_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary"
            )

        st.divider()
        df = st.session_state.batch_data
        st.markdown("### 📋 Prioritized Command Queue")
        
        priority_filter = st.multiselect("Filter by Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
        if priority_filter:
            filtered_df = df[df['priority'].isin(priority_filter)].sort_values(by="cci", ascending=False)
            st.dataframe(
                filtered_df,
                column_config={
                    "cci": st.column_config.ProgressColumn("Risk Score", format="%.1f", min_value=0, max_value=10),
                    "text": st.column_config.TextColumn("Complaint (Eng)", width="large"),
                    "original_text": st.column_config.TextColumn("Original Input"),
                    "priority": st.column_config.TextColumn("Priority"),
                },
                use_container_width=True,
                hide_index=True
            )

# ==========================================
# TAB 3: GEOSPATIAL INTEL
# ==========================================
with tab_map:
    if st.session_state.batch_data is not None:
        df = st.session_state.batch_data
        if 'lat' in df.columns and 'lon' in df.columns:
            st.subheader("📍 Real-Time Incident Heatmap (Vellore)")
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                def get_color(priority):
                    if priority == 'High': return [255, 0, 0, 200]
                    if priority == 'Medium': return [255, 165, 0, 200]
                    return [0, 255, 0, 200]
                
                df['color'] = df['priority'].apply(get_color)
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    df,
                    get_position='[lon, lat]',
                    get_color='color',
                    get_radius=120,
                    pickable=True,
                )
                view_state = pdk.ViewState(latitude=12.9716, longitude=79.1585, zoom=14, pitch=50)
                r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{category}\n{text}"})
                st.pydeck_chart(r)
            with col_m2:
                st.markdown("#### Map Legend")
                st.markdown("🔴 **High Priority**")
                st.markdown("🟠 **Medium Priority**")
                st.markdown("🟢 **Low Priority**")
        else:
            st.warning("⚠️ Uploaded file missing GPS data.")
    else:
        st.info("ℹ️ Please upload data in 'Batch & Queue' first.")

# ==========================================
# TAB 4: GLOBAL ANALYTICS
# ==========================================
with tab_analytics:
    if st.session_state.batch_data is not None:
        df = st.session_state.batch_data
        st.subheader("📈 Real-time System Analytics")
        
        # --- EXECUTIVE METRICS ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Complaints", len(df))
        m2.metric("Critical Issues (High)", len(df[df['priority']=='High']))
        m3.metric("Urgent Flagged", len(df[df['is_urgent']==True]))
        m4.metric("Avg Risk Score", f"{df['cci'].mean():.1f}/10")
        
        st.markdown("---")

        # --- ROW 1 ---
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🚨 Priority Distribution")
            donut = alt.Chart(df).mark_arc(innerRadius=60).encode(
                theta=alt.Theta("count()", stack=True),
                color=alt.Color("priority", scale=alt.Scale(domain=['High', 'Medium', 'Low'], range=['#ff4b4b', '#ffa700', '#00c04b'])),
                tooltip=["priority", "count()"]
            ).properties(height=300)
            st.altair_chart(donut, use_container_width=True)
            
        with c2:
            st.markdown("#### 📂 Complaints by Category")
            bar = alt.Chart(df).mark_bar().encode(
                x=alt.X("count()", title="Number of Complaints"),
                y=alt.Y("category", sort="-x", title="Category"),
                color="priority",
                tooltip=["category", "count()"]
            ).properties(height=300)
            st.altair_chart(bar, use_container_width=True)

        # --- ROW 2 ---
        c3, c4 = st.columns(2)
        with c3:
            st.markdown("#### 🔍 Sentiment vs. Criticality")
            scatter = alt.Chart(df).mark_circle(size=80).encode(
                x=alt.X('sentiment_score', title="Sentiment (-1 to +1)"),
                y=alt.Y('cci', title="Risk Score (CCI)"),
                color=alt.Color('priority', scale=alt.Scale(domain=['High', 'Medium', 'Low'], range=['#ff4b4b', '#ffa700', '#00c04b'])),
                tooltip=['text', 'category', 'cci', 'sentiment_score']
            ).interactive().properties(height=350)
            st.altair_chart(scatter, use_container_width=True)

        with c4:
            st.markdown("#### 🌡️ Average Risk by Dept")
            risk_bar = alt.Chart(df).mark_bar().encode(
                x=alt.X("mean(cci)", title="Avg Risk Score (0-10)"),
                y=alt.Y("category", sort="-x"),
                color=alt.Color("mean(cci)", scale=alt.Scale(scheme='reds')),
                tooltip=["category", "mean(cci)"]
            ).properties(height=350)
            st.altair_chart(risk_bar, use_container_width=True)
            
    else:
        st.info("ℹ️ No data available. Please upload data in the 'Batch & Queue' tab.")
