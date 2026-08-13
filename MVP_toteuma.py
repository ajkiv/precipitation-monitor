# Author & Original Creator: Antti Kiviniemi
#
# License: 
#   MIT (c) 2025 South-Eastern Finland University of Applied Sciences (Xamk)
#   MIT (c) 2026 Antti Kiviniemi 
#   (see LICENSE for details)
#
# Description: Fetches Finnish Meteorological Institute (FMI) actualized precipitation data for several
#              weather stations in Finland. The stations are defined in the .env file as a JSON object.

import requests # For making HTTP requests to FMI API
from xml.etree import ElementTree as ET # For parsing XML responses
from datetime import datetime, timedelta # For handling time ranges
import traceback # For printing detailed error messages
import os # For accessing environment variables
import json # For parsing station data from JSON
from dotenv import load_dotenv # To load environment variables from .env file

# Load environment variables from .env file
load_dotenv()

# Read configuration values from environment
FMI_BASE_URL = os.getenv("FMI_BASE_URL") # Base URL for FMI API
DEBUG_MODE = os.getenv("DEBUG_MODE") == "True" # Enable debug logging if set to true in .env.
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS")) # How many hours back to fetch data
STATIONS = json.loads(os.getenv("STATIONS_JSON")) # Dictionary of station IDs and names

# Thresholds for warning levels based on total precipitation
THRESHOLDS = {
    "mild": float(os.getenv("THRESHOLD_MILD_TOTAL")),
    "moderate": float(os.getenv("THRESHOLD_MODERATE_TOTAL")),
    "severe": float(os.getenv("THRESHOLD_SEVERE_TOTAL")),
}

# Function to fetch actual precipitation for a specific station
def classify_precipitation(total):
    if total >= THRESHOLDS["severe"]:
        return "Severe Warning"
    elif total >= THRESHOLDS["moderate"]:
        return "Moderate Warning"
    elif total >= THRESHOLDS["mild"]:
        return "Mild Warning"
    else:
        return "No Warning"

# Function to fetch actual precipitation data for a specific station
def fetch_precipitation_for_station(station_id, station_name):
    # Define time range for the query: from LOOKBACK_HOURS ago to now
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=LOOKBACK_HOURS)
    
    # Format times as ISO 8601 strings
    start_str = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Define query parameters for FMI API
    params = {
        "request": "GetFeature",
        "storedquery_id": "fmi::observations::weather::timevaluepair",
        "fmisid": station_id,
        "parameters": "precipitation1h",
        "starttime": start_str,
        "endtime": end_str
    }

    try:
        # Make the API request
        response = requests.get(FMI_BASE_URL, params=params)

        # Parse the XML response
        root = ET.fromstring(response.content)
        ns = {'wml2': 'http://www.opengis.net/waterml/2.0'} # XML namespace for WaterML

        time_rain_pairs = [] # List to store (time, value) pairs

        # Extract precipitation values from XML
        for point in root.findall('.//wml2:point', ns):
            time_str = point.find('.//wml2:time', ns).text
            value_str = point.find('.//wml2:value', ns).text
            try:
                val = float(value_str) # Convert value to float
                time_rain_pairs.append((time_str, val)) # Store time and value
            except ValueError:
                continue # Skip invalid values

        # Extract up to two most recent precipitation values
        # If you want more than two values, this part needs to be revised
        if len(time_rain_pairs) >= 2:
            time1, rain1 = time_rain_pairs[0]
            time2, rain2 = time_rain_pairs[1]
        elif len(time_rain_pairs) == 1:
            time1, rain1 = time_rain_pairs[0]
            time2, rain2 = None, 0.0
        else:
            time1, rain1, time2, rain2 = None, 0.0, None, 0.0

        # Combine the two values
        raincombined = rain1 + rain2

        # Classify the combined precipitation into a warning level
        warninglevel = classify_precipitation(raincombined)

        # Return the structured result
        return {
            "station_name": station_name,
            "time1": time1,
            "rain1": rain1,
            "time2": time2,
            "rain2": rain2,
            "raincombined": raincombined,
            "warninglevel": warninglevel
        }

    except Exception as e:
        # Print error message and traceback if something goes wrong
        print(f"Error fetching or processing data for {station_name}: {e}")
        
        traceback.print_exc()
        return None # Return None on failure
