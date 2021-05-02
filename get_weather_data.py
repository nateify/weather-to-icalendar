import json
import os
from datetime import timedelta
from dotenv import load_dotenv
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


icons = {
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

winds = RangeDict(
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

load_dotenv()

api_key = os.environ["ACCUWEATHER_API_KEY"]
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

    weather_data_dict = dict()

    accuweatherSession = CachedSession("accuweather_cache", old_data_on_error=True)

    location_session = accuweatherSession.request(
        "GET",
        f"{api_url_prefix}/locations/v1/postalcodes/US/search?apikey={api_key}&q={zip_code}&language=en-us",
        expire_after=-1,
    )
    print("location data from cache:", location_session.from_cache)

    location_json = json.loads(location_session.text)

    locationKeyValue = location_json[0]["Key"]

    forecast_session = accuweatherSession.request(
        "GET",
        f"{api_url_prefix}/forecasts/v1/daily/5day/{locationKeyValue}?apikey={api_key}&language=en-us&details=true&metric={str(metric).lower()}",
        expire_after=3600,
    )

    print("forecast data from cache:", forecast_session.from_cache)

    forecast_json = json.loads(forecast_session.text)

    for forecast in forecast_json["DailyForecasts"]:
        TempObj = forecast["Temperature"]
        HeatIndxObj = forecast["RealFeelTemperature"]
        WindObj = forecast["Day"]["Wind"]
        WindDegrees = WindObj["Direction"]["Degrees"]
        WindGObj = forecast["Day"]["WindGust"]
        WindGDegrees = WindGObj["Direction"]["Degrees"]

        precipitation_length = timedelta(hours=forecast["Day"]["HoursOfPrecipitation"]).total_seconds()
        hours, remainder = divmod(precipitation_length, 3600)
        minutes = divmod(remainder, 60)[0]

        summary = f"{icons[forecast['Day']['Icon']]} {TempObj['Maximum']['Value']:.0f}° | {TempObj['Minimum']['Value']:.0f}°, {forecast['Day']['IconPhrase']}"

        if forecast["Day"]["HasPrecipitation"]:
            summary += f" ({forecast['Day']['Rain']['Value']} {rain_unit})"

        description = f"Temperature unit: {TempObj['Minimum']['Value']:.0f}°{temp_unit} … {TempObj['Maximum']['Value']:.0f}°{temp_unit}\n"
        description += f"Heat index: {HeatIndxObj['Minimum']['Value']:.0f}°{temp_unit} … {HeatIndxObj['Maximum']['Value']:.0f}°{temp_unit}\n\n"
        description += f"Precipitation: {forecast['Day']['Rain']['Value']} {rain_unit}\n"
        description += f"Length of precipitation: {hours:.0f} h"
        if minutes > 0:
            description += f" {minutes:.0f} m"

        description += f"\nChance of rain: {forecast['Day']['PrecipitationProbability']:.0f}%\n"
        description += f"Cloud cover: {forecast['Day']['CloudCover']:.0f}%\n\n"
        description += f"Wind: {WindObj['Speed']['Value']} {wind_unit} {winds[WindDegrees]} ({WindDegrees}°)\n"
        description += (
            f"Wind gust: {WindGObj['Speed']['Value']} {wind_unit} {winds[WindGDegrees]} ({WindGDegrees}°)\n\n"
        )
        description += f"Additional information\n{forecast['Link']}"

        weather_data_dict[forecast["EpochDate"]] = [summary, description, forecast["Link"]]

    return weather_data_dict
