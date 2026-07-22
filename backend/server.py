from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import random
from datetime import datetime, timedelta
import time
import json
import xarray as xr
import math
from collections import Counter
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import os
import copernicusmarine
import math

app = FastAPI()

# ==========================
# 🔹 CORS
# ==========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================
# 🔹 HISTORY STORAGE
# ==========================
history_data = {
    "temperature": [],
    "salinity": [],
    "oxygen": [],
    "timestamps": []
}

# ==========================
# 🔹 LOCATIONS
# ==========================
locations = {
    "mumbai": {
        "name": "Mumbai Port",
        "lat": 18.9438,
        "lon": 72.8360
    },

    "goa": {
        "name": "Mormugao Port",
        "lat": 15.4121,
        "lon": 73.7997
    },

    "kochi": {
        "name": "Kochi Port",
        "lat": 9.9658,
        "lon": 76.2694
    },

    "chennai": {
        "name": "Chennai Port",
        "lat": 13.0844,
        "lon": 80.2929
    },

    "vizag": {
        "name": "Visakhapatnam Port",
        "lat": 17.6868,
        "lon": 83.2185
    },

    "kolkata": {
        "name": "Kolkata Port",
        "lat": 22.56,
        "lon": 88.36
    },

    "portblair": {
        "name": "Port Blair Port",
        "lat": 11.67,
        "lon": 92.75
    }
}
# ==========================
# 🔹 COPERNICUS SEA LEVEL
# ==========================
# def get_copernicus_sea_level():

#     try:

#         if ds is None:
#             return 0

#         sea_level = float(
#             ds["zos"]
#             .isel(time=-1)
#             .mean(skipna=True)
#             .values
#         )

#         if math.isnan(sea_level):
#             return 0

#         return round(sea_level, 2)

#     except Exception as e:

#         print("Sea Level Error:", e)

#         return 0


_sea_level_cache = {}

def get_copernicus_sea_level(lat, lon):
    lat = round(lat, 2)
    lon = round(lon, 2)

    cache_key = f"{lat},{lon}"
    now = time.time()

    # Return cached value if it's still fresh
    if cache_key in _sea_level_cache:
        cached_value, cached_time = _sea_level_cache[cache_key]
        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    try:
        date = "2026-07-14"

        sealevel_ds = copernicusmarine.open_dataset(
            dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
            minimum_longitude=lon - 0.1,
            maximum_longitude=lon + 0.1,
            minimum_latitude=lat - 0.1,
            maximum_latitude=lat + 0.1,
            start_datetime=date,
            end_datetime=date,
            variables=["zos"]
        )

        sea_level = sealevel_ds["zos"].sel(latitude=lat, longitude=lon, method="nearest")

        value = float(sea_level.values[0])

        print("Raw sea level value:", value)

        if math.isnan(value):
            value = 0.0

        value = round(value, 2)
        print("after fetched sea level value:", value)

        # Save to cache
        _sea_level_cache[cache_key] = (value, now)

        return value

    except Exception as e:
        print("Sea Level Error:", e)
        if cache_key in _sea_level_cache:
            return _sea_level_cache[cache_key][0]
        return 0.0

# ==========================
# 🔹 COPERNICUS SALINITY
# ==========================
# def get_copernicus_salinity():

#     try:

#         if ds is None:
#             return 35.0

#         salinity = float(
#             ds["sob"]
#             .isel(time=-1)
#             .mean(skipna=True)
#             .values
#         )

#         if math.isnan(salinity):
#             return 35.0

#         return round(salinity, 2)

#     except Exception as e:

#         print("Salinity Error:", e)

#         return 35.0

LOCATIONS = {
    "Mumbai": {"lat": 19.07, "lon": 72.87},
    "Goa": {"lat": 15.45, "lon": 73.80},
}

# Simple in-memory cache: {location_key: (value, timestamp)}
_salinity_cache = {}
CACHE_DURATION_SECONDS = 3600  # refetch at most once per hour

def get_copernicus_salinity(lat, lon):
    lat = round(lat, 2)
    lon = round(lon, 2)
    
    



    cache_key = f"{lat},{lon}"
    now = time.time()
    
    # Return cached value if it's still fresh
    if cache_key in _salinity_cache:
        cached_value, cached_time = _salinity_cache[cache_key]
        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    try:
        # date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        date = "2026-07-14"

        salinity_ds = copernicusmarine.open_dataset(
            dataset_id="cmems_mod_glo_phy-so_anfc_0.083deg_P1D-m",
            minimum_longitude=lon - 0.1,
            maximum_longitude=lon + 0.1,
            minimum_latitude=lat - 0.1,
            maximum_latitude=lat + 0.1,
            start_datetime=date,
            end_datetime=date,
            variables=["so"]
        )


        salinity = salinity_ds["so"].sel(latitude=lat, longitude=lon, method="nearest")
        salinity_surface = salinity.isel(depth=0) if "depth" in salinity.dims else salinity

        value = float(salinity_surface.values[0])

        print("Rawbefore value:", value)
        print("Type:", type(value))
        print("isNaN:", math.isnan(value))

        if math.isnan(value):
            value = 34.0

        value = round(value, 2)
        print("after fetched salinity value:", value)
        
        

        # Save to cache
        _salinity_cache[cache_key] = (value, now)

        return value

    except Exception as e:
        print("Salinity Error:", e)
        # If we have ANY old cached value, better to serve that than a hardcoded guess
        if cache_key in _salinity_cache:
            return _salinity_cache[cache_key][0]
        return 35.0
    

    
# ==========================
# 🔹 OPEN METEO REAL DATA
# ==========================
# ==========================
# 🔹 CACHE FOR LAST REAL DATA
# ==========================
last_sea_data = {
    "temperature": 28.0,
    "wave_height": 1.0,
    "wind_speed": 10.0
}

# ==========================
# 🔹 OPEN METEO REAL DATA
# ==========================
def get_sea_data(lat, lon):

    global last_sea_data

    try:

        url = (
            f"https://api.open-meteo.com/v1/marine?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=sea_surface_temperature,wave_height,wind_speed"
        )

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code == 200:

            print("✅ OpenMeteo Success")

            data = response.json()

            sea_data = {

                "temperature":
                    round(
                        float(
                            data["hourly"][
                                "sea_surface_temperature"
                            ][-1]
                        ),
                        2
                    ),

                "wave_height":
                    round(
                        float(
                            data["hourly"][
                                "wave_height"
                            ][-1]
                        ),
                        2
                    ),

                "wind_speed":
                    round(
                        float(
                            data["hourly"][
                                "wind_speed"
                            ][-1]
                        ),
                        2
                    )
            }

            # Save latest real value
            last_sea_data = sea_data

            return sea_data

        else:

            print(
                "❌ OpenMeteo Failed:",
                response.status_code
            )

    except Exception as e:

        print(
            "❌ OpenMeteo Error:",
            e
        )

    # ==========================
    # 🔹 FALLBACK TO LAST REAL DATA
    # ==========================
    print(
        "⚠️ Using Cached Sea Data"
    )

    return last_sea_data


# ==========================
# 🔹 REAL DISSOLVED OXYGEN
# ==========================
# def get_real_oxygen(lat, lon):

#     try:

#         url = (
#             "https://coastwatch.pfeg.noaa.gov/erddap/griddap/"
#             "erdMH1chla8day.csv?"
#             "time,latitude,longitude"
#         )

#         # Placeholder until specific oxygen endpoint chosen

#         return 5.8

#     except Exception as e:

#         print("NOAA Oxygen Error:", e)

#         return 5.5


def get_real_oxygen(temperature, salinity):
    
    base_oxygen = 6.5  #baseline

    temp_effect = (temperature - 27) * 0.15
    salinity_effect = (salinity - 33) * 0.05

    oxygen = base_oxygen - temp_effect - salinity_effect

    return round(max(oxygen, 3.0), 2)  #floorto3 this is to avoid neg value okay?


# ==========================
# 🔹 RISK CALCULATION
# ==========================
def calculate_risk(temp, oxygen):

    score = 0

    if temp > 30:
        score += 40

    elif temp > 28:
        score += 20

    if oxygen < 4.5:
        score += 40

    elif oxygen < 5:
        score += 20

    score += random.randint(0, 10)

    return min(score, 100)
# ==========================
# 🔹 OPEN METEO REAL DATA
# ==========================
def get_sea_data(lat, lon):

    try:

        url = (
            f"https://api.open-meteo.com/v1/marine?"
            f"latitude={lat}&longitude={lon}"
            f"&hourly=sea_surface_temperature,wave_height,wind_speed"
        )

        response = requests.get(url, timeout=5)

        if response.status_code == 200:

            data = response.json()

            return {
                "temperature":
                    data["hourly"]["sea_surface_temperature"][-1],

                "wave_height":
                    data["hourly"]["wave_height"][-1],

                "wind_speed":
                    data["hourly"]["wind_speed"][-1]
            }

    except Exception as e:

        print("OpenMeteo Error:", e)

    return {
        "temperature": round(random.uniform(27, 30), 2),
        "wave_height": round(random.uniform(0.5, 2.5), 2),
        "wind_speed": round(random.uniform(5, 20), 2)
    }

# ==========================
# 🔹 RISK CALCULATION
# ==========================
def calculate_risk(temp, oxygen):

    score = 0

    if temp > 30:
        score += 40

    elif temp > 28:
        score += 20

    if oxygen < 4.5:
        score += 40

    elif oxygen < 5:
        score += 20

    score += random.randint(0, 10)

    return min(score, 100)

# ==========================
# 🔹 MAIN API
# ==========================
@app.get("/api/ocean-data")
def ocean_data(location: str = "mumbai"):

    # ==========================
    # 🔹 LOCATION
    # ==========================
    coords = locations.get(
        location.lower(),
        locations["mumbai"]
    )
    

    # ==========================
    # 🔹 REAL SEA DATA
    # ==========================
    sea = get_sea_data(
        coords["lat"],
        coords["lon"]
    )

    # ==========================
    # 🔹 CORE PARAMETERS
    # ==========================
    temperature = sea["temperature"]

    sea_level = get_copernicus_sea_level(coords["lat"], coords["lon"])

    salinity = get_copernicus_salinity(coords["lat"], coords["lon"])
    
    print("DEBUG lat/lon going into salinity:", coords["lat"], coords["lon"])

    oxygen = get_real_oxygen(
    coords["lat"],
    coords["lon"]
    )

    # ==========================
    # 🔹 RISK SCORE
    # ==========================
    risk_score = calculate_risk(
        temperature,
        oxygen
    )

    # ==========================
    # 🔹 RISK LEVEL
    # ==========================
    if risk_score < 30:

        risk_level = "Low"

    elif risk_score < 70:

        risk_level = "Medium"

    else:

        risk_level = "High"

    # ==========================
    # 🔹 RISK ENGINE
    # ==========================
    critical_zones = 0

    # High waves
    if sea["wave_height"] > 2:
        critical_zones += 1

    # Low oxygen
    if oxygen < 4.5:
        critical_zones += 1

    # High sea level
    if sea_level > 0.5:
        critical_zones += 1

    # Randomized event count
    high_risk_events = random.randint(
        5,
        20
    )

    # Trend
    risk_trend = random.choice([
        "Improving",
        "Stable",
        "Worsening"
    ])

    # ==========================
    # 🔹 RISK FACTORS
    # ==========================
    risk_factors = [

        {
            "title":
                "Temperature Anomalies",

            "desc":
                f"{temperature:.2f}°C detected",

            "severity":
                (
                    "High"
                    if temperature > 29
                    else "Medium"
                ),

            "value":
                min(
                    int(
                        (temperature / 35) * 100
                    ),
                    100
                )
        },

        {
            "title":
                "Low Oxygen Events",

            "desc":
                f"{oxygen:.2f} mg/L",

            "severity":
                (
                    "Critical"
                    if oxygen < 4.5
                    else "Medium"
                ),

            "value":
                (
                    90
                    if oxygen < 4.5
                    else 50
                )
        },

        {
            "title":
                "Sea Level Rise",

            "desc":
                f"{sea_level:.2f} m",

            "severity":
                (
                    "High"
                    if sea_level > 0.5
                    else "Low"
                ),

            "value":
                min(
                    int(sea_level * 100),
                    100
                )
        },

        {
            "title":
                "Wave Turbulence",

            "desc":
                f"{sea['wave_height']:.2f} m waves",

            "severity":
                (
                    "Critical"
                    if sea["wave_height"] > 2
                    else "Low"
                ),

            "value":
                min(
                    int(
                        sea["wave_height"] * 40
                    ),
                    100
                )
        },

        {
            "title":
                "Wind Speed",

            "desc":
                f"{sea['wind_speed']:.2f} km/h",

            "severity":
                (
                    "High"
                    if sea["wind_speed"] > 20
                    else "Medium"
                ),

            "value":
                min(
                    int(
                        sea["wind_speed"] * 4
                    ),
                    100
                )
        }
    ]

    # ==========================
    # 🔹 ALERTS
    # ==========================
    alerts = []

    # High waves
    if sea["wave_height"] > 2:

        alerts.append({

            "type":
                "ALERT",

            "message":
                "High wave activity detected near Mumbai Port",

            "time":
                "Immediate"
        })

    # Low oxygen
    if oxygen < 4.5:

        alerts.append({

            "type":
                "WARNING",

            "message":
                "Low dissolved oxygen may affect marine life",

            "time":
                "Next 24 hrs"
        })

    # High sea level
    if sea_level > 0.5:

        alerts.append({

            "type":
                "NOTICE",

            "message":
                "Elevated sea level observed near coastal region",

            "time":
                "Monitoring"
        })

    # Strong wind
    if sea["wind_speed"] > 20:

        alerts.append({

            "type":
                "ALERT",

            "message":
                "Strong marine winds may affect vessel navigation",

            "time":
                "Immediate"
        })

    # Stable condition
    if len(alerts) == 0:

        alerts.append({

            "type":
                "NOTICE",

            "message":
                "Marine conditions stable near Mumbai Port",

            "time":
                "Live"
        })

    # ==========================
    # 🔹 TIME
    # ==========================
    indian_time = datetime.utcnow() + timedelta(
        hours=5,
        minutes=30
    )

   # ==========================
    # 🔹 LIVE DATA
    # ==========================
    sea = get_sea_data(
        coords["lat"],
        coords["lon"]
    )

    temperature = round(sea["temperature"], 2)

    sea_level = get_copernicus_sea_level(coords["lat"], coords["lon"])
    LOC = {
    "lat": 19.07, "lon": 72.87}
    print(coords)
    print(type(coords["lat"]))
    print(repr(coords["lat"]))


    salinity = get_copernicus_salinity(coords["lat"], coords["lon"])
        
    oxygen = get_real_oxygen(
    temperature,salinity
    )

    # ==========================
    # 🔹 RISK SCORE
    # ==========================
    risk_score = calculate_risk(
        temperature,
        oxygen
    )

    if risk_score < 30:
        risk_level = "Low"

    elif risk_score < 70:
        risk_level = "Medium"

    else:
        risk_level = "High"

    # ==========================
    # 🔹 ADVISORY
    # ==========================
    advisory = "Safe"

    if sea["wave_height"] > 2.5:
        advisory = "Restricted"

    if sea["wind_speed"] > 20:
        advisory = "Danger"

    if risk_score > 70:
        advisory = "Danger"

    # ==========================
    # 🔹 CLUSTERS
    # ==========================
    clusters = [
        {
            "zone": "Dock Area",
            "risk": "Medium"
        },
        {
            "zone": "Entry Channel",
            "risk": "Low"
        },
        {
            "zone": "Deep Water",
            "risk": risk_level
        }
    ]

    indian_time = (
        datetime.utcnow()
        + timedelta(hours=5, minutes=30)
    )

    # ==========================
    # 🔹 STORE HISTORY
    # ==========================
    history_data["temperature"].append(
        temperature
    )

    history_data["salinity"].append(
        salinity
    )

    history_data["oxygen"].append(
        oxygen
    )

    history_data["timestamps"].append(
        indian_time.strftime("%H:%M:%S")
    )

    MAX_POINTS = 20

    for key in history_data:
        history_data[key] = history_data[key][-MAX_POINTS:]

    # ==========================
    # 🔹 API RESPONSE
    # ==========================
    return {

        "timestamp":
            indian_time.isoformat(),

        "location":
            location,

        "data": {

            "temperature":
                temperature,

            "waveHeight":
                sea["wave_height"],

            "windSpeed":
                sea["wind_speed"],

            "seaLevel":
                sea_level,

            "salinity":
                salinity,

            "oxygen":
                oxygen,

            "riskScore":
                risk_score,

            "riskLevel":
                risk_level,

            "advisory":
                advisory,

            "clusters":
                clusters
        },

        "history":
            history_data
    }

# ==========================
# 🔹 ADVISORY REPORT API
# ==========================
@app.get("/api/advisory")
def advisory():

    try:

        # ==========================
        # 🔹 MUMBAI DATA
        # ==========================
        coords = locations["mumbai"]
        # coords["lat"] = round(float(coords["lat"]), 2)p
        # coords["lon"] = round(float(coords["lon"]), 2)
        coords["lat"] = math.floor(coords["lat"] * 100) / 100
        coords["lon"] = math.floor(coords["lon"] * 100) / 100

        sea = get_sea_data(
            coords["lat"],
            coords["lon"]
        )

        temperature = sea["temperature"]

        sea_level = get_copernicus_sea_level(coords["lat"], coords["lon"])

        salinity = get_copernicus_salinity(coords["lat"], coords["lon"])

    
        oxygen = get_real_oxygen(
        coords["lat"],
        coords["lon"]
        )

        risk_score = calculate_risk(
            temperature,
            oxygen
        )

        # ==========================
        # 🔹 ADVISORIES
        # ==========================
        advisories = []

        # Wave advisory
        if sea["wave_height"] > 2:

            advisories.append({

                "type":
                    "Navigation Warning",

                "severity":
                    "High",

                "title":
                    "High Wave Activity",

                "message":
                    (
                        "Wave turbulence near Mumbai Port "
                        "may affect vessel movement."
                    ),

                "recommendation":
                    (
                        "Restrict small vessel movement "
                        "and increase coastal monitoring."
                    )
            })

        # Oxygen advisory
        if oxygen < 4.5:

            advisories.append({

                "type":
                    "Marine Ecosystem Alert",

                "severity":
                    "Critical",

                "title":
                    "Low Dissolved Oxygen",

                "message":
                    (
                        "Marine oxygen levels are below "
                        "safe ecological threshold."
                    ),

                "recommendation":
                    (
                        "Increase biodiversity monitoring "
                        "and fisheries observation."
                    )
            })

        # Sea level
        if sea_level > 0.5:

            advisories.append({

                "type":
                    "Coastal Alert",

                "severity":
                    "Medium",

                "title":
                    "Elevated Sea Level",

                "message":
                    (
                        "Sea level rise observed "
                        "near coastal infrastructure."
                    ),

                "recommendation":
                    (
                        "Monitor coastal erosion "
                        "and tidal impacts."
                    )
            })

        # Temperature anomaly
        if temperature > 29:

            advisories.append({

                "type":
                    "Thermal Stress",

                "severity":
                    "Medium",

                "title":
                    "Elevated Sea Temperature",

                "message":
                    (
                        "Surface water temperature "
                        "is above normal marine baseline."
                    ),

                "recommendation":
                    (
                        "Track coral stress and "
                        "marine habitat fluctuations."
                    )
            })

        # Stable condition
        if len(advisories) == 0:

            advisories.append({

                "type":
                    "Marine Status",

                "severity":
                    "Low",

                "title":
                    "Stable Marine Conditions",

                "message":
                    (
                        "Mumbai coastal marine "
                        "conditions remain stable."
                    ),

                "recommendation":
                    (
                        "Continue routine marine "
                        "environment monitoring."
                    )
            })

        # ==========================
        # 🔹 SUMMARY
        # ==========================
        summary = {

            "riskScore":
                risk_score,

            "waveHeight":
                sea["wave_height"],

            "oxygen":
                oxygen,

            "temperature":
                temperature,

            "seaLevel":
                sea_level
        }

        # ==========================
        # 🔹 RESPONSE
        # ==========================
        return {

            "status":
                "success",

            "location":
                "Mumbai Port",

            "summary":
                summary,

            "advisories":
                advisories
        }

    except Exception as e:

        print(
            "Advisory API Error:",
            e
        )

        return {

            "status":
                "error",

            "message":
                str(e)
        }
    
# ==========================
# 🔹 DOWNLOADABLE PDF REPORT
# ==========================
@app.get("/api/download-report")
def download_report():

    try:

        coords = locations["mumbai"]

        sea = get_sea_data(
            coords["lat"],
            coords["lon"]
        )

        temperature = sea["temperature"]

        sea_level = get_copernicus_sea_level(coords["lat"], coords["lon"])

        salinity = get_copernicus_salinity(coords["lat"], coords["lon"])

    
        oxygen = get_real_oxygen(
        coords["lat"],
        coords["lon"]
        )

        risk_score = calculate_risk(
            temperature,
            oxygen
        )

        report_path = "mumbai_marine_report.pdf"

        doc = SimpleDocTemplate(
            report_path,
            pagesize=letter
        )

        styles = getSampleStyleSheet()

        elements = []

        title = Paragraph(
            "MarineSense — Mumbai Port Advisory Report",
            styles['Title']
        )

        elements.append(title)
        elements.append(Spacer(1, 20))

        report_data = [

            f"Temperature: {temperature:.2f} °C",

            f"Wave Height: {sea['wave_height']:.2f} m",

            f"Wind Speed: {sea['wind_speed']:.2f} km/h",

            f"Sea Level: {sea_level:.2f} m",

            f"Salinity: {salinity:.2f} PSU",

            f"Dissolved Oxygen: {oxygen:.2f} mg/L",

            f"Risk Score: {risk_score}",

            f"Generated: {datetime.utcnow()} UTC"
        ]

        for item in report_data:

            p = Paragraph(item, styles['BodyText'])

            elements.append(p)
            elements.append(Spacer(1, 10))

        recommendation_title = Paragraph(
            "Recommendations",
            styles['Heading2']
        )

        elements.append(recommendation_title)

        recommendations = [

            "Increase monitoring of dissolved oxygen near coastal biodiversity zones.",

            "Restrict small vessel operations during high wave activity.",

            "Continue sea-level surveillance for Mumbai coastal infrastructure.",

            "Track thermal stress for marine ecosystem conservation."
        ]

        for rec in recommendations:

            p = Paragraph(f"• {rec}", styles['BodyText'])

            elements.append(p)
            elements.append(Spacer(1, 6))

        doc.build(elements)

        return FileResponse(
            report_path,
            media_type='application/pdf',
            filename='Mumbai_Marine_Advisory_Report.pdf'
        )

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }
    
 
# ==========================
# 🔹 REAL BIODIVERSITY API
# ==========================
@app.get("/api/biodiversity")
def biodiversity():

    try:

        # 🔹 Mumbai coastal coordinates
        lat = 19.0760
        lon = 72.8777

        # 🔹 OBIS Marine Biodiversity API
        url = (
            "https://api.obis.org/v3/occurrence"
            f"?decimalLatitude={lat}"
            f"&decimalLongitude={lon}"
            "&radius=200000"
            "&size=500"
            "&marine_only=true"
        )

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        results = data.get(
            "results",
            []
        )

        # ==========================
        # 🔹 UNIQUE SPECIES
        # ==========================
        species_set = set()

        for item in results:

            species = item.get(
                "scientificName"
            )

            if (
                species and
                len(species) > 3
            ):

                species_set.add(species)

        species_data = list(species_set)

        # ==========================
        # 🔹 TOP SPECIES
        # ==========================
        top_species = species_data[:20]

        # ==========================
        # 🔹 BEACHES
        # ==========================
        beaches = [

            "Versova Beach",

            "Juhu Beach",

            "Aksa Beach",

            "Girgaon Chowpatty"
        ]

        biodiversity_cards = []

        # ==========================
        # 🔹 GENERATE CARDS
        # ==========================
        for i, beach in enumerate(beaches):

            start_index = i * 4
            end_index = start_index + 4

            selected_species = top_species[
                start_index:end_index
            ]

            if len(selected_species) == 0:

                selected_species = [
                    "No Species Data"
                ]

            biodiversity_cards.append({

                "beach":
                    beach,

                "species":
                    selected_species,

                "biodiversityScore":
                    random.randint(70, 95),

                "riskLevel":
                    random.choice([
                        "Low",
                        "Medium"
                    ])
            })

        # ==========================
        # 🔹 FINAL RESPONSE
        # ==========================
        return {

            "status":
                "success",

            "location":
                "Mumbai Coast",

            "totalSpecies":
                len(species_data),

            "records":
                len(results),

            "topSpecies":
                top_species,

            "data":
                biodiversity_cards
        }

    except Exception as e:

        print(
            "Biodiversity API Error:",
            e
        )

        return {

            "status":
                "error",

            "message":
                str(e)
        }
# ============================================
# ⚠️ RISK ANALYSIS API
# ============================================
@app.get("/api/risk-analysis")
def risk_analysis():

    try:

        # =====================================
        # 🔹 MUMBAI PORT LOCATION
        # =====================================
        coords = locations["mumbai"]

        # =====================================
        # 🔹 LIVE SEA DATA
        # =====================================
        sea = get_sea_data(
            coords["lat"],
            coords["lon"]
        )

        # =====================================
        # 🔹 LIVE PARAMETERS
        # =====================================
        temperature = round(
            sea["temperature"],
            2
        )

        sea_level = get_copernicus_sea_level(coords["lat"], coords["lon"])

        salinity = get_copernicus_salinity(coords["lat"], coords["lon"])

    
        oxygen = get_real_oxygen(
        coords["lat"],
        coords["lon"]
        )

        # =====================================
        # 🔹 RISK SCORE
        # =====================================
        risk_score = calculate_risk(
            temperature,
            oxygen
        )

        # =====================================
        # 🔹 RISK LEVEL
        # =====================================
        if risk_score < 30:

            risk_level = "Low"

        elif risk_score < 70:

            risk_level = "Medium"

        else:

            risk_level = "High"

        # =====================================
        # 🔹 CRITICAL ZONES
        # =====================================
        critical_zones = 0

        if sea["wave_height"] > 2:
            critical_zones += 1

        if oxygen < 4.5:
            critical_zones += 1

        if sea_level > 0.5:
            critical_zones += 1

        if sea["wind_speed"] > 20:
            critical_zones += 1

        # =====================================
        # 🔹 TREND
        # =====================================
        if risk_score < 30:

            trend = "Improving"

        elif risk_score < 70:

            trend = "Stable"

        else:

            trend = "Worsening"

        # =====================================
        # 🔹 RISK FACTORS
        # =====================================
        factors = [

            {
                "title":
                    "Temperature Anomalies",

                "description":
                    (
                        f"Current marine "
                        f"temperature is "
                        f"{temperature:.2f}°C"
                    ),

                "severity":
                    (
                        "High"
                        if temperature > 29
                        else "Medium"
                    ),

                "score":
                    min(
                        int(
                            (temperature / 35) * 100
                        ),
                        100
                    )
            },

            {
                "title":
                    "Wave Turbulence",

                "description":
                    (
                        f"Wave height "
                        f"{sea['wave_height']:.2f} m"
                    ),

                "severity":
                    (
                        "Critical"
                        if sea["wave_height"] > 2
                        else "Low"
                    ),

                "score":
                    min(
                        int(
                            sea["wave_height"] * 40
                        ),
                        100
                    )
            },

            {
                "title":
                    "Wind Instability",

                "description":
                    (
                        f"Wind speed "
                        f"{sea['wind_speed']:.2f} km/h"
                    ),

                "severity":
                    (
                        "High"
                        if sea["wind_speed"] > 20
                        else "Medium"
                    ),

                "score":
                    min(
                        int(
                            sea["wind_speed"] * 4
                        ),
                        100
                    )
            },

            {
                "title":
                    "Low Dissolved Oxygen",

                "description":
                    (
                        f"Oxygen level "
                        f"{oxygen:.2f} mg/L"
                    ),

                "severity":
                    (
                        "Critical"
                        if oxygen < 4.5
                        else "Low"
                    ),

                "score":
                    (
                        90
                        if oxygen < 4.5
                        else 40
                    )
            },

            {
                "title":
                    "Sea Level Rise",

                "description":
                    (
                        f"Sea level "
                        f"{sea_level:.2f} m"
                    ),

                "severity":
                    (
                        "High"
                        if sea_level > 0.5
                        else "Low"
                    ),

                "score":
                    min(
                        int(
                            sea_level * 100
                        ),
                        100
                    )
            }
        ]

        # =====================================
        # 🔹 ALERTS
        # =====================================
        alerts = []

        if sea["wave_height"] > 2:

            alerts.append({

                "type":
                    "ALERT",

                "message":
                    (
                        "High wave activity "
                        "detected near Mumbai Port"
                    ),

                "time":
                    "Immediate"
            })

        if oxygen < 4.5:

            alerts.append({

                "type":
                    "WARNING",

                "message":
                    (
                        "Low dissolved oxygen "
                        "may affect marine biodiversity"
                    ),

                "time":
                    "Next 24 hrs"
            })

        if sea["wind_speed"] > 20:

            alerts.append({

                "type":
                    "ALERT",

                "message":
                    (
                        "Strong marine winds "
                        "may affect vessel navigation"
                    ),

                "time":
                    "Immediate"
            })

        if sea_level > 0.5:

            alerts.append({

                "type":
                    "NOTICE",

                "message":
                    (
                        "Elevated sea level "
                        "detected near coastal region"
                    ),

                "time":
                    "Monitoring"
            })

        # =====================================
        # 🔹 NO ALERT CASE
        # =====================================
        if len(alerts) == 0:

            alerts.append({

                "type":
                    "NOTICE",

                "message":
                    (
                        "Marine conditions "
                        "currently stable"
                    ),

                "time":
                    "Live"
            })

        # =====================================
        # 🔹 RESPONSE
        # =====================================
        return {

            "status":
                "success",

            "location":
                "Mumbai Port",

            "riskScore":
                risk_score,

            "riskLevel":
                risk_level,

            "criticalZones":
                critical_zones,

            "trend":
                trend,

            "factors":
                factors,

            "alerts":
                alerts,

            "liveData": {

                "temperature":
                    temperature,

                "waveHeight":
                    sea["wave_height"],

                "windSpeed":
                    sea["wind_speed"],

                "seaLevel":
                    sea_level,

                "salinity":
                    salinity,

                "oxygen":
                    oxygen
            }
        }

    except Exception as e:

        print(
            "❌ Risk API Error:",
            e
        )

        return {

            "status":
                "error",

            "message":
                str(e)
        }