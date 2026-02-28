import streamlit as st
import sys
import os
import random
import time
import json
import pandas as pd
import io
import base64
from datetime import datetime
from PIL import Image
from bson.objectid import ObjectId
# UPGRADE: Voice Assistants
import speech_recognition as sr

# --- DYNAMIC ROOT DETECTION ---
# Ensures the script can find its dependencies regardless of where it's run from
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the root directory itself (for db_handler in utils)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Add key subdirectories
sys.path.append(os.path.join(ROOT_DIR, "4_pipeline"))
sys.path.append(os.path.join(ROOT_DIR, "utils"))

# --- IMPORTS AFTER PATH SETUP ---
try:
    from db_handler import DatabaseHandler
    from grievance_pipeline import GrievanceOrchestrator
    # UPGRADE: Using Pipeline for cleaner implementation
    from transformers import pipeline
    # IMPORT LOCATION MANAGER
    from utils import location_manager
except ImportError as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# --- PAGE CONFIGURATION (Professional Minimalist) ---
st.set_page_config(
    page_title="Tarp|User Dashboard",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.google.com',
        'Report a bug': "https://www.google.com",
        'About': "# Civic Sentinel\nAI-Powered Grievance Redressal System"
    }
)



# Custom CSS for Black & White Minimalist Theme + Governance Spec (v3.5)
# CSS Injection for Text Visibility (Step 3) - High Contrast Dark Mode Fix
st.markdown("""
<style>
/* --- 1. GLOBAL BACKGROUND & TEXT --- */
.stApp {
    background-color: #000000; /* Pure Black Background */
    color: #FFFFFF;
}
/* --- 2. CONTAINER STYLING (The "Cards") --- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #121212; /* Very Dark Grey Card */
    border: 1px solid #333333; /* Subtle Border */
    border-radius: 10px;
}
/* --- 3. INPUT FIELDS (Text, Areas, Selects) --- */
/* Make inputs blend in with a dark background and white text */
.stTextInput > div > div > input, 
.stTextArea > div > div > textarea, 
.stSelectbox > div > div > div {
    background-color: #1E1E1E !important; 
    color: #FFFFFF !important;
    border: 1px solid #444444 !important;
}
/* Labels must be white */
.stTextInput > label, .stTextArea > label, .stSelectbox > label, .stFileUploader > label, .stCheckbox > label {
    color: #FFFFFF !important;
    font-weight: 600;
}
/* --- 4. BUTTONS (Monochrome) --- */
/* Primary Buttons (Get Location, Submit) -> White Text, Dark Grey BG, White Border */
div.stButton > button {
    background-color: #000000 !important;
    color: #FFFFFF !important;
    border: 1px solid #FFFFFF !important;
    transition: all 0.3s ease;
}
div.stButton > button:hover {
    background-color: #FFFFFF !important;
    color: #000000 !important; /* Invert on hover */
    border: 1px solid #FFFFFF !important;
}
/* --- 5. METRICS (Latitude/Longitude) --- */
div[data-testid="stMetricValue"] {
    color: #FFFFFF !important; /* White numbers */
}
div[data-testid="stMetricLabel"] {
    color: #AAAAAA !important; /* Light Grey labels */
}
/* --- 6. TOASTS & NOTIFICATIONS --- */
div[data-testid="stToast"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# --- CACHED RESOURCES ---
@st.cache_resource
def load_clip_model():
    """Loads and caches the CLIP pipeline to prevent reloading."""
    try:
        # UPGRADE: Using transformers pipeline as requested
        return pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
    except Exception as e:
        st.error(f"Failed to load AI Model: {e}")
        return None

@st.cache_resource
def load_orchestrator():
    """Loads the main Grievance Pipeline."""
    return GrievanceOrchestrator()

@st.cache_resource
def get_db_handler():
    """Connects to MongoDB."""
    return DatabaseHandler()

# --- HELPER: VOICE TRANSCRIPTION ---
def transcribe_audio(audio_file, lang_code="en-IN"):
    """
    Transcribes audio from a file-like object using Google Speech Recognition.
    """
    try:
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = r.record(source)
            # Transcribe using Google (Handles Indian accents well)
            text = r.recognize_google(audio_data, language=lang_code)
            return text
    except Exception as e:
        return None
# --- INITIALIZATION ---
if 'clip_classifier' not in st.session_state:
    st.session_state.clip_classifier = load_clip_model()

if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = load_orchestrator()

if 'db' not in st.session_state:
    st.session_state.db = get_db_handler()

# --- HEADER ---
st.title("📖 Tarp-Project MVP")
st.markdown("### *Your Voice, Our Action.*")
st.markdown("---")

# --- MAIN TABS ---
tab_individual, tab_batch, tab_track = st.tabs(["🎫 Report Grievance", "📂 Batch Upload", "🔍 Track Status"])

# ==========================================
# TAB 1: INDIVIDUAL REPORT (REFACTOREDUI)
# ==========================================
with tab_individual:
    # --- LOGIC: PENDING VOICE TEXT ---
    if "pending_voice_text" in st.session_state and st.session_state.pending_voice_text:
        st.session_state["grievance_description_area"] = st.session_state.pending_voice_text
        del st.session_state.pending_voice_text

    # --- 3-COLUMN GRID LAYOUT ---
    # --- 3-COLUMN GRID LAYOUT ---
    col_details, col_media, col_location = st.columns([1, 0.8, 1.2], gap="large")

    # --- COLUMN 1: TYPE & DETAILS ---
    with col_details:
        with st.container(border=True):
            st.subheader("📝 Grievance Details")
            user_email = st.text_input("📧 Email Address:", placeholder="yourname@example.com")
            grievance_text = st.text_area(
                "Describe your issue in detail:",
                height=250,
                placeholder="e.g., There is a large pothole on Main Street...",
                key="grievance_description_area"
            )

    # --- COLUMN 2: EVIDENCE & VOICE ---
    with col_media:
        with st.container(border=True):
            st.subheader("📸 Evidence & Voice")
            uploaded_file = st.file_uploader("Upload Visual Proof", type=["jpg", "png", "jpeg"])
            
            st.markdown("---")
            st.markdown("**🎤 Voice Assistant**")
            
            # Use columns inside the evidence column for compactness? No, simplified.
            lang_choice = st.selectbox(
                "Language",
                ["English (India)", "Tamil (தமிழ்)", "Hindi (हिंदी)"],
                label_visibility="collapsed"
            )
            lang_map = {"English (India)": "en-IN", "Tamil (தமிழ்)": "ta-IN", "Hindi (हिंदी)": "hi-IN"}
            selected_code = lang_map[lang_choice]

            audio_value = st.audio_input("Record Grievance")
            
            # Voice Logic
            if audio_value:
                file_id = f"{audio_value.name}_{audio_value.size}"
                if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != file_id:
                    with st.spinner("✍️ Transcribing..."):
                        text = transcribe_audio(audio_value, lang_code=selected_code)
                        if text:
                            st.session_state.pending_voice_text = text
                            st.session_state.last_audio_id = file_id
                            st.rerun()

            # --- IMAGE VERIFICATION LOGIC (MOVED HERE) ---
            final_image_str = None
            verification_score = 0.0
            ai_status = "Not Checked"
            
            if uploaded_file and grievance_text:
                try:
                    image = Image.open(uploaded_file)
                    image.thumbnail((800, 800))
                    if st.session_state.clip_classifier:
                         st.caption("🔍 Verifying Image Relevance...")
                         common_issues = ["fire accident", "water logging or flood", "pothole or damaged road", "garbage dump", "street light issue"]
                         active_negatives = [issue for issue in common_issues if issue.split()[0] not in grievance_text.lower()]
                         final_negatives = active_negatives + ["person or selfie", "text document", "object"]
                         all_candidates = [grievance_text[:77]] + final_negatives
                         
                         results = st.session_state.clip_classifier(image, candidate_labels=all_candidates)
                         match_score = next((r['score'] for r in results if r['label'] == grievance_text[:77]), 0.0)
                         verification_score = match_score * 100
                         
                         if match_score > 0.30:
                             st.success(f"✅ AI Verified: {verification_score:.1f}% Match")
                             ai_status = "Verified"
                         else:
                             st.warning(f"⚠️ Low Match: {verification_score:.1f}%")
                             ai_status = "Flagged"
                except Exception as e:
                    st.warning(f"Verification Error: {e}")


    # --- COLUMN 3: LOCATION INTELLIGENCE ---
    with col_location:
        with st.container(border=True):
            st.subheader("📍 Location Intelligence")
            
            # Session State Setup
            if 'lat' not in st.session_state: st.session_state['lat'] = 12.9165
            if 'lon' not in st.session_state: st.session_state['lon'] = 79.1325
            if 'loc_locked' not in st.session_state: st.session_state['loc_locked'] = False
            
            # GPS Logic
            # 1. The Trigger Button
            if st.button("📍 Get My Current Location", key="btn_get_loc"):
                st.session_state['fetching_location'] = True

            # 2. The Conditional Execution (Persists across reruns)
            if st.session_state.get('fetching_location', False):
                st.info("📡 Requesting signals from satellites... (Please Allow 'Location' in browser)")
                
                # Call the GPS function only when flag is True
                gps_data = location_manager.get_user_gps()
                
                if gps_data:
                    # Data Found! Lock it and turn off fetching
                    coords = gps_data.get('coords', {})
                    if coords:
                        st.session_state['lat'] = coords.get('latitude')
                        st.session_state['lon'] = coords.get('longitude')
                        st.session_state['loc_locked'] = True
                        st.session_state['fetching_location'] = False # Stop fetching
                        st.rerun() # Force refresh to show the map
            
            # 3. Low-Level Helper
            with st.expander("⚠️ Location not updating?"):
                st.markdown("""
                1. Check the **Lock Icon 🔒** in your browser address bar.
                2. Ensure 'Location' is set to **Allow**.
                3. Reload the page and try again.
                """)
            
            manual_toggle = st.checkbox("🗺️ Switch to Manual", value=not st.session_state['loc_locked'])
            if manual_toggle: 
                st.session_state['loc_locked'] = False

            # Metrics
            st.write("")
            col_lat, col_lon = st.columns(2)
            col_lat.metric("Latitude", f"{st.session_state['lat']:.4f}")
            col_lon.metric("Longitude", f"{st.session_state['lon']:.4f}")
            
            # Debug Expander
            with st.expander("🛠️ Debug: Raw GPS Data"):
                st.write(gps_data if 'gps_data' in locals() else "No Data")
            
            # Map
            st.map(pd.DataFrame({'lat': [st.session_state['lat']], 'lon': [st.session_state['lon']]}))

    # --- FINAL SUBMIT ACTION (FULL WIDTH) ---
    st.write("") # Spacer
    with st.container(border=False):
        submit_btn = st.button("🚀 Submit Individual Grievance", use_container_width=True)

        if submit_btn:
             # Prepare Data
             if user_email and "@" not in user_email:
                 st.warning("Invalid Email")
             elif not grievance_text:
                 st.warning("Please describe the issue")
             else:
                 with st.spinner("🚀 Submitting..."):
                     # Image Setup (Re-read as needed for safe save)
                     if uploaded_file:
                         try:
                             uploaded_file.seek(0)
                             img_save = Image.open(uploaded_file)
                             img_save.thumbnail((800, 800))
                             buf = io.BytesIO()
                             img_save.save(buf, format="JPEG")
                             final_image_str = base64.b64encode(buf.getvalue()).decode()
                         except: pass

                     # Pipeline
                     res = st.session_state.orchestrator.run_pipeline(grievance_text)
                     
                     packet = {
                         **res,
                         "user_email": user_email,
                         "original_text": grievance_text,
                         "has_image": bool(final_image_str),
                         "image_data": final_image_str,
                         # Use variables from Col 2 scope if defined there, need to be careful with scope.
                         # Variables defined in 'with col_media:' might not be available here if not initialized outside.
                         # Initialized them at top of 'with col_media'. Python scoping is function-level, so they SHOULD be available.
                         "verification_score": verification_score,
                         "ai_status": ai_status,
                         "gps": {"lat": st.session_state['lat'], "lon": st.session_state['lon']},
                         "status": "New",
                         "user_id": user_email or "anonymous",
                         "submission_type": "individual"
                     }
                     
                     success, tid = st.session_state.db.submit_complaint(packet)
                     if success:
                         st.balloons()
                         st.markdown(f"""
                            <div style="background-color: #22c55e; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                                <h3>✅ Grievance Submitted!</h3>
                                <p>Ticket ID: <strong>{tid}</strong></p>
                            </div>
                         """, unsafe_allow_html=True)
                     else:
                         st.error("Submission Failed.")

# ==========================================
# TAB 2: BATCH UPLOAD
# ==========================================
with tab_batch:
    st.subheader("📂 Bulk Grievance Processor")
    st.caption("Upload a JSON file containing multiple grievances.")
    
    uploaded_batch = st.file_uploader("Upload JSON File", type=['json'], key="batch_upload")
    
    if uploaded_batch:
        if st.button("Run Batch Analysis & Upload", type="primary"):
            try:
                data = json.load(uploaded_batch)
                
                # Validation: Ensure it's a list
                if not isinstance(data, list):
                    st.error("Invalid JSON format. Expected a list of objects.")
                    st.stop()
                    
                st.info(f"Processing {len(data)} complaints...")
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                success_count = 0
                
                for i, item in enumerate(data):
                    # Robust key extraction
                    txt = item.get('text', item.get('complaint', item.get('description', '')))
                    
                    if not txt:
                        continue # Skip empty items
                        
                    # 1. Run Pipeline
                    status_text.text(f"Analyzing item {i+1}/{len(data)}...")
                    res = st.session_state.orchestrator.run_pipeline(txt)
                    
                    # 2. Add Metadata & GPS
                    lat = 12.9716 + random.uniform(-0.05, 0.05)
                    lon = 77.5946 + random.uniform(-0.05, 0.05)
                    
                    final_packet = {
                        **item, # Original data
                        **res,  # Pipeline results
                        "has_image": False,
                        "verification_score": 0.0,
                        "gps": {"lat": lat, "lon": lon},
                        "status": "New",
                        "user_id": "batch_upload",
                        "submission_type": "batch"
                    }
                    
                    # 3. Save to DB IMMEDIATELY
                    success, tid = st.session_state.db.submit_complaint(final_packet)
                    if success:
                        success_count += 1
                        final_packet['_id'] = tid
                    
                    results.append(final_packet)
                    progress_bar.progress((i + 1) / len(data))
                
                status_text.text("Processing Complete!")
                st.success(f"✅ Successfully processed and uploaded {success_count}/{len(data)} complaints.")
                
                # Show Summary Dictionary
                if results:
                    df = pd.DataFrame(results)
                    # Filter for display
                    display_cols = ['generated_id', 'category', 'priority', 'cci', 'status'] if 'generated_id' in df.columns else ['category', 'priority', 'cci', 'status'] 
                    # Use standard columns if generated_id is missing (from db response) - actually db returns string ID, we put it in _id
                    
                    st.dataframe(df.head(10))
                    
                    with st.expander("View Full Batch Results"):
                         st.json(results)
                
            except Exception as e:
                st.error(f"Batch Processing Error: {e}")

# ==========================================
# TAB 3: TRACK STATUS
# ==========================================
with tab_track:
    st.subheader("Track Your Complaint Status")
    st.write("Enter your Ticket ID below to see real-time updates from the Action Center.")
    
    search_id = st.text_input("Enter your Ticket ID", placeholder="Paste the ID here... (e.g., 65c4...)")
    
    if st.button("🔍 Search Ticket", use_container_width=True):
        if not search_id:
            st.warning("Please enter a Ticket ID.")
        elif not st.session_state.db.is_connected:
             st.error("Database is currently offline. Cannot search.")
        else:
            try:
                # Convert string to ObjectId
                obj_id = ObjectId(search_id.strip())
                
                # Query DB
                ticket = st.session_state.db.collection.find_one({"_id": obj_id})
                
                if ticket:
                    # Status Badge Color
                    status = ticket.get('status', 'New')
                    status_color = "#22C55E" if status == "Resolved" else "#F59E0B" if status == "In Progress" else "#3B82F6"
                    
                    # Display Card
                    st.markdown(f"""
                        <div class="tracker-card">
                            <h3 style="margin-top:0;">Ticket Details</h3>
                            <p><strong>ID:</strong> <span style="font-family:monospace;">{search_id}</span></p>
                            <p><strong>Status:</strong> <span style="background-color:{status_color}; color:white; padding: 4px 8px; border-radius:4px; font-weight:bold;">{status}</span></p>
                            <p><strong>Category:</strong> {ticket.get('category', 'Unclassified')}</p>
                            <p><strong>Priority:</strong> {ticket.get('priority', 'Medium')}</p>
                            <hr>
                            <p><strong>Description:</strong><br>{ticket.get('text', 'No description provided.')}</p>
                            <br>
                            <div style="background-color:#F3F4F6; padding:10px; border-radius:6px;">
                                <p style="margin:0; font-size:0.9em; color:#4B5563;"><strong>👮 Admin Remarks:</strong></p>
                                <p style="margin-top:5px; color:#111;">{ticket.get('admin_comment', 'No updates yet from the control room.')}</p>
                            </div>
                            <p style="text-align:right; font-size:0.8em; color:#9CA3AF; margin-top:10px;">Last Updated: {ticket.get('updated_at', 'Just now')}</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("❌ Ticket ID not found. Please check and try again.")
                    
            except Exception as e:
                st.error("❌ Invalid Ticket ID format. Please ensure you copied the exact ID.")

# --- FOOTER ---
st.markdown("---")
st.caption("Powered by Transformers, MongoDB & Streamlit")
