import streamlit as st
import requests
import math

# --- 1. HARDCODED EMERGENCY STATIONS (Vellore, TN) ---
# In a real app, this would come from a database.
EMERGENCY_STATIONS = {
    "Fire": [
        {"name": "Vellore Central Fire Station", "lat": 12.9165, "lon": 79.1325}, 
        {"name": "Katpadi Fire & Rescue", "lat": 12.9680, "lon": 79.1450}
    ],
    "Medical": [
        {"name": "Govt. Vellore Medical College Hospital (Adukkamparai)", "lat": 12.8750, "lon": 79.1150},
        {"name": "Christian Medical College (CMC)", "lat": 12.9245, "lon": 79.1350}
    ],
    "Civil": [
        {"name": "Vellore City Police HQ", "lat": 12.9200, "lon": 79.1300},
        {"name": "Collectorate Office", "lat": 12.9300, "lon": 79.1400}
    ]
}

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points on the Earth surface.
    """
    R = 6371  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) * math.sin(d_lat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) * math.sin(d_lon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def find_nearest_station(incident_lat, incident_lon, category):
    """
    Finds the nearest emergency station for a given incident type.
    
    Args:
        incident_lat (float): Latitude of incident.
        incident_lon (float): Longitude of incident.
        category (str): One of 'Fire', 'Medical', 'Civil'.
        
    Returns:
        dict: Closest station object with 'name', 'lat', 'lon', and 'distance_km'.
    """
    if category not in EMERGENCY_STATIONS:
        # Fallback to Civil if category unknown
        category = "Civil"
        
    stations = EMERGENCY_STATIONS[category]
    nearest = None
    min_dist = float('inf')
    
    for station in stations:
        dist = haversine_distance(incident_lat, incident_lon, station['lat'], station['lon'])
        if dist < min_dist:
            min_dist = dist
            nearest = station.copy()
            nearest['distance_km'] = round(dist, 2)
            
    return nearest

def get_route_geometry(start_lat, start_lon, end_lat, end_lon):
    """
    Fetches driving route geometry from Mapbox Directions API.
    
    Args:
        start_lat, start_lon: Starting point (Incident).
        end_lat, end_lon: Destination (Emergency Station).
        
    Returns:
        dict: GeoJSON geometry of the route or None if failed.
    """
    try:
        # 1. Securely fetch token
        mapbox_token = st.secrets["general"]["mapbox_token"]
    except KeyError:
        st.error("🚨 Mapbox Token Missing! specific 'mapbox_token' in .streamlit/secrets.toml")
        return None
    except FileNotFoundError:
        st.error("🚨 Secrets File Missing! Create .streamlit/secrets.toml")
        return None

    # 2. Construct API URL
    # Mapbox uses Longitude,Latitude format
    coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coords}"
    
    params = {
        "geometries": "geojson",
        "overview": "full",
        "access_token": mapbox_token
    }
    
    # 3. Request
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if response.status_code == 200 and "routes" in data and len(data["routes"]) > 0:
            return data["routes"][0]["geometry"]
        else:
            print(f"Routing Error: {data.get('message', 'Unknown Error')}")
            return None
            
    except Exception as e:
        print(f"API Request Failed: {e}")
        return None
