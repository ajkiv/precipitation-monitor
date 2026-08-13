# Author & Original Creator: Antti Kiviniemi
#
# License: 
#   MIT (c) 2025 South-Eastern Finland University of Applied Sciences (Xamk)
#   MIT (c) 2026 Antti Kiviniemi 
#   (see LICENSE for details)
#
# Description: Fetches Finnish Meteorological Institute (FMI) Precipitation Predictions for Mikkeli, Finland. 

import datetime as dt # For working with dates and times
from fmiopendata.wfs import download_stored_query # FMI Open data API client
import os # For accessing environmental variables from .env 
import traceback # For printing detailed error traces
from dotenv import load_dotenv # To Load environment variables from .env file

# Load environment variables
load_dotenv()

# Get bounding box for Mikkeli
FMI_BBOX = os.getenv("FMI_BBOX")

# Load how many hours of predictions we want to fetch
RAW_PREDICTION_HOURS = int(os.getenv("PREDICTION_HOURS"))

# Adjust prediction hours to get the actual hours requested by the variable.
# e.g. If you want 6 hours of predictions, you need to adjust the value to be 5.
ADJUSTED_PREDICTION_HOURS = (RAW_PREDICTION_HOURS - 1)

# Load threshold values for warnings
THRESHOLDS = {
    "total": {
        "mild": float(os.getenv("THRESHOLD_MILD_TOTAL")),
        "moderate": float(os.getenv("THRESHOLD_MODERATE_TOTAL")),
        "severe": float(os.getenv("THRESHOLD_SEVERE_TOTAL"))
    }
}

# Function to classify precipitation value into warning levels
def classify_precipitation(value):
    thresholds = THRESHOLDS["total"]
    if value >= thresholds["severe"]:
        return "Severe Warning"
    elif value >= thresholds["moderate"]:
        return "Moderate Warning"
    elif value >= thresholds["mild"]:
        return "Mild Warning"
    else:
        return "No Warning"

# Main function to fetch forecasted precipitation data from FMI
def fetch_fmi_precipitation_predictions():
    try:

        # We subtract one hour to get the current hours predictions. 
        # Example 1: If we make an API-request with 15:05, it only gives predictions starting from 16:00 onwards.
        # Example 2: If we make an API-request with 14:55, it gives predictions starting from 15:00 onwards.
        now = dt.datetime.utcnow() - dt.timedelta(hours=1)

        # Define start and end time for forecast query (currently next 6 hours)
        start_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = (now + dt.timedelta(hours=ADJUSTED_PREDICTION_HOURS)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # Query FMI for grid-based surface forecast data
        model_data = download_stored_query(
            "fmi::forecast::harmonie::surface::grid",
            args=[
                f"starttime={start_time}",
                f"endtime={end_time}",
                f"bbox={FMI_BBOX}"
            ]
        )

        # Get the latest model run (most recent forecast)
        latest_run = max(model_data.data.keys())
        data = model_data.data[latest_run]

        # Parse the data to clean up memory
        data.parse(delete=True)

        # Extract valid forecast times
        valid_times = sorted(data.data.keys())
        last_precip = 0.0

        # Dead code - variable end_time is used instead.
        last_time = None

        # Loop through forecast times in order
        # Note: Code has been changed from original.
        #       Current form of the code just gets the last item from the data
        #       Kept looking like original, in case we want to revert back and add features.
        for t in valid_times[-ADJUSTED_PREDICTION_HOURS:]:
            for level in data.data[t]:
                datasets = data.data[t][level]

                # Loop through dataset names to find precipitation data
                # In current implementation, we are interested in only the total precipitation amount.
                # The total precipitation amount can be found from the last hour in the forecast data.
                # NOTE: 
                # The structure of the data is unintuitive. E.g. if hour 1 shows 0.1 mm and hour 2 shows 0.1 mm,
                # then it means that on hour 1 it rained 0.1 mm, but on hour 2 it didn't rain, and the total is still 0.1 mm.
                # The value on the hour shows the "total rain so far", not "rain during the lats hour". 
                # If on hour 3 it shows 0.3 mm, and on hour 2 it shows 0.1 mm, it means that on hour 3 it predicts 0.2 mm of rain.
                # As a general comment, ALL the data relating to the precipitation amounts is quite unintuitive, and double checking is recommended.
                for dset in datasets:
                    if "prec" in dset.lower():
                        values = datasets[dset]["data"]
                        flat = [v for row in values for v in row]

                        # Calculate average precipitation for the grid
                        # Note: Grid consists of many values, we take the average of these values.
                        avg_prec = round(sum(flat) / len(flat), 1) if flat else 0.0
                        last_precip = avg_prec

                        # Dead code - variable end_time is used instead.
                        last_time = t.strftime('%Y-%m-%dT%H:%M:%SZ')
                        break
                else:
                    continue
                break

        # Creates the warning: did the precipitation value exceed a threshold value
        warning = classify_precipitation(last_precip)

        # Return the values we have found, which are then used in the frontend
        return {
            "city_name": "Mikkeli", # Currently we are only doing precipitation predictions for Mikkeli
            "total_precipitation": last_precip,
            "total_precipitation_warning": warning,
            "total_precipitation_time_range": {
                "start": start_time,
                "end": end_time
            }
        }

    except Exception as e:
        # Print error message and traceback for debugging
        print(f"Failed to fetch or process FMI data: {e}")

        traceback.print_exc()
        return None
