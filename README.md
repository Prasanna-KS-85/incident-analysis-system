# 🏛️ Civic Sentinel 
### Explainable Multi-Agent Decision Intelligence Framework for Context-Aware Citizen Grievance Prioritization (TARP)
**"From Multilingual Report to Geospatial Response in Seconds."**

Civic Sentinel is an AI-powered civic grievance redressal system. It receives citizen complaints via text, voice, or image, processes them through a multi-agent NLP pipeline, scores each using a novel **Civil Criticality Index (CCI)**, and presents actionable data to administrators via a 3D geospatial command center.

---

## 🚀 The Problem & The Solution
**The Problem:** Traditional grievance portals function as static lists. Minor noise complaints are treated identically to life-threatening gas leaks, creating dangerous dispatch bottlenecks and vague location reporting.

**The Solution:** Civic Sentinel applies AI-based triage. It translates regional languages, classifies the emergency, analyzes sentiment, detects urgency, and calculates the optimal driving route for emergency responders—all before human intervention is required.

---

## 🧠 Multi-Agent Pipeline Architecture
The system operates on a monolithic, sequential multi-agent pipeline:

1.  🌐 **Translation Agent:** Auto-detects regional languages (e.g., Tamil, Hindi) and translates them to English using the Google Translator API.
2.  🏷️ **Classification Agent:** A fine-tuned DistilBERT model that categorizes the grievance into 1 of 11 municipal categories (e.g., Public Safety, Sanitation).
3.  😠 **Sentiment Agent:** Utilizes NLTK VADER to evaluate the citizen's frustration/anger levels.
4.  🚨 **Urgency Agent:** A regex-based engine that detects critical keywords while intelligently handling negations (e.g., "Fire" vs. "No Fire").
5.  ⚖️ **Decision Agent (CCI):** Synthesizes outputs from all agents to compute the **Civil Criticality Index (0-10)** and assigns a Priority Label (High, Medium, Low).

---

## 🌟 Core Features
-   **Multimodal Citizen Portal:** Browser-based GPS locking (<10m accuracy), voice dictation, and image evidence upload with zero-shot CLIP AI verification.
-   **3D Geospatial Command Center:** Real-time dashboard using PyDeck to visualize incident density and departmental jurisdiction across the city.
-   **The "Navigator" Dispatch Engine:** Calculates the fastest driving routes from the nearest emergency station to the incident using the Mapbox Directions API.
-   **Automated Loop Closure:** Backend event triggers serialize official HTML email updates to citizens upon ticket resolution.

---

## ⚙️ Installation & Setup Guide

### 1. Prerequisites
-   Python 3.9, 3.10, or 3.11
-   A MongoDB Atlas account
-   A Mapbox Public Access Token
-   An App Password for a Gmail account (for automated emails)

### 2. Clone the Repository
```bash
git clone https://github.com/Prasanna-KS-85/TARP-Project.git
cd TARP-Project
```

### 3. Virtual Environment & Dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install deep-translator nltk fpdf certifi
```

### 4. ⚠️ CRITICAL: ML Model Setup (File Size Restriction)
Due to GitHub's strict 100MB file size limit, the fine-tuned DistilBERT model (`model.safetensors`) is **not included** in this repository.
To run the classification agent, you must:

1.  Obtain the `bert_brain/` folder containing the model weights and tokenizer configurations.
2.  Place the entire `bert_brain/` folder inside the following directory:
    ```
    3_agents/classification_agent/
    ```

### 5. Environment Variables & Secrets
Create a `.streamlit` folder in the root directory and add a `secrets.toml` file:

```toml
# .streamlit/secrets.toml
[general]
mapbox_token = "YOUR_MAPBOX_PUBLIC_TOKEN"
```

-   Update `utils/db_handler.py` with your MongoDB URI.
-   Update `admin_dashboard.py` with your `SENDER_EMAIL` and `APP_PASSWORD`.

---

## 💻 Running the Application
The system requires two concurrent Streamlit servers. Open two terminal windows:

**Terminal 1: Start the Citizen Portal**
```bash
streamlit run citizen_portal.py
```

**Terminal 2: Start the Admin Command Center**
```bash
streamlit run admin_dashboard.py
```

---

## 🔮 Future Roadmap (Phase 2)
-   **Community Shield:** Geo-fenced SMS alerts to warn citizens within 500m of active critical hazards.
-   **XAI Verification Agent:** Weather and traffic API integrations to automatically detect and flag "fake" or "spam" reports.
-   **Drone Dispatch Simulation:** Real-time calculation of "as-the-crow-flies" routing for survey drones.

---

> *Developed for Technical Answers for Real-world Problems (TARP) Academic Evaluation.*
