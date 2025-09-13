import streamlit as st
import requests
import json
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
from auth import login_ui, logout_ui
from fpcalc import (
    calculate_ta, calculate_fp_coeff, calculate_hf, calculate_rmu,
    get_component_factors, get_sfrs_factors
)

st.set_page_config(page_title="Simple FpCalc", layout="centered", initial_sidebar_state="collapsed")

# Authentication
login_ui()
logout_ui()

# Load Data
def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

arch_components = load_json("data/arch.json")
sfrs_data = load_json("data/building.json")
period_data = load_json("data/period.json")

# Main Header
st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.markdown("# 📐 Simple FpCalc")
st.markdown("**Seismic Design Force (Fp) Calculator for Partition Walls**")
st.markdown("Based on **ASCE/SEI 7-22**, Chapter 13")
st.markdown('</div>', unsafe_allow_html=True)

# Toggle for showing detailed information
show_details = st.toggle("Show detailed information", value=False)

# Geocode address and fetch SDS functions
@st.cache_data(show_spinner=False)
def geocode(addr: str):
    if not addr:
        return None
    geolocator = Nominatim(user_agent="SimpleFpCalc")
    return geolocator.geocode(addr)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_sds_cached(lat, lon, risk_category, site_class="Default"):
    """Fetch SDS from USGS API with caching"""
    url = (
        f"https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
        f"?latitude={lat}&longitude={lon}"
        f"&riskCategory={risk_category}"
        f"&siteClass={site_class}&title=SimpleFpCalc"
    )
    r = requests.get(url)
    r.raise_for_status()
    return float(r.json()["response"]["data"]["sds"])

# Initialize session state for SDS caching
if 'sds_value' not in st.session_state:
    st.session_state.sds_value = None
if 'sds_location' not in st.session_state:
    st.session_state.sds_location = None
if 'sds_params' not in st.session_state:
    st.session_state.sds_params = None

# Building Address
default_address = "601 12th Street, Oakland 94607"
address = st.text_input(
    "Building address:",
    value=default_address,
    placeholder="e.g., 601 12th Street, Oakland 94607"
)

# Geocode address and auto-fetch SDS
location = geocode(address.strip())
if location:
    lat, lon = location.latitude, location.longitude
    
    # Create two columns for location info and map
    col_info, col_map = st.columns([1, 1.5])
    
    with col_info:
        st.info(f"🔍 **{location.address}**\n\nLatitude: {lat:.6f} \n\nLongitude: {lon:.6f}")
    
    with col_map:
        # Map display
        m = folium.Map(location=[lat, lon], zoom_start=16)
        tooltip = folium.Tooltip(f"<strong>Building Location</strong><br>"
                                 f"Lat: {lat:.6f}<br>Lon: {lon:.6f}", parse_html=True)
        folium.Marker([lat, lon], tooltip=tooltip, icon=folium.Icon(icon="building", prefix="fa")).add_to(m)
        st_folium(m, width=400, height=220)
    
else:
    if address:
        st.warning("⚠️ Unable to geocode that address. Please try refining it.")
    lat, lon = None, None

# Building Occupancy
occupancy = st.selectbox(
    "Building occupancy:",
    ["Office", "Hospital"],
    index=1
)

# Risk Category and Importance Factor
if "Office" in occupancy:
    risk_category = "II"
    Ie = 1.0
    Ip = 1.0
    if show_details:
        st.caption("Risk Category: **II** | Importance factor: Ie = **1.0**, Ip = **1.0**")
else:  # Hospital
    risk_category = "IV"
    Ie = 1.5
    Ip = 1.5
    if show_details:
        st.caption("Risk Category: **IV** | Importance factor: Ie = **1.5**, Ip = **1.5**")

# Auto-fetch SDS when address and occupancy are available
SDS = None
if lat is not None and lon is not None:
    # Check if we have cached SDS for current parameters
    current_params = (lat, lon, risk_category, "Default")
    has_cached_sds = (st.session_state.sds_value is not None and 
                     st.session_state.sds_params == current_params)
    
    if has_cached_sds:
        SDS = st.session_state.sds_value
    else:
        try:
            SDS = fetch_sds_cached(lat, lon, risk_category, "Default")
            st.session_state.sds_value = SDS
            st.session_state.sds_location = f"{lat:.6f}, {lon:.6f}"
            st.session_state.sds_params = current_params
            if show_details:
                st.caption(f"SDS = **{SDS:.3f} g**")
        except Exception as e:
            st.error(f"⚠️ Error fetching SDS: {e}")

if SDS is None:
    st.warning("⚠️ Enter a valid address to fetch SDS")

# Building Type
building_type = st.selectbox(
    "Building material:",
    ["Steel", "Concrete", "Masonry", "Wood", "Other/Unknown"],
    index=4
)

# Map building type to SFRS
sfrs_mapping = {
    "Steel": "B3. Building frame system: Steel ordinary concentrically braced frames",
    "Concrete": "A3. Bearing wall system: Ordinary reinforced concrete shear walls", 
    "Masonry": "A10. Bearing wall system: Ordinary reinforced masonry shear walls",
    "Wood": "A16. Bearing wall system: Light-frame (wood) walls sheathed with wood structural panels rated for shear resistance",
    "Other/Unknown": None
}

selected_sfrs = sfrs_mapping[building_type]
if selected_sfrs:
    R, Omega_0 = get_sfrs_factors(sfrs_data, selected_sfrs)
    if show_details:
        st.caption(f"SFRS: **{selected_sfrs}** | R = **{R}**, Ω₀ = **{Omega_0}**")
else:
    R, Omega_0 = 0., 0.
    if show_details:
        st.caption("Using default values: Rμ = **1.3**")

# Number of floors
num_floors = st.number_input(
    "Total number of floors:",
    min_value=1,
    max_value=100,
    value=5,
)

# Calculate building height
if "Office" in occupancy:
    floor_height = 12  # feet
else:  # Hospital
    floor_height = 16  # feet

h = num_floors * floor_height
if show_details:
    st.caption(f"Building height (h): **{h} ft** ({num_floors} floors × {floor_height} ft/floor)")

# Highest floor for partition installation
highest_floor = st.number_input(
    "Highest floor of partition installation:",
    min_value=1,
    max_value=num_floors,
    value=num_floors
)

# Calculate z (attachment height)
z = highest_floor * floor_height
if show_details:
    st.caption(f"Attachment height (z): **{z} ft** (installation floor)")

# Partition wall height
partition_height = st.selectbox(
    "Partition wall height:",
    ["Less than or equal to 9 feet", "Greater than 9 feet"],
    index=1
)

# Map to component type
if "Less than or equal to 9 feet" in partition_height:
    component_name = "1a. Interior nonstructural walls and partitions: Light frame <= 9 ft in height"
else:
    component_name = "1b. Interior nonstructural walls and partitions: Light frame > 9 ft in height"

if show_details:
    st.caption(f"Component: **{component_name}**")

# Results Section
if SDS is not None:
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("#### ✅ Results")
    
    # Get component factors
    location_type = "Supported Above Grade" if z > 0 else "Supported At or Below Grade"
    CAR, Rpo = get_component_factors(arch_components, component_name, location_type)
    
    # Calculate approximate period (Ta)
    structure_type = "All other structural systems"
    
    Ta, Ct, x = calculate_ta(period_data, structure_type, h)
    
    # Calculate other parameters
    Hf, a1, a2 = calculate_hf(z, h, Ta)
    Rmu = calculate_rmu(R, Ie, Omega_0)
    
    # Calculate Fp coefficient
    Wp = 1.0  # Use 1.0 for coefficient calculation
    Fp_coeff, Fp_calc_coeff, Fp_min_coeff, Fp_max_coeff = calculate_fp_coeff(SDS, Ip, Wp, Hf, Rmu, CAR, Rpo)
    
    # Display results
    st.markdown(f"##### **Fp Coefficient = {Fp_coeff:.3f}**")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
else:
    st.warning("⚠️ Please provide a valid building address and fetch SDS to see results.")

st.caption("Simple FpCalc | ASCE/SEI 7-22 Chapter 13 © Degenkolb Engineers")
