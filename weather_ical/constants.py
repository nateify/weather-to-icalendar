from typing import Any


class RangeDict(dict[range, Any]):
    def __getitem__(self, item: range | int) -> Any:
        if not isinstance(item, range):
            for key in self:
                # Use -1 as an unbounded end
                if item in key or (key.stop == -1 and item >= key.start):
                    return self[key]
            raise KeyError(item)
        return super().__getitem__(item)


FORECAST_DAYS = 5

WMO_MAP = {
    0: ("Sunny", "☀"),
    1: ("Mostly sunny", "🌤"),
    2: ("Partly cloudy", "⛅"),
    3: ("Cloudy", "☁"),
    45: ("Fog", "🌫"),
    48: ("Icy fog", "🧊"),
    51: ("Light drizzle", "🌧"),
    53: ("Drizzle", "🌧"),
    55: ("Heavy drizzle", "🌧"),
    56: ("Light freezing drizzle", "🌨"),
    57: ("Freezing drizzle", "🌨"),
    61: ("Light rain", "🌧"),
    63: ("Rain", "🌧"),
    65: ("Heavy rain", "🌧"),
    66: ("Light freezing rain", "🌨"),
    67: ("Freezing rain", "🌨"),
    71: ("Light snow", "❄"),
    73: ("Snow", "❄"),
    75: ("Heavy Snow", "❄"),
    77: ("Snow grains", "❄"),
    80: ("Light showers", "🌧"),
    81: ("Showers", "🌧"),
    82: ("Heavy showers", "🌧"),
    85: ("Light snow showers", "❄"),
    86: ("Snow showers", "❄"),
    95: ("Thunderstorm", "⛈"),
    96: ("Light T-storm w/ hail", "🧊"),
    99: ("T-storm w/ hail", "🧊"),
}

WIND_DIR_MAP = RangeDict(
    {
        range(23): "⬆",  # N
        range(23, 68): "↗",  # NE
        range(68, 113): "➡",  # E
        range(113, 158): "↘",  # SE
        range(158, 203): "⬇",  # S
        range(203, 248): "↙",  # SW
        range(248, 293): "⬅",  # W
        range(293, 338): "↖",  # NW
        range(338, 361): "⬆",  # N
    }
)

AQI_MAP = RangeDict(
    {
        range(51): "Good",
        range(51, 101): "Fair",
        range(101, 151): "Unhealthy (Sensitive)",
        range(151, 201): "Poor",
        range(201, 301): "Very Poor",
        range(301, -1): "Hazardous",
    }
)

UVI_MAP = RangeDict(
    {
        range(3): "Low",
        range(3, 6): "Moderate",
        range(6, 8): "High",
        range(8, 11): "Very High",
        range(11, -1): "Extreme",
    }
)
