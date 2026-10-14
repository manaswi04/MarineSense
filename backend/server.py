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

from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import bcrypt
import jwt
from pydantic import BaseModel

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
# MONGODB CONNECTION
# ============================================================
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
JWT_SECRET = os.getenv("JWT_SECRET")

mongo_client = MongoClient(MONGODB_URI)

db = mongo_client["marinesense"]
users_collection = db["users"]

users_collection.create_index(
    "username",
    unique=True
)

    # -----------------------------
    # SIGNUP AND LOGIN
    # -----------------------------
class SignupRequest(BaseModel):
    name: str
    username: str
    profession: str
    location: str
    password: str


@app.post("/api/auth/signup")
def signup(user: SignupRequest):

    username = user.username.strip().lower()

    existing_user = users_collection.find_one({
        "username": username
    })

    if existing_user:
        return {
            "status": "error",
            "message": "Username already exists"
        }

    # -----------------------------
    # FIND SUPPORTED PORT
    # -----------------------------

    location_input = user.location.strip().lower()

    selected_port = None

    for port_key, port_data in locations.items():

        if (
            location_input == port_key
            or location_input == port_data["name"].lower()
            or port_key in location_input
        ):
            selected_port = port_key
            break

    # -----------------------------
    # DEFAULT TO MUMBAI
    # -----------------------------

    if selected_port is None:
        selected_port = "mumbai"

    port_data = locations[selected_port]

    # -----------------------------
    # HASH PASSWORD
    # -----------------------------

    password_hash = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # -----------------------------
    # SAVE USER
    # -----------------------------

    users_collection.insert_one({
        "name": user.name.strip(),
        "username": username,
        "profession": user.profession.strip(),
        "port": selected_port,
        "portName": port_data["name"],
        "passwordHash": password_hash,
        "createdAt": datetime.utcnow()
    })

    return {
        "status": "success",
        "message": "Account created successfully",
        "port": selected_port,
        "portName": port_data["name"]
    }


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/api/auth/login")
def login(user: LoginRequest):

    username = user.username.strip().lower()

    db_user = users_collection.find_one({
        "username": username
    })

    if not db_user:
        return {
            "status": "error",
            "message": "Invalid username or password"
        }

    password_valid = bcrypt.checkpw(
        user.password.encode("utf-8"),
        db_user["passwordHash"].encode("utf-8")
    )

    if not password_valid:
        return {
            "status": "error",
            "message": "Invalid username or password"
        }

    token = jwt.encode(
        {
            "user_id": str(db_user["_id"]),
            "username": db_user["username"]
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    return {
        "status": "success",
        "token": token,
        "user": {
            "name": db_user["name"],
            "username": db_user["username"],
            "profession": db_user["profession"],
            "port": db_user["port"],
            "portName": db_user["portName"]
        }
    }
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

# Dashboard response cache: 3 minutes per port
DASHBOARD_CACHE_SECONDS = 180
_dashboard_cache = {}
_dashboard_cache_lock = threading.Lock()

# Separate pool for parallel dashboard data retrieval
_dashboard_executor = ThreadPoolExecutor(max_workers=3)

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

# Sea-level cache and failure cooldown
_sea_level_cache = {}
_sea_level_retry_after = {}
_sea_level_state_lock = threading.Lock()

# Avoid repeatedly launching slow Copernicus requests for the same port.
SEA_LEVEL_FAILURE_COOLDOWN_SECONDS = 90
SEA_LEVEL_REQUEST_TIMEOUT_SECONDS = 20


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

    # --------------------------------------------------------
    # 1. CHECK CACHE
    # --------------------------------------------------------
    if cache_key in _current_cache:
        cached_value, cached_time = _current_cache[cache_key]

        if now - cached_time < CACHE_DURATION_SECONDS:
            return cached_value

    with _get_lock("current_" + cache_key):

        # Recheck cache after acquiring lock
        now = time.time()

        if cache_key in _current_cache:
            cached_value, cached_time = _current_cache[cache_key]

            if now - cached_time < CACHE_DURATION_SECONDS:
                return cached_value

        try:
            # ------------------------------------------------
            # 2. REQUEST COPERNICUS DATA
            # ------------------------------------------------
            from datetime import datetime, timedelta

            date = (
                datetime.utcnow() - timedelta(days=1)
            ).strftime("%Y-%m-%d")

            current_ds = _run_with_timeout(
                copernicusmarine.open_dataset,
                dataset_id="cmems_mod_glo_phy-cur_anfc_0.083deg_PT6H-i",
                minimum_longitude=lon - 0.5,
                maximum_longitude=lon + 0.5,
                minimum_latitude=lat - 0.5,
                maximum_latitude=lat + 0.5,
                start_datetime=date,
                end_datetime=date,
                variables=["uo", "vo"]
            )

            # ------------------------------------------------
            # 3. VALIDATE DATASET
            # ------------------------------------------------
            if (
                current_ds is None
                or "uo" not in current_ds
                or "vo" not in current_ds
            ):
                raise ValueError(
                    "Copernicus dataset is missing uo or vo"
                )

            uo_field = current_ds["uo"]
            vo_field = current_ds["vo"]

            # Select a time step
            if "time" in uo_field.dims:
                if uo_field.sizes["time"] == 0:
                    raise ValueError("No ocean-current time values")
                uo_field = uo_field.isel(time=0)

            if "time" in vo_field.dims:
                if vo_field.sizes["time"] == 0:
                    raise ValueError("No ocean-current time values")
                vo_field = vo_field.isel(time=0)

            # Select surface depth
            if "depth" in uo_field.dims:
                uo_field = uo_field.isel(depth=0)

            if "depth" in vo_field.dims:
                vo_field = vo_field.isel(depth=0)

            # ------------------------------------------------
            # 4. READ NEAREST GRID CELL
            # ------------------------------------------------
            try:
                uo_value = safe_float(
                    uo_field.sel(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values.flat[0],
                    float("nan")
                )

                vo_value = safe_float(
                    vo_field.sel(
                        latitude=lat,
                        longitude=lon,
                        method="nearest"
                    ).values.flat[0],
                    float("nan")
                )

            except Exception as lookup_error:
                print("Current grid lookup failed:", lookup_error)
                uo_value = float("nan")
                vo_value = float("nan")

            # ------------------------------------------------
            # 5. SEARCH NEARBY CELLS IF DATA IS MISSING
            # ------------------------------------------------
            # Zero current can be valid. Search nearby cells
            # only when the nearest cell contains missing data.
            if (
                not math.isfinite(uo_value)
                or not math.isfinite(vo_value)
            ):
                try:
                    lats = uo_field["latitude"].values
                    lons = uo_field["longitude"].values
                    uo_values = uo_field.values
                    vo_values = vo_field.values

                    best = None

                    for i, grid_lat in enumerate(lats):
                        for j, grid_lon in enumerate(lons):

                            u = safe_float(
                                uo_values[i, j],
                                float("nan")
                            )
                            v = safe_float(
                                vo_values[i, j],
                                float("nan")
                            )

                            if (
                                not math.isfinite(u)
                                or not math.isfinite(v)
                            ):
                                continue

                            distance = (
                                (float(grid_lat) - lat) ** 2
                                + (float(grid_lon) - lon) ** 2
                            )

                            if best is None or distance < best[0]:
                                best = (
                                    distance,
                                    u,
                                    v,
                                    float(grid_lat),
                                    float(grid_lon)
                                )

                    if best is None:
                        raise ValueError(
                            "No valid ocean-current grid cells found"
                        )

                    uo_value = best[1]
                    vo_value = best[2]

                    print(
                        "Ocean current fallback grid:",
                        best[3],
                        best[4]
                    )

                except Exception as fallback_error:
                    print("Current fallback search failed:", fallback_error)
                    return None

            # ------------------------------------------------
            # 6. NEVER CONVERT MISSING DATA TO ZERO
            # ------------------------------------------------
            if (
                not math.isfinite(uo_value)
                or not math.isfinite(vo_value)
            ):
                print(
                    "Ocean current unavailable:",
                    lat,
                    lon
                )
                return None

            # ------------------------------------------------
            # 7. CALCULATE SPEED AND DIRECTION
            # ------------------------------------------------
            velocity = math.sqrt(
                uo_value ** 2 + vo_value ** 2
            )

            direction = (
                math.degrees(
                    math.atan2(uo_value, vo_value)
                ) + 360
            ) % 360

            result = {
                "velocity": round(velocity, 3),
                "direction": round(direction, 1),
                "uo": round(uo_value, 4),
                "vo": round(vo_value, 4)
            }

            print(
                "Ocean current:",
                lat,
                lon,
                result
            )

            # Cache only valid measurements
            _current_cache[cache_key] = (
                result,
                time.time()
            )

            return result

        except Exception as e:
            print(
                "Current Error:",
                lat,
                lon,
                str(e)
            )

            # Use a previous cached measurement if available
            if cache_key in _current_cache:
                cached_value, cached_time = _current_cache[cache_key]

                if cached_value is not None:
                    print("Using previously cached current:", cached_value)
                    return cached_value

            return None
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
# COPERNICUS SEA LEVEL — CACHED AND TIMEOUT-SAFE
# ============================================================

def get_copernicus_sea_level(lat, lon):
    from datetime import datetime, timedelta

    lat = round(float(lat), 2)
    lon = round(float(lon), 2)
    cache_key = f"{lat},{lon}"
    now = time.time()

    # --------------------------------------------------------
    # 1. CHECK CACHE AND FAILURE COOLDOWN
    # --------------------------------------------------------
    with _sea_level_state_lock:
        cached = _sea_level_cache.get(cache_key)

        if cached is not None:
            cached_value, cached_time = cached

            if now - cached_time < CACHE_DURATION_SECONDS:
                return cached_value

        retry_after = _sea_level_retry_after.get(cache_key, 0)

        if now < retry_after:
            # Do not repeatedly hit Copernicus during an outage.
            # Return a previous valid measurement if available.
            if cached is not None:
                print(
                    "Sea level: using stale cached measurement",
                    cache_key,
                )
                return cached[0]

            print("Sea level: request cooldown active", cache_key)
            return None

    # One lock per sea-level location prevents simultaneous calls
    # for the same coordinates.
    with _get_lock("sea_level_" + cache_key):

        now = time.time()

        with _sea_level_state_lock:
            cached = _sea_level_cache.get(cache_key)

            if cached is not None:
                cached_value, cached_time = cached

                if now - cached_time < CACHE_DURATION_SECONDS:
                    return cached_value

            retry_after = _sea_level_retry_after.get(cache_key, 0)

            if now < retry_after:
                if cached is not None:
                    return cached[0]
                return None

        try:
            # ------------------------------------------------
            # 2. REQUEST A RECENT DAILY DATASET
            # ------------------------------------------------
            date = (
                datetime.utcnow() - timedelta(days=1)
            ).strftime("%Y-%m-%d")

            # Smaller bounding box reduces unnecessary data transfer.
            dataset = _run_with_timeout(
                copernicusmarine.open_dataset,
                dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
                minimum_longitude=lon - 0.15,
                maximum_longitude=lon + 0.15,
                minimum_latitude=lat - 0.15,
                maximum_latitude=lat + 0.15,
                start_datetime=date,
                end_datetime=date,
                variables=["zos"],
                timeout=SEA_LEVEL_REQUEST_TIMEOUT_SECONDS,
            )

            if dataset is None or "zos" not in dataset:
                raise ValueError("Copernicus dataset has no 'zos' variable")

            field = dataset["zos"]

            # ------------------------------------------------
            # 3. SELECT THE FIRST AVAILABLE TIME/DEPTH
            # ------------------------------------------------
            for dim in ("time", "depth"):
                if dim in field.dims:
                    if field.sizes.get(dim, 0) == 0:
                        raise ValueError(f"Dataset has no {dim} values")
                    field = field.isel({dim: 0})

            # ------------------------------------------------
            # 4. FIND THE NEAREST GRID CELL
            # ------------------------------------------------
            value = float("nan")

            try:
                nearest = field.sel(
                    latitude=lat,
                    longitude=lon,
                    method="nearest",
                )

                raw = nearest.values
                if getattr(raw, "size", 0) > 0:
                    candidate = float(raw.flat[0])
                    if math.isfinite(candidate):
                        value = candidate

            except Exception as lookup_error:
                print("Sea-level nearest lookup:", repr(lookup_error))

            # ------------------------------------------------
            # 5. FALL BACK TO THE NEAREST VALID CELL
            # ------------------------------------------------
            # Zero is a valid possible sea-level anomaly.
            if not math.isfinite(value):
                try:
                    import numpy as np

                    grid = field
                    grid_values = np.asarray(grid.values, dtype=float)

                    # Support any remaining singleton dimensions.
                    grid_values = np.squeeze(grid_values)

                    if grid_values.ndim != 2:
                        raise ValueError(
                            "Expected a 2D latitude/longitude grid; "
                            f"received shape {grid_values.shape}"
                        )

                    lats = np.asarray(
                        grid["latitude"].values, dtype=float
                    )
                    lons = np.asarray(
                        grid["longitude"].values, dtype=float
                    )

                    # Handle descending coordinates and either
                    # one-dimensional or two-dimensional coordinates.
                    if lats.ndim == 1 and lons.ndim == 1:
                        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
                    else:
                        lat_grid, lon_grid = lats, lons

                    valid = np.isfinite(grid_values)

                    # Only search cells in the requested small region.
                    nearby = (
                        (np.abs(lat_grid - lat) <= 0.15)
                        & (np.abs(lon_grid - lon) <= 0.15)
                        & valid
                    )

                    if not np.any(nearby):
                        raise ValueError(
                            "No valid sea-level cells near selected port"
                        )

                    # Approximate geographic distance; scale longitude
                    # by latitude so the nearest cell is more meaningful.
                    distance = (
                        (lat_grid - lat) ** 2
                        + (
                            (lon_grid - lon)
                            * math.cos(math.radians(lat))
                        ) ** 2
                    )

                    distance = np.where(nearby, distance, np.inf)
                    nearest_index = np.unravel_index(
                        np.argmin(distance), distance.shape
                    )

                    value = float(grid_values[nearest_index])

                    print(
                        "Sea-level fallback grid:",
                        float(lat_grid[nearest_index]),
                        float(lon_grid[nearest_index]),
                    )

                except Exception as fallback_error:
                    print(
                        "Sea-level fallback failed:",
                        repr(fallback_error),
                    )
                    value = float("nan")

            # ------------------------------------------------
            # 6. VALIDATE AND CACHE ONLY REAL MEASUREMENTS
            # ------------------------------------------------
            if not math.isfinite(value):
                raise ValueError("No finite sea-level measurement found")

            value = round(value, 3)

            with _sea_level_state_lock:
                _sea_level_cache[cache_key] = (value, time.time())
                _sea_level_retry_after.pop(cache_key, None)

            print("Sea level:", lat, lon, value, "m")
            return value

        except Exception as error:
            print("Sea Level Error:", lat, lon, repr(error))

            with _sea_level_state_lock:
                _sea_level_retry_after[cache_key] = (
                    time.time() + SEA_LEVEL_FAILURE_COOLDOWN_SECONDS
                )

                cached = _sea_level_cache.get(cache_key)

            # A stale valid reading is better than a fabricated zero,
            # but the frontend should ideally label it as stale.
            if cached is not None:
                print("Sea level: returning previous valid value", cache_key)
                return cached[0]

            return None
        
# ========================================================
# 4. COPERNICUS (run in parallel instead of sequentially)
# ========================================================
    sea_level_future = _dashboard_executor.submit(
        get_copernicus_sea_level,
        coords["lat"],
        coords["lon"]
    )

    salinity_future = _dashboard_executor.submit(
        get_copernicus_salinity,
        coords["lat"],
        coords["lon"]
    )

    current_future = _dashboard_executor.submit(
        get_copernicus_current,
        coords["lat"],
        coords["lon"]
    )

    # Each getter should return its existing fallback if its
    # upstream request fails. The timeout prevents this endpoint
    # from waiting indefinitely for a result.
    try:
        sea_level = safe_float(
            sea_level_future.result(timeout=35),
            0.0
        )
    except Exception as exc:
        print("Dashboard sea-level timeout/error:", exc)
        sea_level = 0.0

    try:
        salinity = safe_float(
            salinity_future.result(timeout=35),
            35.0
        )
    except Exception as exc:
        print("Dashboard salinity timeout/error:", exc)
        salinity = 35.0

    try:
        current = current_future.result(timeout=35)
        current = current if isinstance(current, dict) else {}
    except Exception as exc:
        print("Dashboard current timeout/error:", exc)
        current = {
            "velocity": 0.0,
            "direction": 0.0,
            "uo": 0.0,
            "vo": 0.0
        }

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
def ocean_data(location: str = "mumbai"):

    global active_location

    # --------------------------------------------------------
    # 1. VALIDATE SELECTED PORT
    # --------------------------------------------------------
    location = (location or "mumbai").lower().strip()

    if location not in locations:
        location = "mumbai"

    active_location = location
    coords = locations[location]

    now = time.time()

    # --------------------------------------------------------
    # 2. CHECK DASHBOARD CACHE
    # --------------------------------------------------------
    with _dashboard_cache_lock:
        cached = _dashboard_cache.get(location)

        if cached and now - cached["time"] < DASHBOARD_CACHE_SECONDS:
            print("Using dashboard cache:", location)
            return cached["response"]

    print("================================")
    print("Selected Port:", coords["name"])
    print("Latitude:", coords["lat"])
    print("Longitude:", coords["lon"])

    # --------------------------------------------------------
    # 3. MARINE AND WEATHER DATA
    # --------------------------------------------------------
    sea = get_sea_data(coords["lat"], coords["lon"])

    temperature = sea.get("temperature")
    wave_height = sea.get("wave_height")
    wind_speed = sea.get("wind_speed")

    # --------------------------------------------------------
    # 4. COPERNICUS SEA LEVEL
    # --------------------------------------------------------
    sea_level = get_copernicus_sea_level(
        coords["lat"],
        coords["lon"]
    )

    # --------------------------------------------------------
    # 5. COPERNICUS SALINITY
    # --------------------------------------------------------
    salinity = get_copernicus_salinity(
        coords["lat"],
        coords["lon"]
    )

    # --------------------------------------------------------
    # 6. COPERNICUS OCEAN CURRENT
    # --------------------------------------------------------
    current = get_copernicus_current(
        coords["lat"],
        coords["lon"]
    )

    current_velocity = (
        current.get("velocity")
        if current is not None
        else None
    )

    current_direction = (
        current.get("direction")
        if current is not None
        else None
    )

    # --------------------------------------------------------
    # 7. RISK CALCULATION
    # --------------------------------------------------------
    # Use zero only internally when current is unavailable.
    # Keep the API measurement itself as None.
    risk_current = (
        current_velocity
        if current_velocity is not None
        else 0.0
    )

    risk_temperature = (
        temperature if temperature is not None else 28.0
    )

    risk_score = calculate_risk(
        risk_temperature,
        risk_current
    )

    if risk_score < 30:
        risk_level = "Low"
    elif risk_score < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # --------------------------------------------------------
    # 8. BUILD RESPONSE
    # --------------------------------------------------------
    response = {
        "status": "success",
        "location": location,
        "locationName": coords["name"],
        "coordinates": {
            "lat": coords["lat"],
            "lon": coords["lon"]
        },
        "temperature": temperature,
        "waveHeight": wave_height,
        "windSpeed": wind_speed,
        "seaLevel": sea_level,
        "salinity": salinity,
        "currentVelocity": current_velocity,
        "currentDirection": current_direction,
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "history": sea.get("history", [])
    }

    # --------------------------------------------------------
    # 9. CACHE RESPONSE BY PORT
    # --------------------------------------------------------
    with _dashboard_cache_lock:
        _dashboard_cache[location] = {
            "time": time.time(),
            "response": response
        }

    print("Ocean data response:", location)
    print("Sea level:", sea_level)
    print("Current velocity:", current_velocity)
    print("Current direction:", current_direction)

    return response

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


    
    with _dashboard_cache_lock:
        _dashboard_cache[location] = {
        "time": time.time(),
        "response": response
    }

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

        active_location = location
        coords = locations[location]

        print("======================================")
        print("ADVISORY PORT:", location)
        print("ADVISORY COORDINATES:", coords["lat"], coords["lon"])

        # ----------------------------------------------------
        # HELPER: PRESERVE UNAVAILABLE VALUES AS NONE
        # ----------------------------------------------------
        def advisory_number(value):
            if value is None:
                return None

            try:
                number = float(value)
                if not math.isfinite(number):
                    return None
                return number
            except (TypeError, ValueError):
                return None

        # ----------------------------------------------------
        # MARINE DATA
        # ----------------------------------------------------
        sea = get_sea_data(coords["lat"], coords["lon"]) or {}

        temperature = advisory_number(sea.get("temperature"))
        wave_height = advisory_number(sea.get("wave_height"))

        # ----------------------------------------------------
        # SEA LEVEL
        # ----------------------------------------------------
        sea_level = advisory_number(
            get_copernicus_sea_level(coords["lat"], coords["lon"])
        )

        # ----------------------------------------------------
        # SALINITY
        # ----------------------------------------------------
        salinity = advisory_number(
            get_copernicus_salinity(coords["lat"], coords["lon"])
        )

        # ----------------------------------------------------
        # OCEAN CURRENT
        # ----------------------------------------------------
        current = get_copernicus_current(
            coords["lat"], coords["lon"]
        )

        current_velocity = None
        current_direction = None

        if isinstance(current, dict):
            current_velocity = advisory_number(current.get("velocity"))
            current_direction = advisory_number(current.get("direction"))

        # ----------------------------------------------------
        # RISK SCORE
        # Do not calculate a score using invented fallback values.
        # ----------------------------------------------------
        if temperature is not None and current_velocity is not None:
            risk_score = calculate_risk(temperature, current_velocity)
        else:
            risk_score = None

        # ----------------------------------------------------
        # ADVISORIES
        # ----------------------------------------------------
        advisories = []

        if wave_height is not None and wave_height > 2:
            advisories.append({
                "type": "Navigation Warning",
                "severity": "High",
                "title": "High Wave Activity",
                "message": (
                    f"Wave turbulence near {coords['name']} "
                    "may affect vessel movement."
                ),
                "recommendation": (
                    "Restrict small vessel movement and "
                    "increase coastal monitoring."
                )
            })

        if current_velocity is not None and current_velocity > 1.5:
            advisories.append({
                "type": "Marine Navigation Alert",
                "severity": "Critical",
                "title": "Strong Ocean Current",
                "message": (
                    f"Ocean current velocity is above the safe "
                    f"navigation threshold near {coords['name']}."
                ),
                "recommendation": (
                    "Increase vessel monitoring and coastal "
                    "current observation."
                )
            })

        if sea_level is not None and sea_level > 0.5:
            advisories.append({
                "type": "Coastal Alert",
                "severity": "Medium",
                "title": "Elevated Sea Level",
                "message": f"Elevated sea level detected near {coords['name']}.",
                "recommendation": (
                    "Monitor coastal erosion and tidal impacts."
                )
            })

        if temperature is not None and temperature > 29:
            advisories.append({
                "type": "Thermal Stress",
                "severity": "Medium",
                "title": "Elevated Sea Temperature",
                "message": (
                    f"Surface water temperature near {coords['name']} "
                    "is elevated."
                ),
                "recommendation": "Track marine habitat fluctuations."
            })

        # ----------------------------------------------------
        # DATA QUALITY NOTICE
        # ----------------------------------------------------
        unavailable = []

        if temperature is None:
            unavailable.append("sea temperature")
        if wave_height is None:
            unavailable.append("wave height")
        if sea_level is None:
            unavailable.append("sea level")
        if salinity is None:
            unavailable.append("salinity")
        if current_velocity is None:
            unavailable.append("ocean current")

        if unavailable:
            advisories.append({
                "type": "Data Quality Notice",
                "severity": "Medium",
                "title": "Some Marine Data Unavailable",
                "message": (
                    "The following measurements could not be verified: "
                    + ", ".join(unavailable)
                    + ". Risk assessment may be incomplete."
                ),
                "recommendation": (
                    "Retry data retrieval and verify the missing "
                    "measurements before making operational decisions."
                )
            })

        # Only report stable conditions when the measurements used
        # for the advisory checks are available.
        if not advisories:
            advisories.append({
                "type": "Marine Status",
                "severity": "Low",
                "title": "No Threshold-Based Warnings Detected",
                "message": (
                    f"No configured warning thresholds were exceeded "
                    f"by the available measurements near {coords['name']}."
                ),
                "recommendation": "Continue routine marine monitoring."
            })

        # ----------------------------------------------------
        # RESPONSE
        # Keep the existing field names for frontend compatibility.
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
            "dataComplete": len(unavailable) == 0,
            "missingData": unavailable,
            "advisories": advisories
        }

    except Exception as e:
        print("Advisory API Error:", repr(e))
        return {
            "status": "error",
            "message": str(e)
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

    print("RISK REQUEST LOCATION:", repr(location))

    try:
        global active_location

        # ----------------------------------------------------
        # 1. SELECT LOCATION
        # ----------------------------------------------------
        location = (location or "mumbai").lower().strip()

        if location not in locations:
            print(
                f"Invalid risk location '{location}', "
                "defaulting to Mumbai"
            )
            location = "mumbai"

        coords = locations[location]
        active_location = location

        print("======================================")
        print("RISK PORT:", location)
        print("RISK COORDINATES:", coords["lat"], coords["lon"])

        # ----------------------------------------------------
        # 2. MARINE DATA
        # ----------------------------------------------------
        sea = get_sea_data(coords["lat"], coords["lon"])

        temperature = safe_float(
            sea.get("temperature"), 28.0
        )

        wave_height = safe_float(
            sea.get("wave_height"), 1.0
        )

        wind_speed = safe_float(
            sea.get("wind_speed"), 10.0
        )

        # ----------------------------------------------------
        # 3. SEA LEVEL
        # ----------------------------------------------------
        sea_level = get_copernicus_sea_level(
            coords["lat"],
            coords["lon"]
        )

        # ----------------------------------------------------
        # 4. SALINITY
        # ----------------------------------------------------
        salinity = get_copernicus_salinity(
            coords["lat"],
            coords["lon"]
        )

        # ----------------------------------------------------
        # 5. OCEAN CURRENT
        # ----------------------------------------------------
        current = get_copernicus_current(
            coords["lat"],
            coords["lon"]
        )

        current_velocity = (
            current.get("velocity")
            if current is not None
            else None
        )

        current_direction = (
            current.get("direction")
            if current is not None
            else None
        )

        # ----------------------------------------------------
        # 6. RISK SCORE
        # ----------------------------------------------------
        # Missing current data must not be reported as zero.
        # Calculate a provisional score from available inputs
        # and explicitly flag incomplete measurements.
        risk_data_complete = current_velocity is not None

        risk_current = (
            current_velocity
            if current_velocity is not None
            else 0.0
        )

        risk_score = calculate_risk(
            temperature,
            risk_current
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
        # 7. CRITICAL ZONES
        # ----------------------------------------------------
        critical_zones = 0

        if wave_height > 2:
            critical_zones += 1

        if (
            current_velocity is not None
            and current_velocity > 1.5
        ):
            critical_zones += 1

        if sea_level is not None and sea_level > 0.5:
            critical_zones += 1

        if wind_speed > 20:
            critical_zones += 1

        # ----------------------------------------------------
        # 8. RISK FACTORS
        # ----------------------------------------------------
        factors = [
            {
                "title": "Temperature Anomalies",
                "description": (
                    f"Current marine temperature is "
                    f"{temperature:.2f}°C"
                ),
                "severity": (
                    "High" if temperature > 29 else "Medium"
                ),
                "score": min(
                    max(int((temperature / 35) * 100), 0),
                    100
                )
            },
            {
                "title": "Wave Turbulence",
                "description": f"Wave height {wave_height:.2f} m",
                "severity": (
                    "Critical" if wave_height > 2 else "Low"
                ),
                "score": min(
                    max(int(wave_height * 40), 0),
                    100
                )
            },
            {
                "title": "Wind Instability",
                "description": f"Wind speed {wind_speed:.2f} km/h",
                "severity": (
                    "High" if wind_speed > 20 else "Medium"
                ),
                "score": min(
                    max(int(wind_speed * 4), 0),
                    100
                )
            },
            {
                "title": "Ocean Current Velocity",
                "description": (
                    f"Current velocity {current_velocity:.2f} m/s"
                    if current_velocity is not None
                    else "Ocean current data unavailable"
                ),
                "severity": (
                    "Critical"
                    if current_velocity is not None
                    and current_velocity > 1.5
                    else "Low"
                    if current_velocity is not None
                    else "Unavailable"
                ),
                "score": (
                    min(int(current_velocity / 1.5 * 100), 100)
                    if current_velocity is not None
                    else None
                )
            },
            {
                "title": "Sea Level Rise",
                "description": (
                    f"Sea level {sea_level:.3f} m"
                    if sea_level is not None
                    else "Sea-level data unavailable"
                ),
                "severity": (
                    "High"
                    if sea_level is not None and sea_level > 0.5
                    else "Low"
                    if sea_level is not None
                    else "Unavailable"
                ),
                "score": (
                    min(max(int(sea_level * 100), 0), 100)
                    if sea_level is not None
                    else None
                )
            }
        ]

        # ----------------------------------------------------
        # 9. ALERTS
        # ----------------------------------------------------
        alerts = []

        if wave_height > 2:
            alerts.append({
                "type": "ALERT",
                "message": (
                    f"High wave activity detected near "
                    f"{coords['name']}"
                ),
                "time": "Immediate"
            })

        if (
            current_velocity is not None
            and current_velocity > 1.5
        ):
            alerts.append({
                "type": "WARNING",
                "message": (
                    f"Strong ocean current near {coords['name']}"
                ),
                "time": "Next 24 hrs"
            })

        if wind_speed > 20:
            alerts.append({
                "type": "ALERT",
                "message": (
                    f"Strong marine winds near {coords['name']}"
                ),
                "time": "Immediate"
            })

        if sea_level is not None and sea_level > 0.5:
            alerts.append({
                "type": "NOTICE",
                "message": (
                    f"Elevated sea level near {coords['name']}"
                ),
                "time": "Monitoring"
            })

        if current_velocity is None or sea_level is None:
            alerts.append({
                "type": "DATA NOTICE",
                "message": (
                    "Some ocean measurements are unavailable. "
                    "Risk assessment may be incomplete."
                ),
                "time": "Data unavailable"
            })

        if not alerts:
            alerts.append({
                "type": "NOTICE",
                "message": (
                    f"Marine conditions near {coords['name']} "
                    "show no threshold-based alerts."
                ),
                "time": "Latest available data"
            })

        # ----------------------------------------------------
        # 10. RESPONSE
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
            "riskDataComplete": risk_data_complete,
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

    except Exception as e:
        print("Risk API Error:", repr(e))

        return {
            "status": "error",
            "message": str(e)
        }
