#!/usr/bin/env python3

import requests
import math
import xml.etree.ElementTree as ET
from datetime import datetime
from pyproj import Transformer

# Define the API endpoint and any necessary parameters
api_o3 = "https://data.public.lu/fr/datasets/r/c50542d0-ce59-4565-a8cb-48544ac18576"
api_no2 = "https://data.public.lu/fr/datasets/r/5ce7c6fe-fc4c-4b5e-84c9-8d97b6a21c81"
api_gml = "https://data.public.lu/fr/datasets/r/93c90cb8-4994-4be7-bcaa-cabe0e66ad9a"


def get_home_location(hass):
    latitude = hass.config.latitude
    longitude = hass.config.longitude
    return latitude, longitude


def get_address_from_gps(latitude, longitude):
    url = f"https://api.geoportail.lu/geocode/reverse?lat={latitude}&lon={longitude}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None


def get_gps_from_address(params):
    url = f"https://api.geoportail.lu/geocode/search"
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            first_result = data["results"][0]
            # Extract the coordinates from the 'geomlonlat' field
            if (
                "geomlonlat" in first_result
                and "coordinates" in first_result["geomlonlat"]
            ):
                coordinates = first_result["geomlonlat"]["coordinates"]
                lon, lat = coordinates[0], coordinates[1]
                return lat, lon
            else:
                print("'geomlonlat' data is missing in the result.")
                return None
        else:
            print("No results found for the given address.")
            return None
    else:
        print(f"API request failed with status code: {response.status_code}")
        return None


def convert_gmtp1_to_local_time(date_str, time_str):
    # Combine date, time, and the GMT+1 offset into a single string
    dt_str = f"{date_str} {time_str} +0100"
    # Define the format of the input date and time, including the timezone offset
    dt_format = "%d.%m.%Y %H:%M %z"
    # Parse the date and time string into a timezone-aware datetime object
    dt = datetime.strptime(dt_str, dt_format)
    # Convert to the local time of the OS
    local_time = dt.astimezone().strftime("%d.%m.%Y %H:%M")
    # Split the local time into date and time components
    local_date, local_time = local_time.split(" ")
    return local_date, local_time


def calculate_distance(x1, y1, x2, y2):
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def fetch_json_data(api_url):
    try:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()  # Parse the JSON data
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred in fetch_data: {http_err}")
        return False
    except Exception as err:
        print(f"An error occurred in fetch_data: {err}")
        return False
    return data


def fetch_gml_data(api_url):
    try:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        response.encoding = "utf-8"  # Ensure the response is interpreted as UTF-8
        data = response.text.replace("Â°C", "°C")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred in fetch_data: {http_err}")
        return False
    except Exception as err:
        print(f"An error occurred in fetch_data: {err}")
        return False
    return data


def extract_json_data(data, x, y):
    if not data:
        return False
    result = {}
    try:
        # Extract the "date" and "hour" fields
        date = data["date"]
        hour = data["hour"]

        # Initialize variables to store the closest gc_id and its details
        gc_id = None
        value = None
        index = None
        min_distance = float("inf")

        # Loop through the grid to find the closest value to our coordinates
        for item in data["grid"]:
            _gc_id = item["gc_id"]
            _x, _y = map(int, _gc_id.replace("X-", "").replace("Y-", "").split(":"))
            # Calculate the distance from the target coordinates
            distance = calculate_distance(_x, _y, x, y)
            # Check if this is the closest gc_id so far
            if distance < min_distance:
                min_distance = distance
                gc_id = _gc_id
                value = item["value"]
                index = item["index"]

        result = {
            "date": date,
            "hour": hour,
            "gc_id": gc_id,
            "value": value,
            "index": index,
        }
    except Exception as err:
        print(f"An error occurred in extract_data: {err}")
        return False
    return result


def get_value_by_name(name, data_array):
    """
    Returns the value associated with a given name from a list of dictionaries.

    Parameters:
    - name (str): The name to search for.
    - data_array (list): A list of dictionaries containing 'name', 'code', and 'value'.

    Returns:
    - str: The value associated with the given name, or None if not found.
    """
    for item in data_array:
        if item["name"] == name:
            return item["value"]
    return None


def extract_gml_data(data, x, y):
    root = ET.fromstring(data)
    # Define namespaces to handle the GML tags
    namespaces = {
        "gml": "http://www.opengis.net/gml/3.2",
        "om": "http://www.opengis.net/om/2.0",
        "omso": "http://inspire.ec.europa.eu/schemas/omso/3.0",
        "swe": "http://www.opengis.net/swe/1.0/gml32",
    }

    # Extract and print information
    points = root.findall(".//gml:Point", namespaces)
    min_distance = float("inf")
    result = {}
    for point in points:
        pos = point.find("gml:pos", namespaces)
        if pos is not None:
            coordinates = pos.text.strip().split()
            _y = float(coordinates[0])
            _x = float(coordinates[1])
            alt = float(coordinates[2]) if len(coordinates) > 2 else None
            distance = calculate_distance(_x, _y, x, y)
            # Check if this is the closest point so far
            if distance < min_distance:
                min_distance = distance
                nearest_point = pos.text.strip()
                result = {
                    "station_x": _x,
                    "station_y": _y,
                    "station_alt": alt,
                }
    # Find the specific Point
    for feature_member in root.findall(".//gml:featureMember", namespaces):
        point = feature_member.find(".//gml:Point/gml:pos", namespaces)

        if point is not None and point.text.strip() == nearest_point:
            # Retrieve the associated observation using the correct namespace
            observation = feature_member.find(
                f".//{{{namespaces['omso']}}}PointTimeSeriesObservation"
            )
            if observation is not None:
                data_array = observation.find(".//swe:DataArray", namespaces)
                if data_array is not None:
                    # Extract field names and codes
                    fields = data_array.findall(".//swe:field", namespaces)
                    field_names = []
                    field_codes = []

                    for field in fields:
                        name = field.find("swe:name", namespaces)
                        code = field.find(".//swe:uom", namespaces)

                        # Extract the name from the 'name' attribute
                        if name is not None and "name" in name.attrib:
                            field_names.append(name.attrib["name"].strip())
                        else:
                            field_names.append("Unknown")

                        if code is not None and "code" in code.attrib:
                            field_codes.append(code.attrib["code"].strip())
                        else:
                            field_codes.append("Unknown")

                    # Extract the values
                    values_element = data_array.find(".//swe:values", namespaces)
                    if values_element is not None:
                        values = values_element.text.strip().split("\n")
                        # Process the values and pair with field names and codes
                        for value in values:
                            value_parts = value.split(";")
                            observation_data = []
                            for i in range(len(field_names)):
                                if i < len(value_parts):
                                    observation_data.append(
                                        {
                                            "name": field_names[i],
                                            "code": field_codes[i],
                                            "value": value_parts[i],
                                        }
                                    )
    transformer = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
    result["station_lon"], result["station_lat"] = transformer.transform(
        result["station_x"], result["station_y"]
    )
    local_date, local_time = convert_gmtp1_to_local_time(
        get_value_by_name("Date", observation_data),
        get_value_by_name("Hour", observation_data),
    )

    result["date"] = local_date
    result["time"] = local_time

    result["temp"] = get_value_by_name(
        "Average Air Temperature 200cm above ground", observation_data
    )
    result["hum"] = get_value_by_name(
        "Relative Air Humidity 200cm above ground", observation_data
    )
    result["t_max"] = get_value_by_name(
        "Maximum Air Temperature 200cm above ground", observation_data
    )
    result["t_min"] = get_value_by_name(
        "Minimum Air Temperature 200cm above ground", observation_data
    )
    result["precipitation"] = get_value_by_name(
        "Precipitation (incl. snow and hail)", observation_data
    )
    return result


# Get coordinates from Home Assistant instance
# latitude, longitude = get_home_location(hass)
# Example GPS coordinates (Longitude, Latitude)
latitude = 49.6602
longitude = 5.9173

# Convert GPS coordinates to LUREF and ETRS89 coordinates
luref_transformer = Transformer.from_crs("EPSG:4326", "EPSG:2169", always_xy=True)
etrs89_transformer = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
x_luref, y_luref = luref_transformer.transform(longitude, latitude)
x_etrs89, y_etrs89 = etrs89_transformer.transform(longitude, latitude)
print(
    f"Our location: Lat = {round(latitude,2)}, Lon = {round(longitude,2)}. LUREF: X = {round(x_luref)}, Y = {round(y_luref)}. LUREF: X = {round(x_etrs89)}, Y = {round(y_etrs89)}"
)


if o3 := extract_json_data(fetch_json_data(api_o3), x_luref, y_luref):
    print(f"O3: {o3}")
if no2 := extract_json_data(fetch_json_data(api_no2), x_luref, y_luref):
    print(f"NO2: {no2}")
if weather := extract_gml_data(fetch_gml_data(api_gml), x_etrs89, y_etrs89):
    print(f"Weather: {weather}")
exit(0)
params = {"zip": 8437, "locality": "", "country": "", "street": "", "num": 13}
if coordinates := get_gps_from_address(params):
    print(f"Coordinates: {coordinates}")
    address = get_address_from_gps(coordinates[0], coordinates[1])
    print(f"Address: {address}")
