import json
import os
from datetime import datetime, timedelta

from requests_cache import CachedSession


class RangeDict(dict):
    def __getitem__(self, item):
        if not isinstance(item, range):
            for key in self:
                if item in key:
                    return self[key]
            raise KeyError(item)
        else:
            return super().__getitem__(item)


forecast_icons = {
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

wind_symbols = RangeDict(
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

api_key = os.environ["ACCUWEATHER_API_KEY"]
print("Loaded AccuWeather API key")

api_url_prefix = "http://dataservice.accuweather.com"


def output_weather_data(zip_code, metric):
    if metric:
        temp_unit = "C"
        rain_unit = "mm"
        wind_unit = "km/h"
    else:
        temp_unit = "F"
        rain_unit = "in"
        wind_unit = "mph"

    metric = str(metric).lower()

    weather_data_dict = dict()

    api_session = CachedSession("request_cache", old_data_on_error=True)

    location_session = api_session.request(
        "GET",
        f"{api_url_prefix}/locations/v1/postalcodes/US/search?apikey={api_key}&q={zip_code}&language=en-us",
        expire_after=-1,
    )
    print("Cache used for location data:", location_session.from_cache)

    location_key = json.loads(location_session.text)[0]["Key"]

    forecast_session = api_session.request(
        "GET",
        f"{api_url_prefix}/forecasts/v1/daily/5day/{location_key}?apikey={api_key}&language=en-us&details=true&metric={metric}",
        expire_after=3600,
    )

    print("Cache used for forecast data:", forecast_session.from_cache)

    forecast_json = json.loads(forecast_session.text)

    # Timezone local to the location of the forecast
    forecast_timezone_str = forecast_json["Headline"]["EffectiveDate"][-6:]
    forecast_timezone = datetime.strptime(forecast_timezone_str, "%z")

    # created_at returns a datetime which does not have tzinfo set but should be UTC
    # create_at is None when the cache is initialized
    if not forecast_session.created_at:
        forecast_cache_last_updated = datetime.utcnow()
    else:
        forecast_cache_last_updated = forecast_session.created_at.replace(
            tzinfo=datetime.strptime("+0000", "%z").tzinfo
        )

    forecast_cache_last_updated = forecast_cache_last_updated.astimezone(forecast_timezone.tzinfo)

    for forecast in forecast_json["DailyForecasts"]:
        j_temp = forecast["Temperature"]
        j_heat = forecast["RealFeelTemperature"]
        j_air = next(x for x in forecast["AirAndPollen"] if x["Name"] == "AirQuality")
        j_uv = next(x for x in forecast["AirAndPollen"] if x["Name"] == "UVIndex")
        j_wind = forecast["Day"]["Wind"]
        j_wind_dir = j_wind["Direction"]["Degrees"]
        j_wind_gust = forecast["Day"]["WindGust"]
        j_wind_gust_dir = j_wind_gust["Direction"]["Degrees"]

        dt_precip_length = timedelta(hours=forecast["Day"]["HoursOfPrecipitation"]).total_seconds()
        hours, remainder = divmod(dt_precip_length, 3600)
        minutes = divmod(remainder, 60)[0]
        s_precip_length = f"{hours:.0f} h"
        if minutes > 0:
            s_precip_length += f" {minutes:.0f} m"

        summary = f"{forecast_icons[forecast['Day']['Icon']]} {j_temp['Maximum']['Value']:.0f}° | {j_temp['Minimum']['Value']:.0f}°, {forecast['Day']['IconPhrase']}"

        # Rain depth in parantheses
        if forecast["Day"]["HasPrecipitation"] and forecast["Day"]["PrecipitationType"] == "Rain":
            summary += f" ({forecast['Day']['Rain']['Value']} {rain_unit})"

        description = f"""\
        Temperature unit: {j_temp['Minimum']['Value']:.0f}°{temp_unit} … {j_temp['Maximum']['Value']:.0f}°{temp_unit}
        Heat index: {j_heat['Minimum']['Value']:.0f}°{temp_unit} … {j_heat['Maximum']['Value']:.0f}°{temp_unit}
        
        Air quality: {j_air['Category']} ({j_air['Value']})
        UV index: {j_uv['Category']} ({j_uv['Value']})
        
        Precipitation: {forecast['Day']['Rain']['Value']} {rain_unit}
        Length of precipitation: {s_precip_length}
        Chance of rain: {forecast['Day']['PrecipitationProbability']:.0f}%
        Cloud cover: {forecast['Day']['CloudCover']:.0f}%
        
        Wind: {j_wind['Speed']['Value']} {wind_unit} {wind_symbols[j_wind_dir]} ({j_wind_dir}°)
        Wind gust: {j_wind_gust['Speed']['Value']} {wind_unit} {wind_symbols[j_wind_gust_dir]} ({j_wind_gust_dir}°)
        
        \u00A9 {datetime.today().year} AccuWeather, Inc.
        
        Updated: {datetime.strftime(forecast_cache_last_updated, '%a, %d %b %Y %I:%M%p %Z')}
        
        Additional information
        {forecast['Link']}
        """

        weather_data_dict[forecast["EpochDate"]] = [summary, description, forecast["Link"]]

    return weather_data_dict
