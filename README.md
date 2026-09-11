# 🚨 Vehicle Checkpoint Geo-Monitoring & Live Attendance System
> Thanjavur Town Sub-Division Real-Time Police Attendance & Geofencing Platform

Built with **Python**, **Streamlit**, **Folium**, and **SQLite**.

## 🌟 Key Features
- **Flexible Headcount Roster**: Assign variable personnel per post (minimum 1 to any number).
- **Dynamic Completion Status**: 100% Green for full attendance, Amber for partial, Red for 0% or Out-of-Bounds violations.
- **Pure Python Haversine Calculation**: Precise distance computation within 100m radius geofence.
- **Mobile & Field Check-in**: Live GPS coordinates, desktop simulator testing controls, and mandatory selfie capture.
- **Supervisory Dashboard**: Interactive Leaflet Map with dynamic geofence color badges, Station Accordion Personnel Audit, and 1-click CSV Report Export.

## 📍 Predefined Checkpoints (Thanjavur Sub-Division)
- **East PS**: T-Square & Keelavasal 4 Road
- **West PS**: Kodiamman Kovil & Old Bus Stand
- **South PS**: Anna Nagar Jn & Ramanathan Roundana
- **TMCH PS**: New Bus Stand & Rahman Nagar Jn

## 🚀 Quick Setup & Run

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adidarsan1/traffic-junction-checkpoints.git
   cd traffic-junction-checkpoints
   ```

2. **Create virtual environment & install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install streamlit pandas folium streamlit-folium
   ```

3. **Run the Streamlit Web App:**
   ```bash
   streamlit run app.py
   ```
