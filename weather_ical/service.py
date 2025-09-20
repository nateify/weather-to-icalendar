from datetime import UTC, datetime, timedelta, timezone
from typing import Any

from requests_cache import NEVER_EXPIRE, CachedSession

from const import AQI_MAP, FORECAST_DAYS, UVI_MAP, WMO_MAP, WIND_DIR_MAP
from process_weather import process_weather_data

from weather_ical.data.client import SimpleHTTPError, WeatherClient
from weather_ical.data.formatting import format_hours_minutes, format_float, clean_description, validate_zip


def get_location_from_zip(zip_code: str) -> tuple[float, float, str]:
    geocoding_session = CachedSession(
        "geocoding_cache",
        expire_after=NEVER_EXPIRE,
        stale_if_error=True,
    )

    # Get location data from ZIP code
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": zip_code,
        "count": 1,
        "countryCode": "US",
    }

    resp = geocoding_session.get(url, params=params)
    resp.raise_for_status()
    location = resp.json()["results"][0]

    print(f"Location data cache hit: {resp.from_cache}")

    location_name = f"{location['name']}, {location['admin1']}" if location.get("admin1") else location["name"]

    return location["latitude"], location["longitude"], location_name


def generate_weather_data(zip_code: str, metric: bool, show_location: bool) -> dict[str, Any]:
    if metric:
        temp_unit = "celsius"
        precip_unit = "mm"
        wind_speed_unit = "ms"
    else:
        temp_unit = "fahrenheit"
        precip_unit = "inch"
        wind_speed_unit = "mph"

    zip_code_validated = validate_zip(zip_code)

    if not zip_code_validated:
        raise SimpleHTTPError(400, "Invalid ZIP code")

    lat, lon, location_string = get_location_from_zip(zip_code_validated)
    location_geo = (lat, lon) if show_location else None

    print(f"Got coordinates ({lat}, {lon}) from {zip_code_validated}")

    client = WeatherClient()

    aqi_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "us_aqi",
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
        "domains": "cams_global",
        "past_hours": 0,
    }
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "precipitation_probability",
            "rain",
            "showers",
            "snowfall",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
            "uv_index",
            "uv_index_clear_sky",
            "weather_code",
        ],
        "minutely_15": "precipitation",
        "timezone": "auto",
        "forecast_days": FORECAST_DAYS,
        "wind_speed_unit": wind_speed_unit,
        "temperature_unit": temp_unit,
        "precipitation_unit": precip_unit,
        "past_hours": 0,
        "past_minutely_15": 0,
    }
    weather_responses, weather_cache_metadata = client.get_weather(
        "https://api.open-meteo.com/v1/forecast", weather_params
    )
    aqi_responses, aqi_cache_metadata = client.get_weather(
        "https://air-quality-api.open-meteo.com/v1/air-quality", aqi_params
    )

    weather_response = weather_responses[0]
    aqi_response = aqi_responses[0]
    tz_abbreviation = weather_response.TimezoneAbbreviation().decode("utf-8")

    print(f"Forecast data cache hit: {weather_cache_metadata.get('from_cache', False)}")
    print(f"Air quality data cache hit: {aqi_cache_metadata.get('from_cache', False)}")

    # Forecast local timezone
    forecast_timezone = timezone(timedelta(seconds=weather_response.UtcOffsetSeconds()))

    # created_at is None when cache is first initialized
    if not weather_cache_metadata.get("created_at"):
        forecast_cache_last_updated = datetime.now(UTC)
    else:
        forecast_cache_last_updated = weather_cache_metadata["created_at"].replace(tzinfo=UTC)

    weather_data_dict = {
        "LastUpdated": forecast_cache_last_updated,
        "ForecastEntries": [],
        "LocationString": location_string,
        "LocationGeo": location_geo,
    }

    forecast_cache_last_updated = forecast_cache_last_updated.astimezone(forecast_timezone)

    forecast_data = process_weather_data(aqi_response, weather_response, weather_params, FORECAST_DAYS)

    # Formatting
    temp_unit = temp_unit[:1].upper()
    precip_unit = precip_unit[:2]
    if wind_speed_unit == "ms":
        wind_speed_unit = "m/s"
    precip_cutoff = 0.01 if precip_unit == "in" else 0.25

    for fc in forecast_data.iter_rows(named=True):
        temp_max = fc["temperature_max"]
        temp_min = fc["temperature_min"]
        adj_temp_max = fc["apparent_temperature_max"]
        adj_temp_min = fc["apparent_temperature_min"]
        wmo = WMO_MAP[fc["wmo"]]
        aqi = fc["aqi_max"]
        uvi = fc["uv_index_max"]
        uvics = fc["uv_index_clear_sky_max"]

        summary = f"{wmo[1]} {temp_max:.0f}° | {temp_min:.0f}°, {wmo[0]}"

        precip_description = ""

        has_precip = fc["precipitation_sum"] > precip_cutoff or fc["precipitation_hours"] > 0

        if has_precip:
            precip_types = []
            if fc["rain_sum"] > 0:
                precip_types.append(("Rain", fc["rain_sum"]))
            if fc["showers_sum"] > 0:
                precip_types.append(("Showers", fc["showers_sum"]))
            if fc["snowfall_sum"] > 0:
                precip_types.append(("Snow", fc["snowfall_sum"]))

            if not precip_types:
                precip_types = [("Precipitation", 0)]

            precip_groups = {}
            for precip_type, precip_value in precip_types:
                if precip_value > 0:
                    precip_len_f = format_hours_minutes(fc["precipitation_hours"])
                    chance = fc["precipitation_probability_max"]

                    key = (precip_len_f, chance)

                    if key not in precip_groups:
                        precip_groups[key] = (precip_type, precip_value)
                    else:
                        _, existing_value = precip_groups[key]
                        # Keep higher amount, or rain if equal
                        if precip_value > existing_value or (precip_value == existing_value and precip_type == "Rain"):
                            precip_groups[key] = (precip_type, precip_value)

            precip_parts = []
            for (precip_len_f, chance), (precip_type, precip_value) in precip_groups.items():
                precip_parts.extend(
                    [
                        f"{precip_type}: {format_float(precip_value)} {precip_unit}",
                        f"Length of {precip_type.lower()}: {precip_len_f}",
                        f"Chance of {precip_type.lower()}: {chance:.0f}%",
                    ]
                )

            precip_description = "\n".join(precip_parts)

            max_amount = max((amount for _, amount in precip_types if amount > 0), default=0)
            if max_amount > 0:
                summary += f" ({format_float(max_amount)} {precip_unit})"

        elif fc["precipitation_probability_max"] > 1:
            precip_description = f"Chance of precipitation: {fc['precipitation_probability_max']:.0f}%"

        uvics_description = ""

        if uvics and uvics != uvi:
            uvics_description = f"UV index (Clear Sky): {UVI_MAP[uvics]} ({uvics})"

        wind_dir = fc["vector_avg_wind_direction_10m"]

        description = f"""\
        Temperature: {temp_min:.0f}°{temp_unit} … {temp_max:.0f}°{temp_unit}
        Feels like: {adj_temp_min:.0f}°{temp_unit} … {adj_temp_max:.0f}°{temp_unit}
        Humidity: {fc["relative_humidity_max"]:.0f}%

        Air quality: {AQI_MAP[aqi]} ({aqi})
        UV index: {UVI_MAP[uvi]} ({uvi})
        {uvics_description}

        {precip_description}
        Cloud cover: {fc["cloud_cover_mean"]:.0f}%

        Wind: {fc["wind_speed_mean"]} {wind_speed_unit} {WIND_DIR_MAP[wind_dir]} ({wind_dir}°)
        Wind gust: {fc["wind_gusts_max"]} {wind_speed_unit}

        Weather data by Open-Meteo.com, CC BY 4.0

        Updated: {datetime.strftime(forecast_cache_last_updated, "%a, %d %b %Y %I:%M%p")} {tz_abbreviation}
        """

        weather_data_dict["ForecastEntries"].append((fc["date"], summary, clean_description(description).rstrip()))

    return weather_data_dict
