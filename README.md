# 🚨 Vehicle Checkpoint Geo-Monitoring & Live Attendance System
> Thanjavur Town Sub-Division Real-Time Police Attendance & Geofencing Platform

Built with **Python**, **Streamlit**, **Folium**, and **SQLite**.

## 🌟 Key Features
- **Flexible Headcount Roster**: Assign variable personnel per post (minimum 1 to any number).
- **Dynamic Completion Status**: 100% Green for full attendance, Amber for partial, Red for 0% or Out-of-Bounds violations.
- **Pure Python Haversine Calculation**: Precise distance computation within 100m radius geofence.
- **Mobile & Field Check-in**: Live GPS coordinates, desktop simulator testing controls, and mandatory selfie capture.
- **Supervisory Dashboard**: Interactive Leaflet Map with dynamic geofence color badges, Station Accordion Personnel Audit, and 1-click CSV Report Export.

## 📍 Predefined Checkpoints & Exact GPS Coordinates (Thanjavur Sub-Division)
- **East PS**:
  - `T-Square`: `10.778028° N, 79.152972° E`
  - `கீழவாசல் 4 ரோடு (Keelavasal 4 Road)`: `10.789778° N, 79.142222° E`
- **West PS**:
  - `கோடியம்மன் கோவில் (Kodiamman Kovil)`: `10.812444° N, 79.139083° E`
  - `பழைய பேருந்து நிலையம் (Old Bus Stand)`: `10.787583° N, 79.138361° E`
- **South PS**:
  - `அண்ணா நகர் Junction (Anna Nagar Jn)`: `10.762528° N, 79.140361° E`
  - `ராமநாதன் ரவுண்டானா (Ramanathan Roundana)`: `10.772560° N, 79.132430° E`
- **TMCH PS**:
  - `வெற்றி ஈ ஸ்கொயர் (Vetri E Square)`: `10.752750° N, 79.109583° E`
  - `ரஹ்மான் நகர் Junction (Rahman Nagar Jn)`: `10.757111° N, 79.099444° E`

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
