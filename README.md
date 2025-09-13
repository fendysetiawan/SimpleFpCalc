# Simple FpCalc - Seismic Design Force Calculator

A simplified version of the FpCalc application for calculating seismic design forces (Fp) for partition walls according to ASCE/SEI 7-22, Chapter 13.

## Features

- **Simplified Input**: Only requires essential building parameters
- **Automatic SDS Fetching**: Automatically retrieves seismic design parameters from USGS API
- **Interactive Map**: Shows building location with geocoding
- **Real-time Calculations**: Updates Fp coefficient as inputs change

## Required Inputs

1. **Building Address**: Enter the building address (automatically geocoded)
2. **Building Occupancy**: 
   - Office (Risk Category II)
   - Hospital (Risk Category IV)
3. **Building Type**:
   - Steel (B3 Ordinary Concentric Braced Frame)
   - Concrete (A3 Bearing wall, ordinary reinforced concrete shear wall)
   - Masonry (A10 Bearing wall, ordinary reinforced masonry shear wall)
   - Wood (A16 Light-framed wood walls w/ wood structural panels)
   - Other/Unknown (uses R_mu = 1.3)
4. **Number of Floors**: Building height calculated automatically (12 ft/floor for office, 16 ft/floor for hospital)
5. **Partition Installation Floor**: Highest floor where partition is installed
6. **Partition Wall Height**:
   - Less than or equal to 9 feet (architectural 1a)
   - Greater than 9 feet (architectural 1b)

## How to Use

1. **Enter Building Address**: Type the building address
2. **Select Occupancy**: Choose Office or Hospital
3. **SDS Auto-Fetch**: SDS is automatically fetched from USGS API when address and occupancy are provided
4. **Configure Building**: Select building type and number of floors
5. **Set Partition Details**: Choose installation floor and wall height
6. **View Results**: Fp coefficient is calculated and displayed

## Output

The app provides:
- **Fp Coefficient**: The main result for seismic design force calculation

## Technical Details

- Uses ASCE/SEI 7-22, Chapter 13 equations
- Automatically calculates building height based on occupancy type
- Fetches SDS from USGS Design Maps API
- Uses default site class for all calculations
- Caches SDS values for performance

## Running the App

```bash
streamlit run app.py
```

## Dependencies

- streamlit
- requests
- geopy
- streamlit-folium
- folium

All dependencies are listed in `requirements.txt`.
