import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import sqlite3
import math
import datetime
import base64
from io import BytesIO

# ---------------------------------------------------------
# Page Configuration & Modern Aesthetics Setup
# ---------------------------------------------------------
st.set_page_config(
    page_title="Thanjavur Police | Vehicle Checkpoint Geo-Monitoring System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Police Dashboard Design System
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1E3A8A 100%);
        padding: 24px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-header h1 {
        font-weight: 800;
        font-size: 2.2rem;
        margin: 0;
        color: #F8FAFC;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #94A3B8;
        margin: 6px 0 0 0;
        font-size: 1.05rem;
    }
    
    .stat-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: transform 0.2s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
    }
    
    .stat-number {
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 4px;
    }
    
    .stat-label {
        color: #94A3B8;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-present {
        background-color: #065F46;
        color: #34D399;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #059669;
    }
    
    .badge-oob {
        background-color: #7F1D1D;
        color: #FCA5A5;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        border: 1px solid #DC2626;
    }
    
    .badge-pending {
        background-color: #334155;
        color: #94A3B8;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #0F172A;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 8px;
        font-weight: 600;
        color: #94A3B8;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Predefined Master Data & Pure Python Haversine Formula
# ---------------------------------------------------------
CHECKPOINTS = [
    # East PS
    {"id": 1, "station": "East PS", "name": "T-Square", "lat": 10.7938, "lon": 79.1408, "radius": 100},
    {"id": 2, "station": "East PS", "name": "கீழவாசல் 4 ரோடு (Keelavasal 4 Road)", "lat": 10.7942, "lon": 79.1475, "radius": 100},
    # West PS
    {"id": 3, "station": "West PS", "name": "கோடியம்மன் கோவில் (Kodiamman Kovil)", "lat": 10.7998, "lon": 79.1332, "radius": 100},
    {"id": 4, "station": "West PS", "name": "பழைய பேருந்து நிலையம் (Old Bus Stand)", "lat": 10.7865, "lon": 79.1382, "radius": 100},
    # South PS
    {"id": 5, "station": "South PS", "name": "அண்ணா நகர் Junction (Anna Nagar Jn)", "lat": 10.7762, "lon": 79.1348, "radius": 100},
    {"id": 6, "station": "South PS", "name": "ராமநாதன் ரவுண்டானா (Ramanathan Roundana)", "lat": 10.7818, "lon": 79.1360, "radius": 100},
    # TMCH PS
    {"id": 7, "station": "TMCH PS", "name": "புதிய பேருந்து நிலையம் (New Bus Stand)", "lat": 10.7585, "lon": 79.1082, "radius": 100},
    {"id": 8, "station": "TMCH PS", "name": "ரஹ்மான் நகர் Junction (Rahman Nagar Jn)", "lat": 10.7674, "lon": 79.1176, "radius": 100}
]

RANKS = ["SI", "SSI", "HC", "Gr-I PC", "PC"]

def calculate_haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in meters using Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ---------------------------------------------------------
# Database Initialization & SQLite Data Layer
# ---------------------------------------------------------
DB_FILE = "checkpoint_monitoring.db"

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roster (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duty_date TEXT,
            station TEXT,
            checkpoint_id INTEGER,
            officer_name TEXT,
            rank TEXT,
            phone TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duty_date TEXT,
            checkpoint_id INTEGER,
            officer_name TEXT,
            timestamp TEXT,
            latitude REAL,
            longitude REAL,
            distance_meters REAL,
            accuracy_meters REAL,
            status TEXT,
            photo_b64 TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Database Helper Functions
def save_roster_for_checkpoint(duty_date, station, checkpoint_id, officer_list):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roster WHERE duty_date = ? AND checkpoint_id = ?", (duty_date, checkpoint_id))
    for officer in officer_list:
        if officer.get("officer_name") and officer.get("officer_name").strip():
            cursor.execute(
                "INSERT INTO roster (duty_date, station, checkpoint_id, officer_name, rank, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (duty_date, station, checkpoint_id, officer["officer_name"].strip(), officer.get("rank", "PC"), officer.get("phone", ""))
            )
    conn.commit()
    conn.close()

def seed_demo_roster(duty_date):
    demo_data = {
        1: [("SI", "K. Ramesh", "9443100001"), ("HC", "M. Sundaram", "9443100002"), ("PC", "V. Siva", "9443100003")],
        2: [("SSI", "R. Rajan", "9443100004"), ("Gr-I PC", "P. Kumar", "9443100005"), ("PC", "S. Karthik", "9443100006")],
        3: [("SI", "T. Vijay", "9443100007"), ("HC", "A. Selvam", "9443100008"), ("PC", "N. Manikandan", "9443100009")],
        4: [("SSI", "G. Murugan", "9443100010"), ("Gr-I PC", "K. Dinesh", "9443100011"), ("PC", "R. Balaji", "9443100012")],
        5: [("SI", "P. Velu", "9443100013"), ("HC", "C. Marimuthu", "9443100014"), ("PC", "K. Anand", "9443100015")],
        6: [("SSI", "V. Thangavel", "9443100016"), ("Gr-I PC", "S. Prakash", "9443100017"), ("PC", "M. Vignesh", "9443100018")],
        7: [("SI", "D. Arumugam", "9443100019"), ("HC", "E. Baskaran", "9443100020"), ("PC", "J. Joseph", "9443100021")],
        8: [("SSI", "M. Ganesan", "9443100022"), ("Gr-I PC", "T. Saravanan", "9443100023"), ("PC", "P. Surya", "9443100024")]
    }
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM roster WHERE duty_date = ?", (duty_date,))
    for cp_id, officers in demo_data.items():
        cp_info = next(c for c in CHECKPOINTS if c["id"] == cp_id)
        for rank, name, phone in officers:
            cursor.execute(
                "INSERT INTO roster (duty_date, station, checkpoint_id, officer_name, rank, phone) VALUES (?, ?, ?, ?, ?, ?)",
                (duty_date, cp_info["station"], cp_id, name, rank, phone)
            )
    conn.commit()
    conn.close()

def get_roster(duty_date, checkpoint_id=None):
    conn = get_db()
    if checkpoint_id:
        df = pd.read_sql_query("SELECT * FROM roster WHERE duty_date = ? AND checkpoint_id = ?", conn, params=(duty_date, checkpoint_id))
    else:
        df = pd.read_sql_query("SELECT * FROM roster WHERE duty_date = ?", conn, params=(duty_date,))
    conn.close()
    return df

def get_checkins(duty_date):
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM checkins WHERE duty_date = ?", conn, params=(duty_date,))
    conn.close()
    return df

def save_checkin(duty_date, checkpoint_id, officer_name, timestamp, lat, lon, dist, accuracy, status, photo_b64):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO checkins (duty_date, checkpoint_id, officer_name, timestamp, latitude, longitude, distance_meters, accuracy_meters, status, photo_b64)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (duty_date, checkpoint_id, officer_name, timestamp, lat, lon, dist, accuracy, status, photo_b64))
    conn.commit()
    conn.close()

# ---------------------------------------------------------
# App Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <h1>Thanjavur Town Sub-Division</h1>
            <p>🚔 Real-Time Vehicle Checkpoint Geo-Monitoring & Live Attendance System</p>
        </div>
        <div style="text-align: right; background: rgba(255,255,255,0.1); padding: 8px 16px; border-radius: 12px;">
            <span style="font-size: 0.85rem; color: #60A5FA; font-weight: 700;">OPERATIONAL HOURS</span><br/>
            <span style="font-weight: 800; font-size: 1.1rem; color: #F8FAFC;">4:00 PM – 7:00 PM</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# App Navigation Tabs
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📋 Tab 1: Morning Duty Roster (Station Admin)",
    "📱 Tab 2: Field Officer Check-In (Mobile View)",
    "📊 Tab 3: Supervisory Live Dashboard (Supervisory View)"
])

# =========================================================
# TAB 1: MORNING DUTY ROSTER (STATION ADMIN)
# =========================================================
with tab1:
    st.subheader("📋 Station Morning Roster Assignment")
    st.caption("Station Administrators can assign any variable number of personnel (minimum 1) per checkpoint.")
    
    col_date, col_station, col_demo = st.columns([1, 1.5, 1.5])
    
    with col_date:
        selected_date = st.date_input("Select Duty Date", datetime.date.today(), key="tab1_date")
        duty_date_str = selected_date.strftime("%Y-%m-%d")
        
    with col_station:
        selected_station = st.selectbox(
            "Select Police Station",
            ["East PS", "West PS", "South PS", "TMCH PS"],
            key="tab1_station"
        )
        
    with col_demo:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("⚡ Quick Pre-Fill Demo Roster (3 Officers / Post)", use_container_width=True, type="secondary"):
            seed_demo_roster(duty_date_str)
            st.success(f"✅ Demo roster pre-filled for ALL 8 checkpoints on {duty_date_str}! (3 officers per post)")
            st.rerun()

    st.markdown("---")
    
    # Filter checkpoints for selected station
    station_cps = [cp for cp in CHECKPOINTS if cp["station"] == selected_station]
    
    for cp in station_cps:
        st.markdown(f"### 📍 Checkpoint #{cp['id']}: {cp['name']}")
        st.caption(f"Location: ({cp['lat']}, {cp['lon']}) | Geofence Radius: {cp['radius']}m")
        
        # Load existing roster entries
        existing_df = get_roster(duty_date_str, cp["id"])
        
        if not existing_df.empty:
            initial_data = existing_df[["rank", "officer_name", "phone"]].to_dict('records')
        else:
            # Default template row for flexible headcount
            initial_data = [
                {"rank": "SI", "officer_name": "", "phone": ""},
                {"rank": "HC", "officer_name": "", "phone": ""},
                {"rank": "PC", "officer_name": "", "phone": ""}
            ]
            
        edited_df = st.data_editor(
            initial_data,
            column_config={
                "rank": st.column_config.SelectboxColumn("Rank", options=RANKS, required=True, width="medium"),
                "officer_name": st.column_config.TextColumn("Officer Name", required=True, width="large"),
                "phone": st.column_config.TextColumn("Contact Phone Number", width="medium")
            },
            num_rows="dynamic",
            key=f"editor_cp_{cp['id']}_{duty_date_str}",
            use_container_width=True
        )
        
        col_save, col_spacer = st.columns([1, 3])
        with col_save:
            if st.button(f"💾 Save Roster for {cp['name']}", key=f"save_btn_{cp['id']}", type="primary"):
                # Filter non-empty officer names
                valid_officers = [row for row in edited_df if str(row.get("officer_name", "")).strip() != ""]
                if len(valid_officers) < 1:
                    st.warning("⚠️ Please assign at least 1 officer to save the roster.")
                else:
                    save_roster_for_checkpoint(duty_date_str, selected_station, cp["id"], valid_officers)
                    st.success(f"✅ Roster for Checkpoint #{cp['id']} updated ({len(valid_officers)} officers assigned)!")
        
        st.markdown("<br/>", unsafe_allow_html=True)
        
    st.markdown("---")
    st.subheader(f"📄 Summary Roster for {selected_station} on {duty_date_str}")
    current_roster_df = get_roster(duty_date_str)
    station_roster = current_roster_df[current_roster_df["station"] == selected_station]
    if not station_roster.empty:
        st.dataframe(station_roster[["checkpoint_id", "rank", "officer_name", "phone"]], use_container_width=True)
    else:
        st.info("No roster saved yet for this date & station. Click 'Quick Pre-Fill Demo Roster' above or save manually.")


# =========================================================
# TAB 2: FIELD OFFICER CHECK-IN (MOBILE OPTIMIZED VIEW)
# =========================================================
with tab2:
    st.subheader("📱 Field Officer Verification Check-In")
    st.caption("Perform live attendance verification with HTML5 Geolocation distance check & selfie snapshot.")
    
    checkin_date = datetime.date.today().strftime("%Y-%m-%d")
    
    # Step 1: Select Station -> Checkpoint
    c1, c2 = st.columns(2)
    with c1:
        st_select = st.selectbox("Step 1: Select Your Station", ["East PS", "West PS", "South PS", "TMCH PS"], key="tab2_station")
    
    cp_options = [cp for cp in CHECKPOINTS if cp["station"] == st_select]
    cp_dict = {f"CP #{cp['id']} - {cp['name']}": cp for cp in cp_options}
    
    with c2:
        cp_chosen_label = st.selectbox("Select Checkpoint Post", list(cp_dict.keys()), key="tab2_cp")
        selected_cp = cp_dict[cp_chosen_label]

    st.info(f"📍 **Target Location:** {selected_cp['name']} | **Center Coordinates:** `{selected_cp['lat']}, {selected_cp['lon']}` | **Geofence Radius:** `100 meters`")

    # Step 2: Select Officer Name dynamically from Roster
    roster_df = get_roster(checkin_date, selected_cp["id"])
    
    if roster_df.empty:
        st.warning(f"⚠️ No officers are assigned to **{selected_cp['name']}** in today's roster ({checkin_date}). Please ask Station Admin to populate Tab 1 or click 'Quick Pre-Fill Demo Roster'.")
    else:
        officer_options = [f"{row['rank']} {row['officer_name']} ({row['phone']})" for _, row in roster_df.iterrows()]
        selected_officer_str = st.selectbox("Step 2: Select Your Name from Roster", officer_options, key="tab2_officer")
        
        # Parse officer name
        officer_name_selected = selected_officer_str.split(" (")[0].strip()
        # Remove rank prefix if present for clean lookup
        for rank in RANKS:
            if officer_name_selected.startswith(rank):
                officer_name_selected = officer_name_selected[len(rank):].strip()
                break

        st.markdown("---")
        
        # Step 3: Fetch Live GPS Coordinates & Fallback Simulator
        st.subheader("Step 3: Geolocation Acquisition")
        
        use_simulator = st.checkbox("🖥️ Enable GPS Simulator / Manual Override (for Desktop Testing)", value=True, key="sim_toggle")
        
        if use_simulator:
            st.caption("Desktop Simulation Controls for testing distance calculations:")
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            
            if "sim_lat" not in st.session_state:
                st.session_state.sim_lat = selected_cp["lat"]
                st.session_state.sim_lon = selected_cp["lon"]
            
            with sim_col1:
                if st.button("🎯 Set GPS to Post Center (0m offset)", use_container_width=True):
                    st.session_state.sim_lat = selected_cp["lat"]
                    st.session_state.sim_lon = selected_cp["lon"]
            with sim_col2:
                if st.button("🟡 Set GPS Near Border (~80m offset)", use_container_width=True):
                    st.session_state.sim_lat = selected_cp["lat"] + 0.00072
                    st.session_state.sim_lon = selected_cp["lon"]
            with sim_col3:
                if st.button("🔴 Set GPS Out-of-Bounds (~160m offset)", use_container_width=True):
                    st.session_state.sim_lat = selected_cp["lat"] + 0.00144
                    st.session_state.sim_lon = selected_cp["lon"]
            
            g1, g2, g3 = st.columns(3)
            with g1:
                lat_input = st.number_input("Latitude", value=float(st.session_state.sim_lat), format="%.6f", key="input_lat")
            with g2:
                lon_input = st.number_input("Longitude", value=float(st.session_state.sim_lon), format="%.6f", key="input_lon")
            with g3:
                accuracy_input = st.number_input("Accuracy (meters)", value=10.0, step=1.0)
        else:
            # HTML5 Geolocation via browser JavaScript
            st.info("Browser Geolocation Active. If prompted, please allow location access.")
            lat_input = selected_cp["lat"]
            lon_input = selected_cp["lon"]
            accuracy_input = 15.0

        st.markdown("---")
        
        # Step 4: Live Selfie Snapshot
        st.subheader("Step 4: Live Verification Selfie")
        camera_photo = st.camera_input("📷 Take Verification Photo", key="camera_input")
        
        fallback_photo = None
        if camera_photo is None:
            fallback_photo = st.file_uploader("Or Upload Selfie Image (Fallback for browsers without webcams)", type=["jpg", "png", "jpeg"])
            
        final_photo = camera_photo if camera_photo is not None else fallback_photo

        st.markdown("---")
        
        # Step 5: Submission & Instant Verification
        if st.button("🚨 Submit Attendance & Verify Check-In", type="primary", use_container_width=True):
            # Check duplicate check-in
            checkins_today = get_checkins(checkin_date)
            existing_checkin = checkins_today[
                (checkins_today["checkpoint_id"] == selected_cp["id"]) & 
                (checkins_today["officer_name"] == officer_name_selected)
            ]
            
            if not existing_checkin.empty:
                st.error(f"❌ **Duplicate Submission Prevented!** Officer **{officer_name_selected}** has already checked in at this checkpoint today at **{existing_checkin.iloc[0]['timestamp']}**.")
            elif final_photo is None:
                st.warning("⚠️ **Selfie Photo Required!** Please capture a selfie using the camera above to proceed.")
            else:
                # Process selfie photo to base64
                image_bytes = final_photo.getvalue()
                photo_b64 = base64.b64encode(image_bytes).decode('utf-8')
                
                # Calculate distance
                dist = calculate_haversine(lat_input, lon_input, selected_cp["lat"], selected_cp["lon"])
                timestamp_now = datetime.datetime.now().strftime("%I:%M:%S %p")
                
                status_str = "Verified Present" if dist <= 100.0 else "Flagged Out-of-Bounds"
                
                # Save to database
                save_checkin(
                    checkin_date, selected_cp["id"], officer_name_selected,
                    timestamp_now, lat_input, lon_input, round(dist, 2),
                    accuracy_input, status_str, photo_b64
                )
                
                if status_str == "Verified Present":
                    st.balloons()
                    st.success(f"""
                    ### ✅ CHECK-IN VERIFIED SUCCESSFULLY!
                    - **Officer:** {officer_name_selected}
                    - **Status Tag:** `Verified Present`
                    - **Distance from Checkpoint Center:** `{dist:.1f} meters` (Inside 100m geofence)
                    - **Timestamp:** `{timestamp_now}`
                    """)
                else:
                    st.error(f"""
                    ### ⚠️ GEOFENCE VIOLATION DETECTED!
                    - **Officer:** {officer_name_selected}
                    - **Status Tag:** `Flagged Out-of-Bounds`
                    - **Distance from Checkpoint Center:** `{dist:.1f} meters` (**{dist - 100:.1f} meters OUTSIDE 100m geofence!**)
                    - **Timestamp:** `{timestamp_now}`
                    - *Notice: Event logged automatically for supervisory review.*
                    """)


# =========================================================
# TAB 3: SUPERVISORY LIVE DASHBOARD (SUPERVISORY VIEW)
# =========================================================
with tab3:
    st.subheader("📊 Supervisory Live Attendance & Geo-Fence Control Center")
    
    dash_date = st.date_input("Select Monitoring Date", datetime.date.today(), key="tab3_date").strftime("%Y-%m-%d")
    
    # Query current DB status
    df_roster_today = get_roster(dash_date)
    df_checkins_today = get_checkins(dash_date)
    
    total_assigned = len(df_roster_today)
    total_checked_in = len(df_checkins_today)
    total_verified = len(df_checkins_today[df_checkins_today["status"] == "Verified Present"]) if not df_checkins_today.empty else 0
    total_oob = len(df_checkins_today[df_checkins_today["status"] == "Flagged Out-of-Bounds"]) if not df_checkins_today.empty else 0
    
    # Key Metrics Cards Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #60A5FA;">{total_assigned}</div>
            <div class="stat-label">Assigned Officers Today</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #FBBF24;">{total_checked_in}</div>
            <div class="stat-label">Total Checked In</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #34D399;">{total_verified}</div>
            <div class="stat-label">Verified Present (In Bounds)</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #FCA5A5;">{total_oob}</div>
            <div class="stat-label">Out-of-Bounds Violations</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Interactive Map Section
    st.markdown("### 🗺️ Live Sub-Division Checkpoint Geo-Map (Thanjavur)")
    st.caption("Circles represent 100m geofences. Color Code: 🟢 Green = 100% Verified | 🟡 Amber = Partial Attendance | 🔴 Red = 0% Checked In or Out-of-Bounds Flagged")
    
    # Map Center: Thanjavur Town (~10.785, 79.135)
    m = folium.Map(location=[10.785, 79.135], zoom_start=13, tiles="CartoDB positron")
    
    # Add Checkpoint Geofence Circles
    for cp in CHECKPOINTS:
        cp_roster = df_roster_today[df_roster_today["checkpoint_id"] == cp["id"]]
        cp_checkins = df_checkins_today[df_checkins_today["checkpoint_id"] == cp["id"]] if not df_checkins_today.empty else pd.DataFrame()
        
        n_assigned = len(cp_roster)
        n_verified = len(cp_checkins[cp_checkins["status"] == "Verified Present"]) if not cp_checkins.empty else 0
        n_oob = len(cp_checkins[cp_checkins["status"] == "Flagged Out-of-Bounds"]) if not cp_checkins.empty else 0
        
        # Color coding logic
        if n_assigned > 0 and n_verified == n_assigned and n_oob == 0:
            circle_color = "#10B981"  # Green
            status_text = "🟢 100% Verified"
        elif n_verified > 0 and n_oob == 0:
            circle_color = "#F59E0B"  # Amber
            status_text = f"🟡 Partial ({n_verified}/{n_assigned})"
        else:
            circle_color = "#EF4444"  # Red
            status_text = f"🔴 Alert ({n_verified}/{n_assigned} Present, {n_oob} OOB)"
            
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px;">
            <b style="font-size: 1.1rem; color: #1E293B;">{cp['station']} - {cp['name']}</b><br/>
            <hr style="margin: 6px 0; border: none; border-top: 1px solid #CBD5E1;"/>
            <b>Status:</b> {status_text}<br/>
            <b>Assigned Personnel:</b> {n_assigned}<br/>
            <b>Verified Present:</b> {n_verified}<br/>
            <b>Out-of-Bounds:</b> {n_oob}<br/>
            <b>Geofence Radius:</b> 100m
        </div>
        """
        
        folium.Circle(
            location=[cp["lat"], cp["lon"]],
            radius=cp["radius"],
            color=circle_color,
            fill=True,
            fill_color=circle_color,
            fill_opacity=0.35,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{cp['station']} - {cp['name']} ({status_text})"
        ).add_to(m)
        
        # Fixed Checkpoint Marker Pin
        folium.Marker(
            location=[cp["lat"], cp["lon"]],
            popup=f"<b>Checkpoint Center:</b> {cp['name']}",
            icon=folium.Icon(color="darkblue", icon="shield", prefix="fa")
        ).add_to(m)

    # Add Officer Live Pins
    if not df_checkins_today.empty:
        for _, checkin in df_checkins_today.iterrows():
            is_present = checkin["status"] == "Verified Present"
            pin_color = "green" if is_present else "red"
            
            officer_popup = f"""
            <div style="font-family: Arial, sans-serif; width: 200px;">
                <b style="color: {'#059669' if is_present else '#DC2626'};">{checkin['officer_name']}</b><br/>
                <b>Punch Time:</b> {checkin['timestamp']}<br/>
                <b>Distance Offset:</b> {checkin['distance_meters']:.1f}m<br/>
                <b>Status:</b> {checkin['status']}<br/>
            </div>
            """
            
            folium.Marker(
                location=[checkin["latitude"], checkin["longitude"]],
                popup=folium.Popup(officer_popup, max_width=250),
                icon=folium.Icon(color=pin_color, icon="user", prefix="fa"),
                tooltip=f"Officer {checkin['officer_name']} ({checkin['status']})"
            ).add_to(m)

    st_folium(m, width=1300, height=450)
    
    st.markdown("---")
    
    # Station-wise Status Accordion Section
    st.markdown("### 🏢 Station-Wise Live Personnel Audit")
    
    for st_name in ["East PS", "West PS", "South PS", "TMCH PS"]:
        with st.expander(f"📌 {st_name} Attendance Breakdown"):
            st_cps = [cp for cp in CHECKPOINTS if cp["station"] == st_name]
            
            for cp in st_cps:
                st.markdown(f"#### Checkpoint #{cp['id']}: {cp['name']}")
                
                cp_roster = df_roster_today[df_roster_today["checkpoint_id"] == cp["id"]]
                
                if cp_roster.empty:
                    st.info("No officers assigned to this post today.")
                else:
                    table_rows = []
                    for _, off in cp_roster.iterrows():
                        off_name = off["officer_name"]
                        # Check checkin record
                        checkin_rec = df_checkins_today[
                            (df_checkins_today["checkpoint_id"] == cp["id"]) & 
                            (df_checkins_today["officer_name"] == off_name)
                        ] if not df_checkins_today.empty else pd.DataFrame()
                        
                        if not checkin_rec.empty:
                            rec = checkin_rec.iloc[0]
                            time_str = rec["timestamp"]
                            dist_str = f"{rec['distance_meters']:.1f} m"
                            st_tag = rec["status"]
                            photo_b64 = rec["photo_b64"]
                        else:
                            time_str = "Not Checked In"
                            dist_str = "-"
                            st_tag = "Pending"
                            photo_b64 = None
                            
                        table_rows.append({
                            "Rank": off["rank"],
                            "Officer Name": off_name,
                            "Contact Phone": off["phone"],
                            "Check-in Time": time_str,
                            "Distance Deviation": dist_str,
                            "Status": st_tag,
                            "Photo": photo_b64
                        })
                    
                    # Display Table & Photo Cards
                    cols = st.columns([1, 1.5, 1.2, 1.2, 1.2, 1.5])
                    cols[0].markdown("**Rank**")
                    cols[1].markdown("**Officer Name**")
                    cols[2].markdown("**Phone**")
                    cols[3].markdown("**Punch Time**")
                    cols[4].markdown("**Distance**")
                    cols[5].markdown("**Status Badge**")
                    
                    for row in table_rows:
                        c0, c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.2, 1.2, 1.2, 1.5])
                        c0.write(row["Rank"])
                        c1.write(row["Officer Name"])
                        c2.write(row["Contact Phone"])
                        c3.write(row["Check-in Time"])
                        c4.write(row["Distance Deviation"])
                        
                        if row["Status"] == "Verified Present":
                            c5.markdown('<span class="badge-present">Verified Present</span>', unsafe_allow_html=True)
                        elif row["Status"] == "Flagged Out-of-Bounds":
                            c5.markdown('<span class="badge-oob">Flagged Out-of-Bounds</span>', unsafe_allow_html=True)
                        else:
                            c5.markdown('<span class="badge-pending">Pending</span>', unsafe_allow_html=True)
                            
                        if row["Photo"]:
                            with st.popover(f"📷 View Selfie ({row['Officer Name']})"):
                                st.image(f"data:image/jpeg;base64,{row['Photo']}", caption=f"{row['Officer Name']} - {row['Status']}")

                st.markdown("<hr style='margin: 12px 0; border: none; border-top: 1px dashed #334155;'/>", unsafe_allow_html=True)

    st.markdown("---")
    
    # CSV Export Button
    st.markdown("### 📥 Export Official Duty Verification Report")
    
    if not df_roster_today.empty:
        # Merge roster & checkins for complete report
        report_data = []
        for _, r in df_roster_today.iterrows():
            cp_info = next(c for c in CHECKPOINTS if c["id"] == r["checkpoint_id"])
            checkin_rec = df_checkins_today[
                (df_checkins_today["checkpoint_id"] == r["checkpoint_id"]) &
                (df_checkins_today["officer_name"] == r["officer_name"])
            ] if not df_checkins_today.empty else pd.DataFrame()
            
            if not checkin_rec.empty:
                rec = checkin_rec.iloc[0]
                punch_time = rec["timestamp"]
                dist = rec["distance_meters"]
                lat = rec["latitude"]
                lon = rec["longitude"]
                status = rec["status"]
            else:
                punch_time = "N/A"
                dist = "N/A"
                lat = "N/A"
                lon = "N/A"
                status = "Not Checked In"
                
            report_data.append({
                "Duty Date": dash_date,
                "Station": r["station"],
                "Checkpoint ID": r["checkpoint_id"],
                "Checkpoint Name": cp_info["name"],
                "Officer Name": r["officer_name"],
                "Rank": r["rank"],
                "Phone": r["phone"],
                "Check-in Timestamp": punch_time,
                "Check-in Lat": lat,
                "Check-in Lon": lon,
                "Distance from Center (m)": dist,
                "Verification Status": status
            })
            
        report_df = pd.DataFrame(report_data)
        csv_bytes = report_df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Download Complete Duty Verification Report (CSV)",
            data=csv_bytes,
            file_name=f"Thanjavur_Checkpoint_Report_{dash_date}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.info("No roster data available for selected date to export.")
