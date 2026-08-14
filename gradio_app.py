# Author & Original Creator: Antti Kiviniemi
#
# License: 
#   MIT (c) 2025 South-Eastern Finland University of Applied Sciences (Xamk)
#   MIT (c) 2026 Antti Kiviniemi 
#   (see LICENSE for details)
#
# Description: Creates a Gradio web application that fetches and displays both actualized and 
#              predicted precipitation data from the Finnish Meteorological Institute (FMI)

import gradio as gr # Gradio is used to create a simple web interface
from datetime import datetime, timedelta # For handling date and time
import pytz # For timezone conversion

import base64
import os


def format_precip(value):
    """
    Round a float to one decimal place and always show one digit after the decimal point.
    Example: 1.299999999998 → 1.3, 1.0 → 1.0, 0.0 → 0.0
    """
    return f"{round(value, 1):.1f}"

# Function to convert UTC time string to Helsinki local time
def convert_to_helsinki_hour(utc_time_str, round_up=True):
    try:
        # Parse the UTC time string into a datetime object
        utc_time = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")

         # Localize the datetime object to UTC
        utc_time = pytz.utc.localize(utc_time)

        # Convert the time to Helsinki timezone
        helsinki_time = utc_time.astimezone(pytz.timezone("Europe/Helsinki"))

        # Round up to next full hour if not already on the hour
        # This makes the hour of the data to mora accurately represent the data we have received from API-calls
        if round_up and (helsinki_time.minute > 0 or helsinki_time.second > 0):
            helsinki_time += timedelta(hours=1)
        
        # This continues the previous, earlier changed the hour, here we fix the minutes, seconds, etc.
        helsinki_time = helsinki_time.replace(minute=0, second=0, microsecond=0)

        # Return the formatted datetime object
        return helsinki_time
    except Exception:
        return utc_time_str

# Import functions and constants from other modules
from MVP_toteuma import fetch_precipitation_for_station, STATIONS
from MVP_ennuste import fetch_fmi_precipitation_predictions

# Function to fetch both actual and predicted weather data
def fetch_weather_data():
    structured_data = []

    # Loop through each station defined in the .env file
    for station_id, station_name in STATIONS.items():
        # Try to fetch actualized precipitation data
        result = fetch_precipitation_for_station(station_id, station_name)

        # If the station returns valid data, include it
        if result:
            structured_data.append({"type": "actual", **result})
        else:
            # If the station is inactive or fails, skip it and log the issue
            print(f"Skipping station {station_name} due to missing or invalid data.")

    # Fetch predicted precipitation data for Mikkeli
    prediction = fetch_fmi_precipitation_predictions()
    if prediction:
        structured_data.append({"type": "prediction", **prediction})

    return structured_data


# Function to format the fetched data into readable text
def format_output(data):
    output_lines = []

    # Loop through each data entry
    for entry in data:

        # Data relating to actualized precipitation numbers
        if entry["type"] == "actual":
            # Get raw timestamps from the data
            time1_raw = entry.get("time1")
            time2_raw = entry.get("time2")

            # Check if both timestamps exist
            if time1_raw and time2_raw:
                # Convert to Helsinki time and adjust time1 to reflect actual observation window
                time1_dt = convert_to_helsinki_hour(time1_raw, round_up=True)
                time2_dt = convert_to_helsinki_hour(time2_raw, round_up=True)

                # If conversion succeeded, format and display the time range
                if time1_dt and time2_dt:

                    # actualized data is for the previous hour
                    # e.g. 12:00 means 11:00 to 12:00
                    time1_dt -= timedelta(hours=1) 

                    output_lines.append(
                        f"[Actual] {entry['station_name']}: Total = {format_precip(entry['raincombined'])} mm "
                        f"({entry['warninglevel']}), Time Range: {time1_dt.strftime('%Y-%m-%d %H:%M')} to {time2_dt.strftime('%Y-%m-%d %H:%M')}"
                    )
                    continue # skip fallback

            # Fallback if timestamps are missing or conversion failed
            output_lines.append(
                f"[Actual] {entry['station_name']}: Total = {format_precip(entry['raincombined'])} mm "
                f"({entry['warninglevel']}), Time Range: {time1_raw or 'N/A'} to {time2_raw or 'N/A'}"
            )

        # Data relating to predicted precipitation numbers
        elif entry["type"] == "prediction":

            # Formatting the times
            # Note: if time relating to predicted values says 15:00, it refers to predicted values between 15:00 to 16:00.
            start_hour = convert_to_helsinki_hour(entry['total_precipitation_time_range']['start']).strftime('%Y-%m-%d %H:00')
            end_hour = convert_to_helsinki_hour(entry['total_precipitation_time_range']['end']).strftime('%Y-%m-%d %H:00')
            end_hour_dt = datetime.strptime(end_hour, "%Y-%m-%d %H:00")
            next_hour = end_hour_dt + timedelta(hours=1)
            # Removes the seconds from the time, afterwards it shows only hours and minutes, e.g. 15:00
            next_hour_str = next_hour.strftime("%H:00")

            # Format prediction data with city name, peak and total precipitation, warnings, and time range
            output_lines.append(
                f"[Prediction] {entry['city_name']}: Total = {entry['total_precipitation']} mm "
                f"({entry['total_precipitation_warning']}), Time Range: {start_hour} to {next_hour_str} "
               #f"(where {end_hour} means {end_hour}–{next_hour_str})"
            )

    return "\n".join(output_lines)


# Create the Gradio interface
iface = gr.Interface(
    fn=lambda: format_output(fetch_weather_data()),  # Function to run when "Generate" is clicked
    inputs=[],  # No input fields needed
    outputs=gr.Textbox(lines=8),  # Output is plain text.
    title="Weather Data Fetcher",  # Title of the App
    description=(
        "<p>Click the <strong>Generate</strong> button to retrieve the latest real-time and predicted precipitation data.</p>"
        "<div style='font-size: 0.9em; color: #666;'>"
        "This application uses Helsinki time, and the times are automatically adjusted for daylight saving time."
        "</div>"
        "<div style='font-size: 0.9em; color: #666;'>"
        "The weather data is provided by the "
        "<a href='https://en.ilmatieteenlaitos.fi/open-data' target='_blank'>Finnish Meteorological Institute (FMI)</a>, "
        "licensed under <a href='https://creativecommons.org/licenses/by/4.0/' target='_blank'>CC BY 4.0</a>."
       "</div>"
    ),

    flagging_mode="never" # Disable Gradio's default flagging feature
)

# Launch the Gradio App
if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
