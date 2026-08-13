# Precipitation Monitoring App

## Overview
This project provides a **Gradio-based web application** for monitoring precipitation in South Savo, Finland. It combines:
- **Actual precipitation data** from Finnish Meteorological Institute (FMI) observation stations.
- **Predicted precipitation data** from FMI’s Harmonie surface forecast model.

The app displays both real-time and forecasted precipitation values, along with warning levels based on configurable thresholds.

---

## Features
- Fetches **actual precipitation** for multiple stations defined in `.env`.
- Fetches **forecast precipitation** for a bounding box (currently Mikkeli city center).
- Classifies precipitation into **warning levels** (Mild, Moderate, Severe).
- Displays results in a **simple Gradio interface**.
- Times are converted to **Helsinki local time**.

---

## Project Structure
```
.
├── gradio_app.py        # Main Gradio app (entry point)
├── MVP_ennuste.py       # Fetches precipitation predictions from FMI
├── MVP_toteuma.py       # Fetches actual precipitation data from FMI stations
├── logos.png            # Logo displayed in the Gradio UI
├── .env                 # Environment variables (API URL, thresholds, stations)
├── README.md            # Project documentation
├── LICENSE.txt          # License information (MIT)
```

---

## Environment Variables
Your `.env` file should look like this:
```
FMI_BASE_URL=https://opendata.fmi.fi/wfs
DEBUG_MODE=False

LOOKBACK_HOURS=2
PREDICTION_HOURS=12

THRESHOLD_MILD_TOTAL=30.0
THRESHOLD_MODERATE_TOTAL=35.0
THRESHOLD_SEVERE_TOTAL=40.0

THRESHOLD_MILD_PEAK=25.0
THRESHOLD_MODERATE_PEAK=30.0
THRESHOLD_SEVERE_PEAK=35.0

FMI_BBOX=27.2575,61.6775,27.28,61.7

STATIONS_JSON={"150168": "Puumala", "101398": "Mikkeli lentoasema", "101196": "Heinola Asemantaus", "101219": "Kouvola Utti Lentoportintie", "101237": "Lappeenranta lentoasema", "101421": "Varkaus Kosulanniemi", "101367": "Joutsa Savenaho"}
```

---

## Installation
1. Clone the repository:
```bash
git clone <repo-url>
cd <repo-folder>
```
2. Install dependencies:
```bash
python -m pip install -r requirements.txt
```
Required packages:
- gradio
- requests
- python-dotenv
- fmiopendata
- pytz
- eccodes

---

## Usage
Run the Gradio app:
```bash
python gradio_app.py
```
This will start a local server and open the app in your browser.

---

## How It Works
- **MVP_toteuma.py**:
  - Fetches actual precipitation for each station in `STATIONS_JSON`.
  - Uses FMI’s `observations::weather::timevaluepair` query.
  - Combines last two hourly values and classifies warning level.

- **MVP_ennuste.py**:
  - Fetches forecast precipitation for the next `PREDICTION_HOURS`.
  - Uses FMI’s `forecast::harmonie::surface::grid` query.
  - Calculates average precipitation over the grid and classifies warning level.

- **gradio_app.py**:
  - Calls both modules.
  - Formats output with Helsinki time.
  - Displays results in a Gradio interface with project logos and credits.

---

## Example Output
```
[Actual] Puumala: Total = 0.0 mm (No Warning), Time Range: 2026-08-13 09:00 to 2026-08-13 11:00
[Actual] Mikkeli lentoasema: Total = 2.0 mm (No Warning), Time Range: N/A to N/A
[Actual] Heinola Asemantaus: Total = 0.0 mm (No Warning), Time Range: 2026-08-13 09:00 to 2026-08-13 11:00
[Actual] Kouvola Utti Lentoportintie: Total = 0.0 mm (No Warning), Time Range: N/A to N/A
[Actual] Lappeenranta lentoasema: Total = 0.0 mm (No Warning), Time Range: 2026-08-13 09:00 to 2026-08-13 11:00
[Actual] Varkaus Kosulanniemi: Total = 0.0 mm (No Warning), Time Range: 2026-08-13 09:00 to 2026-08-13 11:00
[Actual] Joutsa Savenaho: Total = 0.0 mm (No Warning), Time Range: 2026-08-13 09:00 to 2026-08-13 11:00
[Prediction] Mikkeli: Total = 4.5 mm (No Warning), Time Range: 2026-08-13 11:00 to 23:00 
```

---

## Authors and acknowledgment
Application developed by **Antti Kiviniemi** as part of the **DAME project** 
(South Savo Data Economy Accelerator – Shared Data as a Joint Success Factor), 
South-Eastern Finland University of Applied Sciences, Digital Information 
Management Research Centre Digitalia, in partnership with 
- City of Mikkeli
- MikseiMikkeli Oy
- Mipro Oy
- Rambøll Group A/S
- Mikkeli Water Company

The DAME-project is co‑funded by the European Union. The funding has been granted by the Centre for Economic Development, Transport and the Environment for South Savo from the European Regional Development Fund.

Data provided by https://en.ilmatieteenlaitos.fi/open-data, licensed under https://creativecommons.org/licenses/by/4.0/.

---

## Contributors

- **Antti Kiviniemi** — Author & Original Creator (all code in this repository)

---

## License

MIT License Copyright (c) 2025 South-Eastern Finland University of Applied Sciences (Xamk)

MIT License Copyright (c) 2026 Antti Kiviniemi

See [LICENSE](./LICENSE) for full details.
