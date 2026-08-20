from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import requests
import random
import time
import math
import os
from typing import Optional
from datetime import datetime, timedelta, timezone

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import copernicusmarine
import threading

# ============================================================
# APP
# ============================================================

app = FastAPI()


_copernicus_executor = ThreadPoolExecutor(max_workers=4)

def _run_with_timeout(fn, *args, timeout=25, **kwargs):
    future = _copernicus_executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=timeout)
    except FutureTimeoutError:
        raise Exception(f"Copernicus call timed out after {timeout}s")

_cache_locks = {}

def _get_lock(cache_key):
    if cache_key not in _cache_locks:
        _cache_locks[cache_key] = threading.Lock()
    return _cache_locks[cache_key]

# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=0.0):
    try:
        value = float(value)

        if not math.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# CACHE SETTINGS
# ============================================================

CACHE_DURATION_SECONDS = 1200
_sea_data_cache = {}
SEA_DATA_CACHE_SECONDS = 1200

# ============================================================
# LOCATIONS / PORTS
# ============================================================

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

active_location = "mumbai"
# ============================================================
# PER-PORT HISTORY
# ============================================================

history_data = {}


def get_port_history(location):

    location = location.lower().strip()

    if location not in history_data:

        history_data[location] = {

            "temperature": [],
            "waveHeight": [],
            "windSpeed": [],
            "salinity": [],
            "currentVelocity": [],
            "timestamps": []
        }

    return history_data[location]


# ============================================================
# UPDATE PER-PORT HISTORY
# ============================================================

def update_port_history(
    location,
    temperature,
    wave_height,
    wind_speed,
    salinity,
    current_velocity,
    timestamp
):

    history = get_port_history(location)

    history["temperature"].append(
        round(safe_float(temperature, 28.0), 2)
    )

    history["waveHeight"].append(
        round(safe_float(wave_height, 1.0), 2)
    )

    history["windSpeed"].append(
        round(safe_float(wind_speed, 10.0), 2)
    )

    history["salinity"].append(
        round(safe_float(salinity, 35.0), 2)
    )

    history["currentVelocity"].append(
        round(safe_float(current_velocity, 0.0), 2)
    )

    history["timestamps"].append(timestamp)

    # Keep only four points
    for key in history:

        history[key] = history[key][-4:]

    return history


# ============================================================
# COPERNICUS CACHES
# ============================================================

_sea_level_cache = {}
_salinity_cache = {}
_current_cache = {}


# ============================================================
# COPERNICUS SALINITY
# ============================================================

def get_copernicus_salinity(lat, lon):

    lat = round(lat, 2)
    lon = round(lon, 2)

    cache_key = f"{lat},{lon}"

    now = time.time()

    if cache_key in _salinity_cache:

        cached_value, cached_time = _salinity_cache[cache_key]

        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    try:

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

        salinity = salinity_ds["so"].sel(
            latitude=lat,
            longitude=lon,
            method="nearest"
        )

        # Safely select surface depth
        if "depth" in salinity.dims:

            salinity_surface = salinity.isel(
                depth=0
            )

        else:

            salinity_surface = salinity

        value = safe_float(
            salinity_surface.values.flat[0],
            35.0
        )

        value = round(value, 2)

        print(
            "Salinity:",
            lat,
            lon,
            value
        )

        _salinity_cache[cache_key] = (
            value,
            now
        )

        return value

    except Exception as e:

        print(
            "Salinity Error:",
            e
        )

        if cache_key in _salinity_cache:
            return _salinity_cache[cache_key][0]

        return 35.0


# ============================================================
# COPERNICUS OCEAN CURRENT
# ============================================================

def get_copernicus_current(lat, lon):

    lat = round(lat, 2)
    lon = round(lon, 2)

    cache_key = f"{lat},{lon}"

    now = time.time()

    if cache_key in _current_cache:

        cached_value, cached_time = _current_cache[cache_key]

        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    try:

        date = "2026-07-14"

        current_ds = copernicusmarine.open_dataset(
            dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i",
            minimum_longitude=lon - 0.5,
            maximum_longitude=lon + 0.5,
            minimum_latitude=lat - 0.5,
            maximum_latitude=lat + 0.5,
            start_datetime=date,
            end_datetime=date,
            variables=["uo", "vo"]
        )

        uo_field = current_ds["uo"]
        vo_field = current_ds["vo"]

        if "time" in uo_field.dims:
            uo_field = uo_field.isel(time=0)
        if "time" in vo_field.dims:
            vo_field = vo_field.isel(time=0)
        if "depth" in uo_field.dims:
            uo_field = uo_field.isel(depth=0)
        if "depth" in vo_field.dims:
            vo_field = vo_field.isel(depth=0)

        try:
            uo_value = safe_float(
                uo_field.sel(latitude=lat, longitude=lon, method="nearest").values.flat[0],
                float("nan")
            )
            vo_value = safe_float(
                vo_field.sel(latitude=lat, longitude=lon, method="nearest").values.flat[0],
                float("nan")
            )
        except Exception:
            uo_value = float("nan")
            vo_value = float("nan")

        # If the port point is land/zero-current, use the closest valid ocean cell.
        if (not math.isfinite(uo_value) or not math.isfinite(vo_value) or
                (abs(uo_value) < 1e-9 and abs(vo_value) < 1e-9)):
            try:
                lats = uo_field["latitude"].values
                lons = uo_field["longitude"].values
                uo_values = uo_field.values
                vo_values = vo_field.values
                best = None
                for i, grid_lat in enumerate(lats):
                    for j, grid_lon in enumerate(lons):
                        u = safe_float(uo_values[i, j], float("nan"))
                        v = safe_float(vo_values[i, j], float("nan"))
                        if not math.isfinite(u) or not math.isfinite(v):
                            continue
                        magnitude = math.sqrt(u * u + v * v)
                        if magnitude < 1e-9:
                            continue
                        distance = (float(grid_lat) - lat) ** 2 + (float(grid_lon) - lon) ** 2
                        if best is None or distance < best[0]:
                            best = (distance, u, v, float(grid_lat), float(grid_lon))
                if best is not None:
                    uo_value = best[1]
                    vo_value = best[2]
                    print("Ocean current fallback grid:", best[3], best[4])
            except Exception as fallback_error:
                print("Ocean current fallback search error:", fallback_error)

        if not math.isfinite(uo_value):
            uo_value = 0.0
        if not math.isfinite(vo_value):
            vo_value = 0.0

        velocity = math.sqrt(
            uo_value ** 2 +
            vo_value ** 2
        )

        direction = (
            math.degrees(
                math.atan2(
                    uo_value,
                    vo_value
                )
            ) + 360
        ) % 360

        result = {

            "velocity":
                round(velocity, 2),

            "direction":
                round(direction, 1),

            "uo":
                round(uo_value, 3),

            "vo":
                round(vo_value, 3)
        }

        print(
            "Ocean current:",
            lat,
            lon,
            result
        )

        _current_cache[cache_key] = (
            result,
            now
        )

        return result

    except Exception as e:

        print(
            "Current Error:",
            e
        )

        if cache_key in _current_cache:
            return _current_cache[cache_key][0]

        return {

            "velocity": 0.0,
            "direction": 0.0,
            "uo": 0.0,
            "vo": 0.0
        }

# ============================================================
# OPEN METEO
# LAST 4 HOURLY POINTS
#
# T-3
# T-2
# T-1
# T
# ============================================================

last_sea_data = {

    "temperature": 28.0,
    "wave_height": 1.0,
    "wind_speed": 10.0
}


# ============================================================
# OPEN METEO CACHE
# ============================================================

_sea_data_cache = {}
SEA_DATA_CACHE_SECONDS = 1200   # data is hourly anyway — 5 min reuse is plenty


def get_sea_data(lat, lon):

    lat_r = round(lat, 2)
    lon_r = round(lon, 2)

    cache_key = f"{lat_r},{lon_r}"

    now = time.time()

    if cache_key in _sea_data_cache:
        cached_value, cached_time = _sea_data_cache[cache_key]
        if now - cached_time < SEA_DATA_CACHE_SECONDS:
            return cached_value

    with _get_lock(cache_key):

        # Re-check cache after acquiring the lock — another thread
        # may have just finished fetching this while we were waiting.
        now = time.time()

        if cache_key in _sea_data_cache:
            cached_value, cached_time = _sea_data_cache[cache_key]
            if now - cached_time < SEA_DATA_CACHE_SECONDS:
                return cached_value

        try:

            # ====================================================
            # 1. MARINE API
            # ====================================================

            marine_url = (

                "https://marine-api.open-meteo.com/v1/marine"

                f"?latitude={lat}"

                f"&longitude={lon}"

                "&hourly=sea_surface_temperature,wave_height"

                "&past_days=1"

                "&forecast_days=1"

                "&timezone=Asia%2FKolkata"
            )

            marine_response = requests.get(
                marine_url,
                timeout=15
            )

            print(
                "Marine API status:",
                marine_response.status_code
            )

            if marine_response.status_code != 200:

                print(
                    "Marine API response:",
                    marine_response.text
                )

                raise Exception(
                    f"Marine API HTTP "
                    f"{marine_response.status_code}"
                )

            marine_data = marine_response.json()


            # ====================================================
            # 2. WEATHER API
            # ====================================================

            weather_url = (

                "https://api.open-meteo.com/v1/forecast"

                f"?latitude={lat}"

                f"&longitude={lon}"

                "&hourly=wind_speed_10m"

                "&past_days=1"

                "&forecast_days=1"

                "&timezone=Asia%2FKolkata"
            )

            weather_response = requests.get(
                weather_url,
                timeout=15
            )

            print(
                "Weather API status:",
                weather_response.status_code
            )

            if weather_response.status_code != 200:

                print(
                    "Weather API response:",
                    weather_response.text
                )

                raise Exception(
                    f"Weather API HTTP "
                    f"{weather_response.status_code}"
                )

            weather_data = weather_response.json()


            # ====================================================
            # 3. EXTRACT MARINE DATA
            # ====================================================

            marine_times = (
                marine_data
                .get("hourly", {})
                .get("time", [])
            )

            temperatures = (
                marine_data
                .get("hourly", {})
                .get(
                    "sea_surface_temperature",
                    []
                )
            )

            waves = (
                marine_data
                .get("hourly", {})
                .get(
                    "wave_height",
                    []
                )
            )


            # ====================================================
            # 4. EXTRACT WEATHER DATA
            # ====================================================

            weather_times = (
                weather_data
                .get("hourly", {})
                .get("time", [])
            )

            winds = (
                weather_data
                .get("hourly", {})
                .get(
                    "wind_speed_10m",
                    []
                )
            )


            # ====================================================
            # 5. WIND LOOKUP
            # ====================================================

            wind_lookup = dict(
                zip(
                    weather_times,
                    winds
                )
            )


            # ====================================================
            # 6. CURRENT IST HOUR
            #
            # Open-Meteo timezone is Asia/Kolkata.
            # Therefore use IST here as well.
            # ====================================================

            ist = timezone(
                timedelta(hours=5, minutes=30)
            )

            now_ist = datetime.now(ist)

            current_hour = now_ist.replace(
                minute=0,
                second=0,
                microsecond=0
            ).replace(
                tzinfo=None
            )


            # ====================================================
            # 7. BUILD ALL HOURLY DATA
            # ====================================================

            all_history = []

            for i, time_string in enumerate(
                marine_times
            ):

                if i >= len(temperatures):
                    continue

                if i >= len(waves):
                    continue

                if time_string not in wind_lookup:
                    continue

                try:

                    point_time = datetime.fromisoformat(
                        time_string
                    )

                    temperature = safe_float(
                        temperatures[i],
                        28.0
                    )

                    wave_height = safe_float(
                        waves[i],
                        1.0
                    )

                    wind_speed = safe_float(
                        wind_lookup[time_string],
                        10.0
                    )

                    all_history.append({

                        "time":
                            time_string,

                        "temperature":
                            round(
                                temperature,
                                2
                            ),

                        "wave_height":
                            round(
                                wave_height,
                                2
                            ),

                        "wind_speed":
                            round(
                                wind_speed,
                                2
                            )
                    })

                except Exception:
                    continue


            # ====================================================
            # 8. SELECT EXACT 4-HOUR WINDOW
            #
            # T-3
            # T-2
            # T-1
            # T
            # ====================================================

            filtered_history = []

            start_hour = (
                current_hour -
                timedelta(hours=3)
            )

            for point in all_history:

                try:

                    point_time = datetime.fromisoformat(
                        point["time"]
                    )

                    if (
                        start_hour
                        <= point_time
                        <= current_hour
                    ):

                        filtered_history.append(
                            point
                        )

                except Exception:
                    continue


            # ====================================================
            # 9. SORT BY TIME
            # ====================================================

            filtered_history.sort(
                key=lambda x: x["time"]
            )


            # ====================================================
            # 10. TAKE LAST 4
            # ====================================================

            history = filtered_history[-4:]


            # ====================================================
            # 11. FALLBACK ONLY IF WINDOW IS EMPTY
            # ====================================================

            if len(history) == 0:

                history = all_history[-4:]


            if len(history) == 0:

                raise Exception(
                    "Open-Meteo returned no hourly data"
                )


            # ====================================================
            # 12. CURRENT VALUE
            # ====================================================

            current = history[-1]


            result = {

                "temperature":
                    current["temperature"],

                "wave_height":
                    current["wave_height"],

                "wind_speed":
                    current["wind_speed"],

                "history":
                    history
            }

            last_sea_data.update({
                "temperature": current["temperature"],
                "wave_height": current["wave_height"],
                "wind_speed": current["wind_speed"]
            })

            _sea_data_cache[cache_key] = (
                result,
                now
            )


            # ====================================================
            # DEBUG
            # ====================================================

            print(
                "======================================"
            )

            print(
                "MarineSense coordinates:",
                lat,
                lon
            )

            print(
                "Current IST hour:",
                current_hour
            )

            print(
                "Graph points:",
                len(history)
            )

            for point in history:

                print(

                    point["time"],

                    "| SST:",
                    point["temperature"],

                    "| Wave:",
                    point["wave_height"],

                    "| Wind:",
                    point["wind_speed"]
                )

            print(
                "======================================"
            )


            return result


        except Exception as e:

            print(
                "OpenMeteo Error:",
                e
            )

            if cache_key in _sea_data_cache:
                return _sea_data_cache[cache_key][0]

            return {

                "temperature":
                    last_sea_data["temperature"],

                "wave_height":
                    last_sea_data["wave_height"],

                "wind_speed":
                    last_sea_data["wind_speed"],

                "history": []
            }

# ============================================================
# COPERNICUS SEA LEVEL
# ============================================================

def get_copernicus_sea_level(lat, lon):

    lat = round(lat, 2)
    lon = round(lon, 2)

    cache_key = f"{lat},{lon}"

    now = time.time()

    if cache_key in _sea_level_cache:
        cached_value, cached_time = _sea_level_cache[cache_key]
        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    with _get_lock(cache_key):

        # Re-check cache after acquiring the lock — another thread
        # may have just finished fetching this while we were waiting.
        now = time.time()

        if cache_key in _sea_level_cache:
            cached_value, cached_time = _sea_level_cache[cache_key]
            if now - cached_time < CACHE_DURATION_SECONDS:
                return cached_value

        try:

            date = "2026-07-14"

            # Wider search area prevents coastal port coordinates from landing on a land cell.
            sealevel_ds = _run_with_timeout(
                copernicusmarine.open_dataset,
                dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
                minimum_longitude=lon - 0.5,
                maximum_longitude=lon + 0.5,
                minimum_latitude=lat - 0.5,
                maximum_latitude=lat + 0.5,
                start_datetime=date,
                end_datetime=date,
                variables=["zos"]
            )

            field = sealevel_ds["zos"]
            if "time" in field.dims:
                field = field.isel(time=0)

            try:
                nearest = field.sel(
                    latitude=lat,
                    longitude=lon,
                    method="nearest"
                )
                value = safe_float(nearest.values.flat[0], float("nan"))
            except Exception:
                value = float("nan")

            # If the port point is land/zero, use the closest valid ocean grid cell.
            if not math.isfinite(value) or abs(value) < 1e-12:
                try:
                    lats = field["latitude"].values
                    lons = field["longitude"].values
                    values = field.values
                    best = None
                    for i, grid_lat in enumerate(lats):
                        for j, grid_lon in enumerate(lons):
                            candidate = safe_float(values[i, j], float("nan"))
                            if not math.isfinite(candidate) or abs(candidate) < 1e-12:
                                continue
                            distance = (float(grid_lat) - lat) ** 2 + (float(grid_lon) - lon) ** 2
                            if best is None or distance < best[0]:
                                best = (distance, candidate, float(grid_lat), float(grid_lon))
                    if best is not None:
                        value = best[1]
                        print("Sea level fallback grid:", best[2], best[3])
                except Exception as fallback_error:
                    print("Sea level fallback search error:", fallback_error)

            if not math.isfinite(value):
                value = 0.0

            value = round(value, 2)

            print(
                "Sea level:",
                lat,
                lon,
                value
            )

            _sea_level_cache[cache_key] = (
                value,
                now
            )

            return value

        except Exception as e:

            print(
                "Sea Level Error:",
                e
            )

            if cache_key in _sea_level_cache:
                return _sea_level_cache[cache_key][0]

            return 0.0 


# ========================================================
# 4. COPERNICUS (run in parallel instead of sequentially)
# ========================================================

    sea_level_future = _copernicus_executor.submit(
    get_copernicus_sea_level, coords["lat"], coords["lon"]
)
    salinity_future = _copernicus_executor.submit(
    get_copernicus_salinity, coords["lat"], coords["lon"]
)
    current_future = _copernicus_executor.submit(
    get_copernicus_current, coords["lat"], coords["lon"]
)

    sea_level = safe_float(sea_level_future.result(), 0.0)
    salinity = safe_float(salinity_future.result(), 35.0)
    current = current_future.result()

    current_velocity = safe_float(current.get("velocity"), 0.0)
    current_direction = safe_float(current.get("direction"), 0.0)

# ============================================================
# RISK CALCULATION
# ============================================================

def calculate_risk(
    temp,
    current_velocity
):

    score = 0

    if temp > 30:

        score += 40

    elif temp > 28:

        score += 20


    if current_velocity > 1.5:

        score += 40

    elif current_velocity > 0.8:

        score += 20


    score += random.randint(
        0,
        10
    )

    return min(
        score,
        100
    )


# ============================================================
# OCEAN DATA API
# ============================================================

@app.get("/api/ocean-data")
def ocean_data(
    location: str = "mumbai"
):
    global active_location

    location = (
        location
        .lower()
        .strip()
    )

    if location not in locations:
        location = "mumbai"

    active_location = location
    coords = locations[location]

    print("================================")
    print("Selected Port:", coords["name"])
    print("Latitude:", coords["lat"])
    print("Longitude:", coords["lon"])

    # ========================================================
    # 3. OPEN METEO
    # ========================================================

    sea = get_sea_data(

        coords["lat"],
        coords["lon"]
    )


    temperature = safe_float(
        sea["temperature"],
        28.0
    )

    wave_height = safe_float(
        sea["wave_height"],
        1.0
    )

    wind_speed = safe_float(
        sea["wind_speed"],
        10.0
    )


    # ========================================================
    # 4. COPERNICUS
    # ========================================================

    sea_level = safe_float(

        get_copernicus_sea_level(

            coords["lat"],
            coords["lon"]
        ),

        0.0
    )


    salinity = safe_float(

        get_copernicus_salinity(

            coords["lat"],
            coords["lon"]
        ),

        35.0
    )


    current = get_copernicus_current(

        coords["lat"],
        coords["lon"]
    )


    current_velocity = safe_float(

        current.get(
            "velocity"
        ),

        0.0
    )


    current_direction = safe_float(

        current.get(
            "direction"
        ),

        0.0
    )


    # ========================================================
    # 5. RISK
    # ========================================================

    risk_score = calculate_risk(

        temperature,
        current_velocity
    )


    if risk_score < 30:

        risk_level = "Low"

    elif risk_score < 70:

        risk_level = "Medium"

    else:

        risk_level = "High"


    # ========================================================
    # 6. ADVISORY
    # ========================================================

    advisory = "Safe"


    if wave_height > 2.5:

        advisory = "Restricted"


    if wind_speed > 20:

        advisory = "Danger"


    if risk_score > 70:

        advisory = "Danger"


    # ========================================================
    # 7. CLUSTERS
    # ========================================================

    clusters = [

        {
            "zone":
                "Dock Area",

            "risk":
                "Medium"
        },

        {
            "zone":
                "Entry Channel",

            "risk":
                "Low"
        },

        {
            "zone":
                "Deep Water",

            "risk":
                risk_level
        }
    ]


    # ========================================================
    # 8. IST TIME
    # ========================================================

    ist = timezone(
        timedelta(
            hours=5,
            minutes=30
        )
    )

    indian_time = datetime.now(
        ist
    )


    # ========================================================
    # 9. OPEN-METEO HISTORY
    # ========================================================

    graph_history = sea.get(
        "history",
        []
    )


    clean_history = []


    for point in graph_history:

        clean_history.append({

            "time":
                point.get(
                    "time",
                    ""
                ),

            "temperature":
                safe_float(
                    point.get(
                        "temperature"
                    ),
                    temperature
                ),

            "wave_height":
                safe_float(
                    point.get(
                        "wave_height"
                    ),
                    wave_height
                ),

            "wind_speed":
                safe_float(
                    point.get(
                        "wind_speed"
                    ),
                    wind_speed
                )
        })


    # ========================================================
    # 10. ADD SALINITY + CURRENT HISTORY
    #
    # These are stored separately per port.
    # ========================================================

    port_history = update_port_history(

        location,

        temperature,

        wave_height,

        wind_speed,

        salinity,

        current_velocity,

        indian_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )


    # ========================================================
    # 11. BUILD COMBINED HISTORY
    #
    # Open-Meteo provides real hourly:
    # temperature / wave / wind
    #
    # Copernicus provides:
    # salinity / current
    # ========================================================

    combined_history = []


    # Prefer Open-Meteo's actual 4 hourly timestamps
    if len(clean_history) > 0:

        for i, point in enumerate(
            clean_history
        ):

            if i < len(
                port_history[
                    "salinity"
                ]
            ):

                salinity_value = (
                    port_history[
                        "salinity"
                    ][i]
                )

            else:

                salinity_value = salinity


            if i < len(
                port_history[
                    "currentVelocity"
                ]
            ):

                current_value = (
                    port_history[
                        "currentVelocity"
                    ][i]
                )

            else:

                current_value = current_velocity


            combined_history.append({

                "time":
                    point["time"],

                "temperature":
                    point["temperature"],

                "wave_height":
                    point["wave_height"],

                "wind_speed":
                    point["wind_speed"],

                "salinity":
                    salinity_value,

                "currentVelocity":
                    current_value
            })


    # If Open-Meteo history failed,
    # use per-port history.
    else:

        timestamps = port_history[
            "timestamps"
        ]

        for i in range(
            len(timestamps)
        ):

            combined_history.append({

                "time":
                    timestamps[i],

                "temperature":
                    port_history[
                        "temperature"
                    ][i],

                "wave_height":
                    port_history[
                        "waveHeight"
                    ][i],

                "wind_speed":
                    port_history[
                        "windSpeed"
                    ][i],

                "salinity":
                    port_history[
                        "salinity"
                    ][i],

                "currentVelocity":
                    port_history[
                        "currentVelocity"
                    ][i]
            })


    # ========================================================
    # 12. FINAL RESPONSE
    # ========================================================

    response = {

        "timestamp":
            indian_time.isoformat(),

        "location":
            location,

        "locationName":
            coords["name"],

        "coordinates": {

            "lat":
                coords["lat"],

            "lon":
                coords["lon"]
        },

        "data": {

            "temperature":
                temperature,

            "waveHeight":
                wave_height,

            "windSpeed":
                wind_speed,

            "seaLevel":
                sea_level,

            "salinity":
                salinity,

            "currentVelocity":
                current_velocity,

            "currentDirection":
                current_direction,

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
            combined_history
    }


    print(
        "Final graph points:",
        len(combined_history)
    )

    print(
        "================================"
    )


    return response

# ============================================================
# ADVISORY API
# ============================================================
@app.get("/api/advisory")
def advisory(location: Optional[str] = None):

    try:
        global active_location

        # ----------------------------------------------------
        # SELECT LOCATION
        # ----------------------------------------------------
        if not location:
            location = active_location

        location = location.lower().strip()

        if location not in locations:
            location = active_location

        # Save selected location
        active_location = location

        # Get selected port coordinates
        coords = locations[location]

        print("======================================")
        print("ADVISORY PORT:", location)
        print(
            "ADVISORY COORDINATES:",
            coords["lat"],
            coords["lon"]
        )

        # ----------------------------------------------------
        # MARINE DATA
        # ----------------------------------------------------
        sea = get_sea_data(
            coords["lat"],
            coords["lon"]
        )

        temperature = safe_float(
            sea.get("temperature"),
            28.0
        )

        wave_height = safe_float(
            sea.get("wave_height"),
            1.0
        )

        # ----------------------------------------------------
        # SEA LEVEL
        # ----------------------------------------------------
        sea_level = safe_float(
            get_copernicus_sea_level(
                coords["lat"],
                coords["lon"]
            ),
            0.0
        )

        # ----------------------------------------------------
        # SALINITY
        # ----------------------------------------------------
        salinity = safe_float(
            get_copernicus_salinity(
                coords["lat"],
                coords["lon"]
            ),
            35.0
        )

        # ----------------------------------------------------
        # OCEAN CURRENT
        # ----------------------------------------------------
        current = get_copernicus_current(
            coords["lat"],
            coords["lon"]
        )

        current_velocity = safe_float(
            current.get("velocity"),
            0.0
        )

        current_direction = safe_float(
            current.get("direction"),
            0.0
        )

        # ----------------------------------------------------
        # RISK SCORE
        # ----------------------------------------------------
        risk_score = calculate_risk(
            temperature,
            current_velocity
        )

        # ----------------------------------------------------
        # ADVISORIES
        # ----------------------------------------------------
        advisories = []

        # High wave activity
        if wave_height > 2:

            advisories.append({
                "type": "Navigation Warning",

                "severity": "High",

                "title": "High Wave Activity",

                "message": (
                    f"Wave turbulence near {coords['name']} "
                    "may affect vessel movement."
                ),

                "recommendation": (
                    "Restrict small vessel movement "
                    "and increase coastal monitoring."
                )
            })

        # Strong ocean current
        if current_velocity > 1.5:

            advisories.append({
                "type": "Marine Navigation Alert",

                "severity": "Critical",

                "title": "Strong Ocean Current",

                "message": (
                    f"Ocean current velocity is above "
                    f"the safe navigation threshold near "
                    f"{coords['name']}."
                ),

                "recommendation": (
                    "Increase vessel monitoring "
                    "and coastal current observation."
                )
            })

        # Elevated sea level
        if sea_level > 0.5:

            advisories.append({
                "type": "Coastal Alert",

                "severity": "Medium",

                "title": "Elevated Sea Level",

                "message": (
                    f"Elevated sea level detected near "
                    f"{coords['name']}."
                ),

                "recommendation": (
                    "Monitor coastal erosion and tidal impacts."
                )
            })

        # Elevated temperature
        if temperature > 29:

            advisories.append({
                "type": "Thermal Stress",

                "severity": "Medium",

                "title": "Elevated Sea Temperature",

                "message": (
                    f"Surface water temperature near "
                    f"{coords['name']} is elevated."
                ),

                "recommendation": (
                    "Track marine habitat fluctuations."
                )
            })

        # No warnings
        if not advisories:

            advisories.append({
                "type": "Marine Status",

                "severity": "Low",

                "title": "Stable Marine Conditions",

                "message": (
                    f"{coords['name']} marine conditions "
                    "remain stable."
                ),

                "recommendation": (
                    "Continue routine marine monitoring."
                )
            })

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------
        return {

            "status": "success",

            "location": location,

            "locationName": coords["name"],

            "coordinates": {
                "lat": coords["lat"],
                "lon": coords["lon"]
            },

            "summary": {

                "riskScore": risk_score,

                "waveHeight": wave_height,

                "currentVelocity": current_velocity,

                "currentDirection": current_direction,

                "temperature": temperature,

                "seaLevel": sea_level,

                "salinity": salinity
            },

            "advisories": advisories
        }

    # --------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------
    except Exception as e:

        print("Advisory API Error:", e)

        return {
            "status": "error",
            "message": str(e)
        }
# ============================================================
# DOWNLOADABLE PDF REPORT
# ============================================================

@app.get("/api/download-report")
def download_report():

    try:

        coords = locations[
            "mumbai"
        ]

        sea = get_sea_data(

            coords["lat"],
            coords["lon"]
        )

        temperature = sea[
            "temperature"
        ]

        sea_level = get_copernicus_sea_level(

            coords["lat"],
            coords["lon"]
        )

        salinity = get_copernicus_salinity(

            coords["lat"],
            coords["lon"]
        )

        current = get_copernicus_current(

            coords["lat"],
            coords["lon"]
        )

        current_velocity = current[
            "velocity"
        ]

        current_direction = current[
            "direction"
        ]

        risk_score = calculate_risk(

            temperature,
            current_velocity
        )


        report_path = (
            "mumbai_marine_report.pdf"
        )


        doc = SimpleDocTemplate(

            report_path,

            pagesize=letter
        )


        styles = getSampleStyleSheet()

        elements = []


        elements.append(
            Paragraph(
                "MarineSense — Mumbai Port Advisory Report",
                styles["Title"]
            )
        )

        elements.append(
            Spacer(
                1,
                20
            )
        )


        report_data = [

            f"Temperature: "
            f"{temperature:.2f} °C",

            f"Wave Height: "
            f"{sea['wave_height']:.2f} m",

            f"Wind Speed: "
            f"{sea['wind_speed']:.2f} km/h",

            f"Sea Level: "
            f"{sea_level:.2f} m",

            f"Salinity: "
            f"{salinity:.2f} PSU",

            f"Current Velocity: "
            f"{current_velocity:.2f} m/s",

            f"Current Direction: "
            f"{current_direction:.1f}°",

            f"Risk Score: "
            f"{risk_score}",

            f"Generated: "
            f"{datetime.utcnow()} UTC"
        ]


        for item in report_data:

            elements.append(
                Paragraph(
                    item,
                    styles["BodyText"]
                )
            )

            elements.append(
                Spacer(
                    1,
                    10
                )
            )


        elements.append(
            Paragraph(
                "Recommendations",
                styles["Heading2"]
            )
        )


        recommendations = [

            "Increase monitoring of ocean current velocity near coastal biodiversity zones.",

            "Restrict small vessel operations during high wave activity.",

            "Continue sea-level surveillance for Mumbai coastal infrastructure.",

            "Track thermal stress for marine ecosystem conservation."
        ]


        for rec in recommendations:

            elements.append(
                Paragraph(
                    f"• {rec}",
                    styles["BodyText"]
                )
            )

            elements.append(
                Spacer(
                    1,
                    6
                )
            )


        doc.build(
            elements
        )


        return FileResponse(

            report_path,

            media_type="application/pdf",

            filename=(
                "Mumbai_Marine_Advisory_Report.pdf"
            )
        )


    except Exception as e:

        return {

            "status":
                "error",

            "message":
                str(e)
        }

# ============================================================
# BIODIVERSITY API
# ============================================================
@app.get("/api/biodiversity")
def biodiversity(location: str = "mumbai"):

    try:
        global active_location

        location = location.lower().strip()

        if location not in locations:
            location = active_location

        active_location = location
        coords = locations[location]

        lat = coords["lat"]
        lon = coords["lon"]

        url = (
            "https://api.obis.org/v3/occurrence"
            f"?decimalLatitude={lat}"
            f"&decimalLongitude={lon}"
            "&radius=200000"
            "&size=500"
            "&marine_only=true"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        species_set = set()

        for item in results:
            species = item.get("scientificName")
            if species and len(species) > 3:
                species_set.add(species)

        species_data = list(species_set)
        top_species = species_data[:20]

        beaches = ["Zone A", "Zone B", "Zone C", "Zone D"]  # generic — see note below

        biodiversity_cards = []

        for i, beach in enumerate(beaches):
            start_index = i * 4
            end_index = start_index + 4
            selected_species = top_species[start_index:end_index]

            if len(selected_species) == 0:
                selected_species = ["No Species Data"]

            biodiversity_cards.append({
                "beach": beach,
                "species": selected_species,
                "biodiversityScore": random.randint(70, 95),
                "riskLevel": random.choice(["Low", "Medium"])
            })

        return {
            "status": "success",
            "location": location,
            "locationName": coords["name"],
            "totalSpecies": len(species_data),
            "records": len(results),
            "topSpecies": top_species,
            "data": biodiversity_cards
        }

    except Exception as e:
        print("Biodiversity API Error:", e)
        return {"status": "error", "message": str(e)}
    
# ============================================================
# RISK ANALYSIS API
# ============================================================
@app.get("/api/risk-analysis")
def risk_analysis(location: Optional[str] = None):
    try:
        global active_location

        # ----------------------------------------------------
        # SELECT LOCATION
        # ----------------------------------------------------
        if not location:
            location = active_location

        location = location.lower().strip()

        if location not in locations:
            location = active_location

        # Save selected location
        active_location = location

        # Get coordinates
        coords = locations[location]

        print("======================================")
        print("RISK PORT:", location)
        print(
            "RISK COORDINATES:",
            coords["lat"],
            coords["lon"]
        )

        # ----------------------------------------------------
        # MARINE DATA
        # ----------------------------------------------------
        sea = get_sea_data(
            coords["lat"],
            coords["lon"]
        )

        temperature = safe_float(
            sea.get("temperature"),
            28.0
        )

        wave_height = safe_float(
            sea.get("wave_height"),
            1.0
        )

        wind_speed = safe_float(
            sea.get("wind_speed"),
            10.0
        )

        # ----------------------------------------------------
        # SEA LEVEL
        # ----------------------------------------------------
        sea_level = safe_float(
            get_copernicus_sea_level(
                coords["lat"],
                coords["lon"]
            ),
            0.0
        )

        # ----------------------------------------------------
        # SALINITY
        # ----------------------------------------------------
        salinity = safe_float(
            get_copernicus_salinity(
                coords["lat"],
                coords["lon"]
            ),
            35.0
        )

        # ----------------------------------------------------
        # OCEAN CURRENT
        # ----------------------------------------------------
        current = get_copernicus_current(
            coords["lat"],
            coords["lon"]
        )

        current_velocity = safe_float(
            current.get("velocity"),
            0.0
        )

        current_direction = safe_float(
            current.get("direction"),
            0.0
        )

        # ----------------------------------------------------
        # RISK SCORE
        # ----------------------------------------------------
        risk_score = calculate_risk(
            temperature,
            current_velocity
        )

        if risk_score < 30:
            risk_level = "Low"
            trend = "Improving"

        elif risk_score < 70:
            risk_level = "Medium"
            trend = "Stable"

        else:
            risk_level = "High"
            trend = "Worsening"

        # ----------------------------------------------------
        # CRITICAL ZONES
        # ----------------------------------------------------
        critical_zones = 0

        if wave_height > 2:
            critical_zones += 1

        if current_velocity > 1.5:
            critical_zones += 1

        if sea_level > 0.5:
            critical_zones += 1

        if wind_speed > 20:
            critical_zones += 1

        # ----------------------------------------------------
        # RISK FACTORS
        # ----------------------------------------------------
        factors = [

            {
                "title": "Temperature Anomalies",

                "description":
                    f"Current marine temperature is {temperature:.2f}°C",

                "severity":
                    "High" if temperature > 29 else "Medium",

                "score":
                    min(int((temperature / 35) * 100), 100)
            },

            {
                "title": "Wave Turbulence",

                "description":
                    f"Wave height {wave_height:.2f} m",

                "severity":
                    "Critical" if wave_height > 2 else "Low",

                "score":
                    min(int(wave_height * 40), 100)
            },

            {
                "title": "Wind Instability",

                "description":
                    f"Wind speed {wind_speed:.2f} km/h",

                "severity":
                    "High" if wind_speed > 20 else "Medium",

                "score":
                    min(int(wind_speed * 4), 100)
            },

            {
                "title": "Ocean Current Velocity",

                "description":
                    f"Current velocity {current_velocity:.2f} m/s",

                "severity":
                    "Critical"
                    if current_velocity > 1.5
                    else "Low",

                "score":
                    90
                    if current_velocity > 1.5
                    else 40
            },

            {
                "title": "Sea Level Rise",

                "description":
                    f"Sea level {sea_level:.2f} m",

                "severity":
                    "High" if sea_level > 0.5 else "Low",

                "score":
                    min(int(sea_level * 100), 100)
            }
        ]

        # ----------------------------------------------------
        # ALERTS
        # ----------------------------------------------------
        alerts = []

        if wave_height > 2:

            alerts.append({
                "type": "ALERT",

                "message":
                    f"High wave activity detected near {coords['name']}",

                "time": "Immediate"
            })

        if current_velocity > 1.5:

            alerts.append({
                "type": "WARNING",

                "message":
                    f"Strong ocean current near {coords['name']}",

                "time": "Next 24 hrs"
            })

        if wind_speed > 20:

            alerts.append({
                "type": "ALERT",

                "message":
                    f"Strong marine winds near {coords['name']}",

                "time": "Immediate"
            })

        if sea_level > 0.5:

            alerts.append({
                "type": "NOTICE",

                "message":
                    f"Elevated sea level near {coords['name']}",

                "time": "Monitoring"
            })

        # If there are no alerts
        if not alerts:

            alerts.append({
                "type": "NOTICE",

                "message":
                    f"Marine conditions near {coords['name']} are stable",

                "time": "Live"
            })

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------
        return {

            "status": "success",

            "location": location,

            "locationName": coords["name"],

            "coordinates": {
                "lat": coords["lat"],
                "lon": coords["lon"]
            },

            "riskScore": risk_score,

            "riskLevel": risk_level,

            "criticalZones": critical_zones,

            "trend": trend,

            "factors": factors,

            "alerts": alerts,

            "liveData": {

                "temperature": temperature,

                "waveHeight": wave_height,

                "windSpeed": wind_speed,

                "seaLevel": sea_level,

                "salinity": salinity,

                "currentVelocity": current_velocity,

                "currentDirection": current_direction
            }
        }

    # --------------------------------------------------------
    # ERROR HANDLING
    # --------------------------------------------------------
    except Exception as e:

        print("Risk API Error:", e)

        return {
            "status": "error",
            "message": str(e)
        }