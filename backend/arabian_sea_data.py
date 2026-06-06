import requests
import pandas as pd
from datetime import datetime

ERDDAP_URL = "https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.csv"

def get_arabian_sea_data():
    
    query = (
        f"{ERDDAP_URL}?"
        "analysed_sst"
        "[last]"
        "[8:1:25]"
        "[60:1:75]"
    )

    response = requests.get(query)

    if response.status_code != 200:
        return {"error": "Failed to fetch satellite data"}

    data = pd.read_csv(pd.compat.StringIO(response.text))

    avg_temp = data["analysed_sst"].mean()

    result = {
        "region": "Arabian Sea",
        "timestamp": datetime.utcnow(),
        "avg_sea_temperature": round(avg_temp,2),
        "data_points": len(data)
    }

    return result