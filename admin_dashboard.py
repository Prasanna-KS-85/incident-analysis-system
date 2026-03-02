import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
from utils import route_engine
from utils import route_engine
from utils import route_engine
import sys
import os
import time
import base64
import io
from PIL import Image
from datetime import datetime
from bson.objectid import ObjectId
import smtplib
import re
import reprlib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# --- CONFIGURATION: ECHO NOTIFICATION SYSTEM ---
# --- CONFIGURATION: ECHO NOTIFICATION SYSTEM ---
SENDER_EMAIL = "YOUR_GMAIL_ADDRESS" # REPLACE WITH YOUR GMAIL
APP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"   # REPLACE WITH YOUR APP PASSWORD (NOT LOGIN PASSWORD)

# --- EMAIL ENGINE ---
# --- EMAIL ENGINE ---
def send_notification_email(recipient_email, ticket_id, new_status, admin_remarks, grievance_text=""):
    print("\n--- 🔍 MAIL DEBUG START ---")
    print(f"Recipient: {repr(recipient_email)}")
    print(f"Ticket ID: {repr(ticket_id)}")
    print(f"Status: {repr(new_status)}")
    print(f"Remarks Type: {type(admin_remarks)}")
    # Use repr() to reveal hidden characters like \xa0
    print(f"Remarks Content: {repr(admin_remarks)}") 
    print("--- 🔍 MAIL DEBUG END ---\n")

    if not recipient_email or "@" not in recipient_email:
        return False, "Invalid Email"

    # --- 1. STRING CLEANING (ASCII-PROOFING) ---
    def clean_text(text):
        if not text: return ""
        # Replaces all non-breaking spaces and weird whitespace with standard spaces
        return re.sub(r'[^\x00-\x7F]+', ' ', str(text)).strip()
        
    # Check for toxic characters before cleaning for warning
    if '\xa0' in str(admin_remarks):
        st.warning("⚠️ Toxic character (\\xa0) detected in remarks! Cleaning automatically...")

    ticket_id = clean_text(ticket_id)
    new_status = clean_text(new_status)
    admin_remarks = clean_text(admin_remarks)
    grievance_text = clean_text(grievance_text or "No description provided.")
        
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        
        # --- 3. ROBUST HEADER ENCODING ---
        subject_text = f"Grievance Update: Ticket #{ticket_id} [{new_status}]"
        # Since we cleaned the text, simple utf-8 header is enough, but encode() makes it safe bytes
        msg['Subject'] = Header(subject_text, 'utf-8')

        # Define status color
        status_color = "#22C55E" if new_status == "Resolved" else "#F59E0B" if new_status == "In Progress" else "#3B82F6"

        # 1. Plain Text Fallback
        text_body = f"""
        CIVIC SENTINEL UPDATE
        ---------------------
        Ticket ID: {ticket_id}
        New Status: {new_status}
        
        You Reported:
        {grievance_text}
        
        Admin Remarks:
        {admin_remarks}
        
        Thank you for helping us improve our city.
        """
        
        # 2. Professional HTML Template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ background-color: #1E293B; color: #ffffff; padding: 20px; text-align: center; }}
                .header h2 {{ margin: 0; font-size: 24px; letter-spacing: 1px; }}
                .content {{ padding: 30px; color: #333333; line-height: 1.6; }}
                .status-badge {{ display: inline-block; background-color: {status_color}; color: #ffffff; padding: 5px 12px; border-radius: 4px; font-weight: bold; margin-bottom: 20px; }}
                .section {{ margin-bottom: 25px; border-left: 4px solid #e2e8f0; padding-left: 15px; }}
                .section h3 {{ margin-top: 0; color: #475569; font-size: 16px; text-transform: uppercase; letter-spacing: 0.5px; }}
                .footer {{ background-color: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
                .btn {{ display: inline-block; padding: 10px 20px; color: #ffffff; text-decoration: none; border-radius: 5px; margin: 0 5px; font-size: 14px; }}
                .btn-good {{ background-color: #10B981; }}
                .btn-bad {{ background-color: #EF4444; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>CIVIC SENTINEL | OFFICIAL UPDATE</h2>
                </div>
                <div class="content">
                    <p>Dear Citizen,</p>
                    <p>This is an automated update regarding your grievance (ID: <strong>{ticket_id}</strong>).</p>
                    
                    <div style="text-align: center;">
                        <span class="status-badge">{new_status}</span>
                    </div>
                    
                    <div class="section">
                        <h3>You Reported</h3>
                        <p style="font-style: italic; color: #555;">"{grievance_text}"</p>
                    </div>
                    
                    <div class="section">
                        <h3>Action Taken</h3>
                        <p>{admin_remarks}</p>
                    </div>
                    
                    <p>Thank you for being an active citizen and helping us improve our city.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="font-weight: bold; margin-bottom: 10px;">How was our response?</p>
                        <a href="#" class="btn btn-good">Great 👍</a>
                        <a href="#" class="btn btn-bad">Poor 👎</a>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2026 Civic Sentinel Authority. All rights reserved.</p>
                    <p>This is an automated government response. Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # --- 2. SET UTF-8 ENCODING (CRITICAL) ---
        # Attach both parts (client will choose best one)
        msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        
        # Strip hidden characters and spaces from credentials
        clean_email = SENDER_EMAIL.strip().replace('\xa0', '')
        clean_password = APP_PASSWORD.strip().replace('\xa0', '').replace(' ', '')
        
        server.login(clean_email, clean_password)
        # Use send_message for better UTF-8 handling
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("❌ EMAIL FAILED WITH TRACEBACK:")
        traceback.print_exc()
        return False

# ---------------------------------------------------------
# VELLORE EMERGENCY HUBS CONFIGURATION
# ---------------------------------------------------------

# ---------------------------------------------------------
# VELLORE MULTI-HUB CONFIGURATION (REAL COORDINATES)
# ---------------------------------------------------------

# ---------------------------------------------------------
# VELLORE MULTI-HUB CONFIGURATION (REAL COORDINATES)
# ---------------------------------------------------------
VELLORE_HUBS = {
    "Police": {
        "color": [0, 255, 255, 200], # Neon Cyan
        "stations": [
            {"name": "Vellore North Stn", "lat": 12.9232, "lon": 79.1316},
            {"name": "SP Office Sathuvachari", "lat": 12.9369, "lon": 79.1500},
            {"name": "Ponnai Stn (Katpadi)", "lat": 13.1319, "lon": 79.2573}
        ]
    },
    "Medical": {
        "color": [57, 255, 20, 200], # Neon Green
        "stations": [
            {"name": "CMC Main Campus", "lat": 12.9248, "lon": 79.1334},
            {"name": "Govt Medical College", "lat": 12.9360, "lon": 79.0660}
        ]
    },
    "Fire": {
        "color": [255, 50, 50, 200], # Neon Red
        "stations": [{"name": "Vellore Fire Stn", "lat": 12.9150, "lon": 79.1300}]
    },
    "Municipal": {
        "color": [255, 215, 0, 200], # Gold
        "stations": [{"name": "Vellore City Corp", "lat": 12.9112, "lon": 79.1302}]
    }
}

def get_dept_hub(dept_name):
    """Fuzzy matcher for Department Names"""
    name = str(dept_name).lower()
    if "police" in name or "safety" in name: return VELLORE_HUBS["Police"]
    if "medical" in name or "health" in name or "ambulance" in name: return VELLORE_HUBS["Medical"]
    if "fire" in name: return VELLORE_HUBS["Fire"]
    if "municipal" in name or "water" in name or "road" in name: return VELLORE_HUBS["Municipal"]
    return None



# --- DYNAMIC ROOT DETECTION ---
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "utils"))

# --- IMPORTS ---
try:
    from db_handler import DatabaseHandler
except ImportError:
    st.error("Could not import DatabaseHandler. Check your path or utils folder.")
    st.stop()

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Tarp|Admin Dashboard",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Command Center Dark Mode (Monochrome)
st.markdown("""
<style>
    /* Main Background - Deep Charcoal/Black */
    .stApp {
        background-color: #000000;
        color: #E0E0E0;
        font-family: 'Roboto Mono', monospace; /* Tech/Command aesthetic */
    }
    
    /* Sidebar - Dark Slate */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #333333;
    }
    
    /* Metric Cards - Dark Cards */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        padding: 15px;
        border-radius: 4px; /* Sharper corners */
        color: #FFFFFF;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="metric-container"] > label {
        color: #9E9E9E !important; /* Muted label */
        font-weight: 600;
    }
    
    /* Headers - White/Silver */
    h1, h2, h3, h4 {
        color: #FFFFFF !important;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Dataframes/Tables - Dark Theme */
    .stDataFrame {
        border: 1px solid #333333;
        background-color: #1E1E1E;
    }
    [data-testid="stDataFrameResizable"] {
        background-color: #111111;
        color: #E0E0E0;
    }
    
    /* Buttons - Minimalist High Contrast */
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
        color: #000000 !important;
        border-radius: 4px;
        font-weight: bold;
    }
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #FFFFFF !important;
        color: #FFFFFF !important;
        border-radius: 4px;
    }
    
    /* Sidebar Filter Multiselect */
    .stMultiSelect > label {
        color: #FFFFFF !important;
    }
    span[data-baseweb="tag"] {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: 1px solid #555555;
    }
    
    /* Toast/Alerts */
    .stToast {
        background-color: #333333 !important;
        color: white !important;
        border: 1px solid #555555;
    }
    
    /* Selectbox & Text Area in Forms */
    .stSelectbox > label, .stTextArea > label {
        color: #E0E0E0 !important;
    }
    .stSelectbox > div > div {
        background-color: #111111;
        color: white;
        border: 1px solid #333;
    }
    .stTextArea > div > div > textarea {
        background-color: #111111;
        color: white;
        border: 1px solid #333;
    }
</style>
""", unsafe_allow_html=True)

# --- DB CONNECTION ---
@st.cache_resource
def get_db():
    return DatabaseHandler()

db = get_db()

# --- SIDEBAR & CONTROLS ---
st.sidebar.title("COMMAND CENTER")
st.sidebar.caption("v2.0 | SYSTEM ONLINE")
st.sidebar.markdown("---")

# 1. SYSTEM RESET
if st.sidebar.button("⚠️ SYSTEM RESET", type="primary"):
    if db.clear_all_complaints():
        st.toast("SYSTEM PURGED. REBOOTING...", icon="🗑️")
        time.sleep(1)
        st.rerun()

st.sidebar.info("CLEAR DATABASE FOR DEMO")
st.sidebar.markdown("---")

# --- HEADER ---
st.title("🚔 CIVIC SENTINEL")
st.markdown("### *REAL-TIME GRIEVANCE MONITORING*")
st.markdown("---")

# --- 2. DATA PIPELINE (ZERO-CRASH POLICY) ---
if not db.is_connected:
    st.error("🚨 CRITICAL FAILURE: DATABASE OFFLINE")
    st.stop()

with st.spinner("ESTABLISHING DATALINK..."):
    # STRICTION: Immediate conversion to list
    raw_data = list(db.fetch_all_complaints())
    
if not raw_data:
    st.info("ℹ️ SYSTEM STANDBY. NO ACTIVE SIGNALS.")
    st.stop()

# STRICTION: DataFrame Creation
df_raw = pd.DataFrame(raw_data)

# FIX: Convert ObjectId to string
if '_id' in df_raw.columns:
    df_raw['_id'] = df_raw['_id'].astype(str)

# Robust Numeric Conversion
for col in ['cci', 'sentiment_score']:
    if col in df_raw.columns:
        df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0.0)
    else:
        df_raw[col] = 0.0

# --- ROBUST TEXT NORMALIZATION ---
# Ensure 'text' column exists and is populated from various possible keys
def get_grievance_text(row):
    return row.get('text') or row.get('description') or row.get('complaint') or row.get('grievance_text') or "No description provided."

df_raw['text'] = df_raw.apply(get_grievance_text, axis=1)

# --- 3. HYBRID EXTRACTION LOGIC (CRITICAL) ---
def get_lat(row):
    # Option A: Check flat column (Batch JSON format)
    if pd.notnull(row.get('lat')) and row.get('lat') != 0:
        try:
            return float(row['lat'])
        except:
            pass
    # Option B: Check nested GPS object (Live Report format)
    if isinstance(row.get('gps'), dict):
        try:
            return float(row['gps'].get('lat', 0.0))
        except:
            pass
    return 0.0

def get_lon(row):
    # Option A: Check flat column
    if pd.notnull(row.get('lon')) and row.get('lon') != 0:
        try:
            return float(row['lon'])
        except:
            pass
    # Option B: Check nested GPS object
    if isinstance(row.get('gps'), dict):
        try:
            return float(row['gps'].get('lon', 0.0))
        except:
            pass
    return 0.0

df_raw['lat'] = df_raw.apply(get_lat, axis=1)
df_raw['lon'] = df_raw.apply(get_lon, axis=1)

# Fill Metadata
df_raw['priority'] = df_raw.get('priority', 'Medium').fillna('Medium')
df_raw['category'] = df_raw.get('category', 'Unclassified').fillna('Unclassified')

# --- 4. LOGIC UPGRADE: AI AUTO-DISPATCHER ---
def assign_department(row):
    # Analyze both category and text
    text_content = (str(row.get('category', '')) + " " + str(row.get('text', ''))).lower()
    
    # Police & Fire
    if any(k in text_content for k in ["fire", "theft", "accident", "blood", "harassment", "collision", "crime", "police"]):
        return "Police Control Room"
    
    # Medical
    if any(k in text_content for k in ["ambulance", "health", "hospital", "injury", "medical", "doctor"]):
        return "Medical Emergency Services"
    
    # Municipal
    if any(k in text_content for k in ["water", "road", "garbage", "sewage", "pothole", "sanitation", "pipe", "trash", "clean"]):
        return "Municipal Corporation"
    
    # Electricity
    if any(k in text_content for k in ["electric", "power", "wire", "shock", "light", "outage", "tneb"]):
        return "TNEB (Electricity Board)"
        
    # Default
    return "Civil Administration"

df_raw['assigned_dept'] = df_raw.apply(assign_department, axis=1)

# --- 5. UI UPGRADE: SIDEBAR FILTERS ---
st.sidebar.markdown("### 🔍 UNIT FILTERS")
all_depts = sorted(df_raw['assigned_dept'].unique())
dept_filter = st.sidebar.multiselect(
    "SELECT DEPLOYMENT UNIT",
    options=all_depts,
    default=all_depts
)

if not dept_filter:
    st.warning("SELECT AT LEAST ONE UNIT.")
    st.stop()

# FILTER DATAFRAME based on selection
df = df_raw[df_raw['assigned_dept'].isin(dept_filter)].copy()

# --- KPI METRICS (FILTERED) ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("TOTAL TICKETS", len(df), delta="LIVE")
c2.metric("CRITICAL OPS", len(df[df['priority'] == 'High']), delta="ACTION REQ", delta_color="inverse")
c3.metric("AVG RESPONSE", "4.2 HRS", delta="-12%")
c4.metric("MEAN RISK IDX", f"{df['cci'].mean():.1f}/10")

st.markdown("---")

# --- 6. 3D GEOSPATIAL MAP (VELLORE CENTERING) ---
st.subheader("🌍 GEOSPATIAL HEATMAP")

# Filter for valid data > 10 (Avoid Ocean)
valid_geo = df[(df['lat'] > 10) & (df['lon'] > 70)].copy()

if not valid_geo.empty:
    mid_lat = valid_geo['lat'].mean()
    mid_lon = valid_geo['lon'].mean()
else:
    # FORCE DEFAULT TO VELLORE
    mid_lat = 12.9165
    mid_lon = 79.1325

col_map, col_legend = st.columns([3, 1])

with col_map:
    # Define Color Logic (RGBA)
    def get_color(row):
        p = row['priority']
        if p == 'High': return [239, 68, 68, 200]    # Red
        if p == 'Medium': return [249, 115, 22, 200] # Orange
        return [34, 197, 94, 200]                    # Green

    if not valid_geo.empty:
        valid_geo['color'] = valid_geo.apply(get_color, axis=1)
        valid_geo['elevation_scaled'] = valid_geo['cci'] * 100 
    
    # 3D Column Layer
    layer = pdk.Layer(
        "ColumnLayer",
        data=valid_geo,
        get_position=["lon", "lat"],
        get_elevation="elevation_scaled",
        elevation_scale=1,
        radius=70,  
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        latitude=mid_lat,
        longitude=mid_lon,
        zoom=13,
        pitch=45, # 3D Perspective
        bearing=0
    )

    # --- ARC VECTOR LOGIC ---
    arc_layers = []
    
    # Check if a SINGLE department is selected (Laser Mode)
    if len(dept_filter) == 1:
        target_dept_name = dept_filter[0]
        
        # Fuzzy Match to find the Hub Config
        dept_config = get_dept_hub(target_dept_name)
        
        if dept_config and not valid_geo.empty:
            stations = dept_config['stations']
            dept_color = dept_config['color']
            
            # Helper to find nearest station
            def get_nearest_hub_coords(row):
                inc_lat = row['lat']
                inc_lon = row['lon']
                
                nearest = None
                min_dist = float('inf')
                
                for stn in stations:
                    # Simple Euclidean distance squared
                    dist = (stn['lat'] - inc_lat)**2 + (stn['lon'] - inc_lon)**2
                    if dist < min_dist:
                        min_dist = dist
                        nearest = stn
                
                if nearest:
                    return [nearest['lon'], nearest['lat']]
                return [0, 0]

            # Create Arc Dataframe
            arc_data = valid_geo.copy()
            arc_data['source'] = arc_data.apply(get_nearest_hub_coords, axis=1)
            arc_data['target'] = arc_data.apply(lambda x: [x['lon'], x['lat']], axis=1)
            arc_data['color'] = arc_data.apply(lambda x: dept_color, axis=1)
            
            # Create Arc Layer
            vector_layer = pdk.Layer(
                "ArcLayer",
                data=arc_data,
                get_source_position="source",
                get_target_position="target",
                get_source_color="color",          
                get_target_color=[255, 0, 0, 200], # Red Impact
                get_width=6,                       # Thick
                get_tilt=20,                       # High Arch
                pickable=True,
                auto_highlight=True,
            )
            arc_layers.append(vector_layer)

    # Streamlit Default Map Tiles (Carto Dark Matter basemap)
    r = pdk.Deck(
        layers=[layer] + arc_layers,
        initial_view_state=view_state,
        map_style="dark",
        tooltip={"text": "Category: {category}\nAssigned: {assigned_dept}\nRisk: {cci}"}
    )
    
    st.pydeck_chart(r)

with col_legend:
    st.markdown("#### THREAT LEGEND")
    st.error("🔴 **HIGH RISK** (CRITICAL)")
    st.warning("🟡 **MEDIUM RISK** (WATCH)")
    st.success("🟢 **LOW RISK** (MONITOR)")
    st.caption("ELEVATION = RISK MAGNITUDE")

# --- 7. DEBUGGING LAYER ---
with st.expander("🕵️ DEBUG: TELEMETRY CHECK"):
    st.write(df[['category', 'lat', 'lon', 'priority', 'assigned_dept']].head(10))
    st.caption("VERIFY COORDINATE STREAM")

st.markdown("---")

# --- 8. GLOBAL ANALYTICS ---
st.subheader("📊 GLOBAL SITUATION AWARENESS")

domain = ['High', 'Medium', 'Low']
range_ = ['#EF4444', '#F97316', '#22C55E']

rc1, rc2 = st.columns(2)
with rc1:
    st.markdown("#### 🚨 PRIORITY DISTRIBUTION")
    donut = alt.Chart(df).mark_arc(innerRadius=60).encode(
        theta=alt.Theta("count()", stack=True),
        color=alt.Color("priority", scale=alt.Scale(domain=domain, range=range_)),
        tooltip=["priority", "count()"]
    ).properties(height=300)
    st.altair_chart(donut, use_container_width=True)

with rc2:
    st.markdown("#### 🔍 SENTIMENT MATRIX")
    scatter = alt.Chart(df).mark_circle(size=80).encode(
        x=alt.X('sentiment_score', title="Sentiment (-1 to +1)"),
        y=alt.Y('cci', title="Risk Score (CCI)"),
        color=alt.Color("priority", scale=alt.Scale(domain=domain, range=range_)),
        tooltip=['category', 'assigned_dept', 'cci']
    ).interactive().properties(height=300)
    st.altair_chart(scatter, use_container_width=True)

# Risk by Dept
st.markdown("#### 🌡️ RISK BY UNIT")
bar = alt.Chart(df).mark_bar().encode(
    x=alt.X("mean(cci)", title="Avg Risk Score"),
    y=alt.Y("category", sort="-x"),
    color=alt.Color("mean(cci)", scale=alt.Scale(scheme="reds"), legend=None),
    tooltip=["category", "mean(cci)"]
).properties(height=350)
st.altair_chart(bar, use_container_width=True)

st.markdown("---")

# --- 9. TICKET RESOLUTION DESK (ACTION CENTER) ---
st.markdown("### 🛠️ TICKET RESOLUTION DESK")

# Filter logic for Ticket Selector
# Create a display string list options
ticket_options = df_raw.apply(
    lambda x: f"{x['_id']} - {x['category']} ({x['priority']})", axis=1
).tolist()

selected_ticket_str = st.selectbox("SELECT TICKET TO MANAGE", ticket_options)

if selected_ticket_str:
    # Extract ID
    selected_id = selected_ticket_str.split(" - ")[0]
    
    # --- CRITICAL FIX: FETCH FROM DB DIRECTLY ---
    # We fetch from DB instead of df_raw to ensure we get ALL fields (text, images, etc.)
    if db.is_connected:
        from bson.objectid import ObjectId
        try:
            ticket_data = db.collection.find_one({"_id": ObjectId(selected_id)})
        except:
            st.error("Invalid ID format.")
            st.stop()
    else:
        st.error("Database Offline.")
        st.stop()

    # --- NEW: INCIDENT CONTEXT BOX ---
    st.markdown("### 📄 Incident Details")
    
    # Text Extraction: Prioritize 'original_text' based on DB Schema
    grievance_desc = ticket_data.get('original_text') or ticket_data.get('translated_text') or ticket_data.get('text') or "No description provided."
    lang = ticket_data.get('src_lang', 'Unknown')
    
    with st.container():
        # Custom CSS for the description box to make it stand out
        st.markdown(f"""
        <div style="background-color: #1E293B; padding: 20px; border-radius: 8px; border-left: 5px solid #3B82F6; margin-bottom: 20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 5px;">
                <p style="color: #94A3B8; font-size: 0.85em; margin:0;">REPORTED GRIEVANCE:</p>
                <span style="background-color:#334155; color:#cbd5e1; padding:2px 8px; border-radius:4px; font-size:0.7em;">Lang: {lang}</span>
            </div>
            <p style="color: #FFFFFF; font-size: 1.1em; font-weight: 500; margin: 0;">
                "{grievance_desc}"
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Display English Transcript if applicable
        translated = ticket_data.get('translated_text', '')
        original = ticket_data.get('original_text', '')
        
        if translated and translated != original:
            st.markdown("---")
            st.markdown("#### 🌎 English Transcript:")
            st.success(f"{translated}")

        # Optional: Show Image Thumbnail if exists
        if ticket_data.get('has_image'):
            st.caption("📸 Visual Evidence is attached to this report (See below).")
    
    # --- 6. NAVIGATOR INTEGRATION (DYNAMIC ROUTING) ---
    # --- NAVIGATOR ENGINE INTEGRATION ---
    st.markdown("### 🚁 Emergency Response Route")
    with st.spinner("🛰️ Calculating fastest extraction route..."):
        # 1. FIND NEAREST STATION
        # Uses the ticket's category (Fire/Medical) to pick the right station type
        ticket_cat = ticket_data.get('category', 'General') 
        # 1. Extract GPS (Prioritize flat batch keys over nested portal keys)
        incident_lat = None
        incident_lon = None
        if 'lat' in ticket_data and 'lon' in ticket_data and ticket_data['lat'] is not None:
            incident_lat = float(ticket_data['lat'])
            incident_lon = float(ticket_data['lon'])
        elif 'latitude' in ticket_data and 'longitude' in ticket_data:
            incident_lat = float(ticket_data['latitude'])
            incident_lon = float(ticket_data['longitude'])
        elif 'gps' in ticket_data and isinstance(ticket_data['gps'], dict):
            incident_lat = ticket_data['gps'].get('lat')
            incident_lon = ticket_data['gps'].get('lon')
        
        if incident_lat and incident_lon:
            t_lat = incident_lat
            t_lon = incident_lon
            # 2. Use translated text for accurate keyword routing
            text_to_analyze = ticket_data.get('translated_text', ticket_data.get('original_text', ''))
            station = route_engine.find_nearest_station(
                incident_lat, 
                incident_lon, 
                ticket_data.get('category', ''), 
                text_to_analyze
            )
            
            if station:
                # EXTRACT COORDINATES SAFELY
                # Assuming station['coords'] is [Lon, Lat] (GeoJSON standard) as per route_engine.py
                # But wait! route_engine.py returns 'lat' and 'lon' keys in the dict, NOT 'coords'.
                # Let's check how find_nearest_station returns data.
                # It returns: {'name':..., 'lat':..., 'lon':..., 'distance_km':...}
                st_lat = station['lat']
                st_lon = station['lon']
    
                # Ensure we pass (LAT, LON) to the engine
                # ERROR WAS HERE: We previously swapped these!
                route_path = route_engine.get_route_geometry(
                    st_lat, st_lon,  # Start: Station (Latitude First!)
                    t_lat, t_lon     # End: Incident
                )
                
                # VISUAL DEBUGGER (Show us the data!)
                with st.expander("🛠️ Debug: Route Telemetry"):
                    st.write(f"Station: {st_lat}, {st_lon}")
                    st.write(f"Incident: {t_lat}, {t_lon}")
                    if route_path:
                        st.write(f"✅ Route Found! {len(route_path['geometry']['coordinates'])} points.")
                        st.write(f"First Point: {route_path['geometry']['coordinates'][0]}")
                    else:
                        st.error("❌ Google Maps returned NO route. Check coordinates above.")
                
                if route_path:
                    # --- 1. INITIALIZE THE LAYERS LIST (CRITICAL FIX) ---
                    layers = [] 
    
                    # --- 2. CREATE THE PATH LAYER (The Route Line) ---
                    layer_path = pdk.Layer(
                        "PathLayer",
                        data=[{
                            "path": route_path["geometry"]["coordinates"], 
                            "color": [255, 50, 50, 255] # Emergency Red
                        }],
                        get_path="path",
                        get_color="color",
                        width_scale=20,
                        width_min_pixels=5,
                    )
                    layers.append(layer_path) # Safe to append now
                    
                    # --- 3. CREATE THE ICONS LAYER (Start/End Points) ---
                    icon_data = [
                        {"position": [station['lon'], station['lat']], "color": [0, 255, 0], "name": f"STATION: {station['name']}"},
                        {"position": [t_lon, t_lat], "color": [255, 0, 0], "name": "INCIDENT SITE"}
                    ]
                    
                    layer_points = pdk.Layer(
                        "ScatterplotLayer",
                        data=icon_data,
                        get_position="position",
                        get_fill_color="color",
                        get_radius=120,
                        pickable=True
                    )
                    layers.append(layer_points)
                    
                    # --- 4. RENDER THE CHART ---
                    # 3D View State
                    view_state = pdk.ViewState(
                        latitude=t_lat,
                        longitude=t_lon,
                        zoom=13,
                        pitch=50 # Cool 3D angle
                    )
                    
                    st.pydeck_chart(pdk.Deck(
                        layers=layers,  # Pass the list we just built
                        initial_view_state=view_state,
                        map_style="dark",
                        tooltip={"text": "{name}"}
                    ))
                    
                    st.success(f"Dispatched from: {station['name']}")
                    col1, col2 = st.columns(2)
                    col1.metric("Live ETA", route_path["duration_text"])
                    col2.metric("Distance", route_path["distance_text"])
                    
                else:
                    st.warning("⚠️ Route calculation unavailable. Showing static location.")
                    st.map(pd.DataFrame({'lat': [t_lat], 'lon': [t_lon]}))
            else:
                st.warning("⚠️ Dispatch Engine Offline: Unable to locate a nearby facility or missing API credentials.")
        else:
             st.warning("⚠️ No GPS Coordinates available for this ticket.")

    # Update Form
    with st.form("update_form"):
        st.markdown("#### UPDATE TICKET STATUS")
        
        new_status = st.selectbox(
            "New Status",
            ["Pending", "In Progress", "Resolved", "Rejected"],
            index=0
        )
        
        admin_comment = st.text_area("Admin Remarks", placeholder="Enter resolution details or dispatch notes...")
        
        submit_update = st.form_submit_button("UPDATE STATUS", type="primary")
        
        if submit_update:
            if db.is_connected:
                try:
                    # Update DB
                    db.collection.update_one(
                        {"_id": ObjectId(selected_id)}, 
                        {"$set": {
                            "status": new_status, 
                            "admin_comment": admin_comment,
                            "updated_at": datetime.now()
                        }}
                    )
                    
                    # --- ECHO NOTIFICATION TRIGGER ---
                    # Check for email keys: 'email', 'user_email', or 'contact'
                    recipient_email = ticket_data.get('email') or ticket_data.get('user_email') or ticket_data.get('contact')
                    
                    if recipient_email:
                        with st.spinner("📧 Sending Notification..."):
                            mail_sent = send_notification_email(recipient_email, selected_id, new_status, admin_comment, grievance_desc)
                            
                            if mail_sent:
                                st.balloons()
                                st.toast("📧 Notification sent to Citizen!", icon="✅")
                                st.success("✅ Ticket Updated & Citizen Notified Successfully!")
                            else:
                                st.warning("⚠️ Ticket Updated, but Email Notification Failed.")
                    else:
                        st.success("✅ Ticket Updated (No Email Found)")
                    # ---------------------------------

                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"UPDATE FAILED: {e}")
            else:
                st.error("DATABASE OFFLINE. CANNOT UPDATE.")

st.markdown("---")

# --- 10. LIVE QUEUE (SMART STATUS) ---
st.subheader("📋 LIVE INCIDENT FEED")
st.write(f"Total Records: {len(df)}") # Debugging line to see row count

# Format Assigned Dept with Fire Icon if Critical
def format_dept(row):
    dept = row['assigned_dept']
    if row['priority'] == 'High':
        return f"🔥 {dept}"
    return dept

df['Formatted Dept'] = df.apply(format_dept, axis=1)

display_cols = ['Formatted Dept', 'category', 'priority', 'cci', 'text', 'status', 'sentiment_score', 'lat', 'lon']
cols = [c for c in display_cols if c in df.columns]

st.dataframe(
    df[cols].sort_values(by='cci', ascending=False),
    use_container_width=True,
    column_config={
        "cci": st.column_config.ProgressColumn("Risk Score", min_value=0, max_value=10, format="%.1f"),
        "Formatted Dept": st.column_config.TextColumn("⚠️ ASSIGNED UNIT", width="medium"),
        "lat": st.column_config.NumberColumn("LAT", format="%.4f"),
        "lon": st.column_config.NumberColumn("LON", format="%.4f")
    },
    hide_index=True
)

st.caption(f"LAST SYNC: {datetime.now().strftime('%H:%M:%S')}")
