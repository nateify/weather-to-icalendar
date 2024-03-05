import json
import re
from datetime import datetime, timedelta

from requests.exceptions import HTTPError
from requests_cache import CachedSession


class HTTPErrorWithContent(Exception):
    def __init__(self, status_code, content):
        self.status_code = status_code
        self.content = content


class RangeDict(dict):
    def __getitem__(self, item):
        if not isinstance(item, range):
            for key in self:
                if item in key:
                    return self[key]
            raise KeyError(item)
        else:
            return super().__getitem__(item)


def clean_description(s):
    lines = [line.lstrip() for line in s.splitlines()]
    # Collapse multiple blank lines, catches when precipitation description is a blank string
    cleaned_lines = []
    for line in lines:
        if line == "" and (not cleaned_lines or cleaned_lines[-1] != ""):
            cleaned_lines.append(line)
        elif line != "":
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def generate_weather_data(zip_code, metric, api_key):
    forecast_icon = {
        1: "\u2600\uFE0F",
        2: "\u2600\uFE0F",
        3: "\U0001f324\uFE0F",
        4: "\U0001f324\uFE0F",
        5: "\u2600\uFE0F",
        6: "\U0001f325\uFE0F",
        7: "\u2601\uFE0F",
        8: "\u2601\uFE0F",
        11: "\U0001f32b\uFE0F",
        12: "\U0001f327\uFE0F",
        13: "\U0001f326\uFE0F",
        14: "\U0001f326\uFE0F",
        15: "\u26C8\uFE0F",
        16: "\u26C8\uFE0F",
        17: "\U0001f326\uFE0F",
        18: "\U0001f327\uFE0F",
        19: "\U0001f328\uFE0F",
        20: "\U0001f328\uFE0F",
        21: "\U0001f328\uFE0F",
        22: "\u2744\uFE0F",
        23: "\u2744\uFE0F",
        24: "\u2744\uFE0F",
        25: "\U0001f328\uFE0F",
        26: "\U0001f327\uFE0F",
        29: "\U0001f327\uFE0F",
        30: "\U0001f525",
        31: "\U0001f9ca",
        32: "\U0001f343",
    }

    wind_symbol = RangeDict(
        {
            range(0, 23): "\u2B06",  # N
            range(23, 68): "\u2197",  # NE
            range(68, 113): "\u27A1",  # E
            range(113, 158): "\u2198",  # SE
            range(158, 203): "\u2B07",  # S
            range(203, 248): "\u2199",  # SW
            range(248, 293): "\u2B05",  # W
            range(293, 338): "\u2196",  # NW
            range(338, 361): "\u2B06",  # N
        }
    )

    precipitation_types = ["Rain", "Snow", "Ice"]

    if metric:
        temp_unit = "C"
        precip_unit = "mm"
        wind_unit = "km/h"
    else:
        temp_unit = "F"
        precip_unit = "in"
        wind_unit = "mph"

    api_uri = "http://dataservice.accuweather.com"

    re_zip = re.compile(r"^(\d{5})[-\s]?(?:\d{4})?$")

    if zip_match := re.match(re_zip, zip_code.strip()):
        zip_code = zip_match[1]
    else:
        raise HTTPError(400)

    api_session = CachedSession("request_cache", stale_if_error=timedelta(hours=12))

    try:
        location_resp = api_session.get(
            f"{api_uri}/locations/v1/postalcodes/US/search?apikey={api_key}&q={zip_code}&language=en-us",
            expire_after=-1,
        )
        location_resp.raise_for_status()

        location_key = json.loads(location_resp.text)[0]["Key"]

        print(f"Got location_key {location_key} from {zip_code}")

        metric_str = str(metric).lower()

        forecast_resp = api_session.get(
            f"{api_uri}/forecasts/v1/daily/5day/{location_key}?apikey={api_key}&language=en-us&details=true&metric={metric_str}",
            expire_after=3600,
        )
        forecast_resp.raise_for_status()
    except HTTPError as http_err:
        if http_err.response.headers["Content-Type"] == "application/json":
            error_content = http_err.response.json()
        else:
            error_content = http_err.response.content.decode()
        raise HTTPErrorWithContent(http_err.response.status_code, error_content) from None

    print(f"Cache was used for location data: {location_resp.from_cache}")
    print(f"Cache was used for forecast data: {forecast_resp.from_cache}")

    forecast_json = json.loads(forecast_resp.text)

    # Timezone local to the location of the forecast
    forecast_timezone_str = forecast_json["Headline"]["EffectiveDate"][-6:]
    forecast_timezone = datetime.strptime(forecast_timezone_str, "%z")

    # created_at returns a datetime which does not have tzinfo set but should be UTC
    # create_at is None when the cache is initialized
    if not forecast_resp.created_at:
        forecast_cache_last_updated = datetime.utcnow()
    else:
        forecast_cache_last_updated = forecast_resp.created_at.replace(tzinfo=datetime.strptime("+0000", "%z").tzinfo)

    forecast_cache_last_updated = forecast_cache_last_updated.astimezone(forecast_timezone.tzinfo)

    weather_data_dict = dict()

    for forecast in forecast_json["DailyForecasts"]:
        day_cast = forecast["Day"]
        temp = forecast["Temperature"]
        rfeel = forecast["RealFeelTemperature"]
        air_qual = next(x for x in forecast["AirAndPollen"] if x["Name"] == "AirQuality")
        uv = next(x for x in forecast["AirAndPollen"] if x["Name"] == "UVIndex")

        wind = day_cast["Wind"]
        wind_dir = wind["Direction"]["Degrees"]
        wind_gust = day_cast["WindGust"]
        wind_gust_dir = wind_gust["Direction"]["Degrees"]

        summary = f"{forecast_icon[day_cast['Icon']]} {temp['Maximum']['Value']:.0f}° | {temp['Minimum']['Value']:.0f}°, {day_cast['IconPhrase']}"

        precip_description = ""

        has_precip = day_cast["HasPrecipitation"]

        if has_precip:
            precip_type = day_cast["PrecipitationType"]

            if precip_type == "Mixed":
                for precip_type in precipitation_types:
                    precip_prob = day_cast[f"{precip_type}Probability"]

                    if not precip_prob > 1:
                        continue

                    precip_seconds = timedelta(hours=day_cast[f"HoursOf{precip_type}"]).total_seconds()
                    hours, remainder = divmod(precip_seconds, 3600)
                    minutes = divmod(remainder, 60)[0]
                    precip_length = f"{hours:.0f} h"
                    if minutes > 0:
                        precip_length += f" {minutes:.0f} m"

                    precip_value = day_cast[precip_type]["Value"]
                    precip_prob = day_cast[f"{precip_type}Probability"]

                    precip_description += (
                        f"{precip_type}: {precip_value} {precip_unit}\n"
                        f"Length of {precip_type.lower()}: {precip_length}\n"
                        f"Chance of {precip_type.lower()}: {precip_prob:.0f}%\n"
                    )

                selected_precip = {k: v["Value"] for k, v in day_cast.items() if k in precipitation_types}

                max_key = max(selected_precip, key=selected_precip.get)

                if selected_precip[max_key] > 0:
                    precip_value = selected_precip[max_key]
                    summary += f" ({precip_value} {precip_unit})"

            else:
                precip_seconds = timedelta(hours=day_cast[f"HoursOf{precip_type}"]).total_seconds()
                hours, remainder = divmod(precip_seconds, 3600)
                minutes = divmod(remainder, 60)[0]

                precip_parts = []
                if hours > 0:
                    precip_parts.append(f"{hours:.0f} h")
                if minutes > 0:
                    precip_parts.append(f"{minutes:.0f} m")

                precip_length = " ".join(precip_parts)

                precip_value = day_cast[precip_type]["Value"]
                precip_prob = day_cast[f"{precip_type}Probability"]

                precip_description = (
                    f"{precip_type}: {precip_value} {precip_unit}\n"
                    f"Length of {precip_type.lower()}: {precip_length}\n"
                    f"Chance of {precip_type.lower()}: {precip_prob:.0f}%"
                )

                summary += f" ({precip_value} {precip_unit})"
        else:
            for precip_type in precipitation_types:
                precip_prob = day_cast[f"{precip_type}Probability"]
                if precip_prob > 1:
                    precip_description += f"Chance of {precip_type}: {precip_prob:.0f}%\n"

        # rstrip is needed to catch extra trailing newline on mixed precipitation
        precip_descr_condition = f"{precip_description.rstrip()}" if precip_description else ""

        description = f"""\
        Temperature: {temp['Minimum']['Value']:.0f}°{temp_unit} … {temp['Maximum']['Value']:.0f}°{temp_unit}
        RealFeel\u00AE: {rfeel['Minimum']['Value']:.0f}°{temp_unit} … {rfeel['Maximum']['Value']:.0f}°{temp_unit}
        
        Air quality: {air_qual['Category']} ({air_qual['Value']})
        UV index: {uv['Category']} ({uv['Value']})
        
        {precip_descr_condition}
        Cloud cover: {day_cast['CloudCover']:.0f}%
        
        Wind: {wind['Speed']['Value']} {wind_unit} {wind_symbol[wind_dir]} ({wind_dir}°)
        Wind gust: {wind_gust['Speed']['Value']} {wind_unit} {wind_symbol[wind_gust_dir]} ({wind_gust_dir}°)
        
        \u00A9 {datetime.today().year} AccuWeather, Inc.
        
        Updated: {datetime.strftime(forecast_cache_last_updated, '%a, %d %b %Y %I:%M%p %Z')}
        """

        weather_data_dict[forecast["EpochDate"]] = [summary, clean_description(description.rstrip()), forecast["Link"]]

    return weather_data_dict
