#!/bin/bash
echo "Starting Civic Sentinel Services..."
# Start the Citizen Portal in the background
streamlit run citizen_portal.py --server.port=8501 --server.address=0.0.0.0 &

# Start the Admin Dashboard in the foreground
streamlit run admin_dashboard.py --server.port=8502 --server.address=0.0.0.0
