import streamlit as st
import pandas as pd
import json
import time
import altair as alt
import pydeck as pdk
import sys
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VIT Civic Sentinel",
    page_icon="📡",
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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from pipeline_package.grievance_pipeline import GrievanceOrchestrator
except ImportError:
    # Fallback path if running from root
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '4_pipeline'))
    try:
        from grievance_pipeline import GrievanceOrchestrator
    except ImportError:
         st.error("Pipeline module missing. Check directory structure.")
         st.stop()

# --- ADAPTER (CRITICAL FIX FOR NESTED DATA) ---
def flatten_result(raw):
    """Flattens the nested pipeline output for UI consumption."""
    flat = raw.copy()
    if 'classification' in raw:
        flat['category'] = raw['classification'].get('category')
        flat['confidence'] = raw['classification'].get('confidence')
    if 'sentiment' in raw:
        flat['sentiment_score'] = raw['sentiment'].get('score')
    if 'urgency' in raw:
        flat['is_urgent'] = raw['urgency'].get('is_urgent', False)
    if 'decision' in raw:
        flat['cci'] = raw['decision'].get('cci')
        flat['priority'] = raw['decision'].get('priority')
    return flat

# --- SESSION STATE ---
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = GrievanceOrchestrator()
if 'batch_data' not in st.session_state:
    st.session_state.batch_data = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 VIT Sentinel")
    st.caption("v2.0 | Integrated Command Center")
    st.markdown("---")
    st.subheader("System Status")
    st.success("● AI Agents Online")
    st.info("● Connected to Vellore Grid")
    st.markdown("---")
    
    # Department Filter
    department = st.selectbox(
        "Department Scope", 
        ["All Departments", "Public Safety", "Sanitation", "Electrical", "Roads"],
        key="dept_filter"
    )
    
    if st.button("🔄 Reset System"):
        st.session_state.batch_data = None
        st.rerun()

# --- MAIN TABS ---
tab_live, tab_batch, tab_map, tab_analytics = st.tabs([
    "🎫 Live Ticket", 
    "📂 Batch & Queue", 
    "🌍 Geospatial Intel", 
    "📈 Global Analytics"
])

# ==========================================
# TAB 1: LIVE TICKET ENTRY
# ==========================================
with tab_live:
    st.subheader("📝 Rapid Incident Reporting")
    col1, col2 = st.columns([2, 1])
    with col1:
        text_input = st.text_area("Complaint Narrative", height=150, placeholder="e.g., 'Fire in the chemistry lab on 3rd floor...'")
        if st.button("🚀 Process Ticket", type="primary"):
            if text_input:
                with st.spinner("Analyzing Sentiment, Urgency, and Risk..."):
                    time.sleep(0.5)
                    raw_result = st.session_state.orchestrator.run_pipeline(text_input)
                    result = flatten_result(raw_result) # Fix: Apply adapter
                    
                    st.divider()
                    p_level = result.get('priority', 'Medium')
                    
                    # Dynamic Alert Box
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
                        st.json(raw_result)

# ==========================================
# TAB 2: BATCH PROCESSING (The "Pro" Table)
# ==========================================
with tab_batch:
    st.subheader("📂 Bulk Grievance Processor")
    uploaded_file = st.file_uploader("Upload JSON File (Standard or Geospatial)", type=['json'])
    
    if uploaded_file:
        if st.button("Run Batch Analysis"):
            try:
                data = json.load(uploaded_file)
                st.info(f"Processing {len(data)} complaints...")
                
                results = []
                progress_bar = st.progress(0)
                
                for i, item in enumerate(data):
                    # Robust text extraction
                    txt = item.get('text', item.get('complaint', ''))
                    if not txt: continue
                    
                    raw_res = st.session_state.orchestrator.run_pipeline(txt)
                    res = flatten_result(raw_res) # Fix: Apply adapter
                    
                    combined = {**item, **res}
                    results.append(combined)
                    progress_bar.progress((i + 1) / len(data))
                
                # Create DataFrame & Sanitize
                df = pd.DataFrame(results)
                if 'priority' not in df.columns: df['priority'] = 'Medium'
                if 'cci' not in df.columns: df['cci'] = 0.0
                
                st.session_state.batch_data = df
                st.success("Processing Complete! View results below.")
                
            except Exception as e:
                st.error(f"Error: {e}")

    # THE PRO COMMAND QUEUE TABLE
    if st.session_state.batch_data is not None:
        st.divider()
        df = st.session_state.batch_data
        
        st.markdown("### 📋 Prioritized Command Queue")
        
        # Interactive Filter
        priority_filter = st.multiselect("Filter by Priority", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
        
        if priority_filter:
            # Ensure columns exist before filtering
            if 'priority' in df.columns:
                 filtered_df = df[df['priority'].isin(priority_filter)].sort_values(by="cci", ascending=False)
            
                 st.dataframe(
                    filtered_df,
                    column_config={
                        "cci": st.column_config.ProgressColumn("Risk Score", format="%.1f", min_value=0, max_value=10),
                        "text": st.column_config.TextColumn("Complaint", width="large"),
                        "priority": st.column_config.TextColumn("Priority"),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                 st.error("Data missing 'priority' column.")

# ==========================================
# TAB 3: GEOSPATIAL INTEL (The Map)
# ==========================================
with tab_map:
    if st.session_state.batch_data is not None:
        df = st.session_state.batch_data
        
        # Check if Lat/Lon exists
        if 'lat' in df.columns and 'lon' in df.columns:
            st.subheader("📍 Real-Time Incident Heatmap (Vellore)")
            
            # Map Controls
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                # Color Logic
                def get_color(priority):
                    if priority == 'High': return [255, 0, 0, 200]
                    if priority == 'Medium': return [255, 165, 0, 200]
                    return [0, 255, 0, 200]
                
                if 'priority' not in df.columns:
                     df['priority'] = 'Medium'
                
                df['color'] = df['priority'].apply(get_color)
                
                # 3D Layer
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    df,
                    get_position='[lon, lat]',
                    get_fill_color='color',
                    get_radius=120,
                    pickable=True,
                )
                
                # View State (Centered on VIT Vellore)
                view_state = pdk.ViewState(latitude=12.9716, longitude=79.1585, zoom=14, pitch=50)
                
                # Render Map
                r = pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip={"text": "Category: {category}\nPriority: {priority}\nDesc: {text}"}
                )
                st.pydeck_chart(r)
            
            with col_m2:
                st.markdown("#### Map Legend")
                st.markdown("🔴 **High Priority**")
                st.markdown("🟠 **Medium Priority**")
                st.markdown("🟢 **Low Priority**")
                st.info("💡 Rotate map with Right-Click. Zoom with Scroll.")
                
        else:
            st.warning("⚠️ The uploaded file does not contain GPS coordinates. Upload 'vellore_complaints.json' to see the map.")
    else:
        st.info("ℹ️ Please upload a file in the 'Batch & Queue' tab first.")

# ==========================================
# TAB 4: GLOBAL ANALYTICS (The Charts)
# ==========================================
with tab_analytics:
    if st.session_state.batch_data is not None:
        df = st.session_state.batch_data
        st.subheader("📈 Real-time System Analytics")
        
        # Data Validity Check
        cols_needed = ['priority', 'category', 'sentiment_score', 'cci']
        if all(col in df.columns for col in cols_needed):
            # ROW 1: Donut & Bar
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("#### 🚨 Risk Distribution")
                donut = alt.Chart(df).mark_arc(innerRadius=60).encode(
                    theta=alt.Theta("count()", stack=True),
                    color=alt.Color("priority", scale=alt.Scale(domain=['High', 'Medium', 'Low'], range=['#ff4b4b', '#ffa700', '#00c04b'])),
                    tooltip=["priority", "count()"]
                ).properties(height=300)
                st.altair_chart(donut, use_container_width=True)
                
            with c2:
                st.markdown("#### 📂 Category Breakdown")
                bar = alt.Chart(df).mark_bar().encode(
                    x="count()",
                    y=alt.Y("category", sort="-x"),
                    color="category",
                    tooltip=["category", "count()"]
                ).properties(height=300)
                st.altair_chart(bar, use_container_width=True)
                
            # ROW 2: Scatter Plot
            st.markdown("#### 🔍 Sentiment vs. Criticality")
            scatter = alt.Chart(df).mark_circle(size=60).encode(
                x=alt.X('sentiment_score', title="Sentiment (-1 to +1)"),
                y=alt.Y('cci', title="Criticality Index (CCI)"),
                color='priority',
                tooltip=['text', 'category', 'cci']
            ).interactive()
            st.altair_chart(scatter, use_container_width=True)
        else:
            st.warning("Missing columns for analytics (priority, category, etc).")
        
    else:
        st.info("ℹ️ No data available.")