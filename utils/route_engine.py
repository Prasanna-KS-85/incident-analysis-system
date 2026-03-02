import streamlit as st
import googlemaps
import polyline
import math

def get_gmaps_client():
    """Initializes and returns the Google Maps client using Streamlit secrets."""
    try:
        api_key = st.secrets["general"]["google_maps_api_key"]
        return googlemaps.Client(key=api_key)
    except KeyError:
        st.error("Google Maps API key not found in secrets.toml")
        return None

def get_facility_type(category, grievance_text=""):
    """Maps the grievance to a Google Places Type and a specific search keyword."""
    cat = str(category).lower()
    text = str(grievance_text).lower()
    
    # 1. Medical Emergencies
    if "medical" in cat or "health" in cat or any(w in text for w in ["medical", "injury", "ambulance", "accident", "heart"]):
        return {"type": "hospital"}
        
    # 2. Fire Emergencies
    if "fire" in cat or any(w in text for w in ["fire", "smoke", "burn", "aag"]):
        return {"type": "fire_station"}
        
    # 3. Police / Law Enforcement
    if "crime" in cat or "safety" in cat or "security" in cat or any(w in text for w in ["police", "theft", "assault", "fight", "snatching"]):
        return {"type": "police"}
        
    # 4. Civic Issues - Electricity
    if any(w in text for w in ["light", "electricity", "power", "transformer", "wire"]):
        return {"type": "local_government_office", "keyword": "Electricity Board TNEB BESCOM"}
        
    # 5. Civic Issues - Water & Flooding
    if any(w in text for w in ["water", "flood", "pipe", "drain", "clogging"]):
        return {"type": "local_government_office", "keyword": "Water Board CMWSSB"}
        
    # 6. Civic Issues - Roads & Sanitation
    if any(w in text for w in ["road", "pothole", "garbage", "trash"]):
        return {"type": "local_government_office", "keyword": "Municipal Corporation"}
        
    # 7. Animal Rescue
    if any(w in text for w in ["animal", "deer", "dog", "cow"]):
        return {"type": "veterinary_care", "keyword": "Animal Rescue Blue Cross"}
        
    # Default Fallback for anything else
    return {"type": "local_government_office", "keyword": "Municipal Corporation"}

def find_nearest_station(incident_lat, incident_lon, category, grievance_text=""):
    """Dynamically finds the nearest appropriate facility using Google Places API."""
    gmaps = get_gmaps_client()
    if not gmaps:
        return None

    facility_info = get_facility_type(category, grievance_text)
    fac_type = facility_info["type"]
    fac_keyword = facility_info.get("keyword") # This might be None
    
    try:
        # Build search parameters dynamically
        search_params = {
            "location": (incident_lat, incident_lon),
            "radius": 10000,
            "type": fac_type
        }
        if fac_keyword:
            search_params["keyword"] = fac_keyword
            
        places_result = gmaps.places_nearby(**search_params)
        
        if not places_result.get('results'):
            return None
            
        nearest = places_result['results'][0]
        return {
            "name": nearest['name'],
            "lat": nearest['geometry']['location']['lat'],
            "lon": nearest['geometry']['location']['lng'],
            "type": fac_type
        }
    except Exception as e:
        st.error(f"Error fetching nearby places: {e}")
        return None
        
def get_route_geometry(start_lat, start_lon, end_lat, end_lon):
    """Fetches the route from Google Directions API and decodes the polyline for PyDeck."""
    gmaps = get_gmaps_client()
    if not gmaps:
        return None

    try:
        directions_result = gmaps.directions(
            (start_lat, start_lon),
            (end_lat, end_lon),
            mode="driving",
            departure_time="now" # Takes current traffic into account
        )
        
        if not directions_result:
            return None
            
        # Extract the encoded polyline
        encoded_polyline = directions_result[0]['overview_polyline']['points']
        
        # Decode the polyline into a list of (lat, lon) tuples
        decoded_points = polyline.decode(encoded_polyline)
        
        # PyDeck requires [lon, lat] format, so we must reverse the tuples
        pydeck_path = [[lon, lat] for lat, lon in decoded_points]
        
        # Return in a format ready for PyDeck's PathLayer
        return {
            "geometry": {
                "coordinates": pydeck_path
            },
            "distance_text": directions_result[0]['legs'][0]['distance']['text'],
            "duration_text": directions_result[0]['legs'][0]['duration']['text']
        }
    except Exception as e:
        st.error(f"Error calculating route: {e}")
        return None
