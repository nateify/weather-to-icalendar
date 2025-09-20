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
    0: ("Sunny", "\u2600\ufe0f"),
    1: ("Mostly sunny", "\U0001f324"),
    2: ("Partly cloudy", "\u26c5\ufe0f"),
    3: ("Cloudy", "\u2601\ufe0f"),
    45: ("Fog", "\U0001f32b"),
    48: ("Icy fog", "\U0001f9ca"),
    51: ("Light drizzle", "\U0001f327"),
    53: ("Drizzle", "\U0001f327"),
    55: ("Heavy drizzle", "\U0001f327"),
    56: ("Light freezing drizzle", "\U0001f328"),
    57: ("Freezing drizzle", "\U0001f328"),
    61: ("Light rain", "\U0001f327"),
    63: ("Rain", "\U0001f327"),
    65: ("Heavy rain", "\U0001f327"),
    66: ("Light freezing rain", "\U0001f328"),
    67: ("Freezing rain", "\U0001f328"),
    71: ("Light snow", "\u2744\ufe0f"),
    73: ("Snow", "\u2744\ufe0f"),
    75: ("Heavy Snow", "\u2744\ufe0f"),
    77: ("Snow grains", "\u2744\ufe0f"),
    80: ("Light showers", "\U0001f327"),
    81: ("Showers", "\U0001f327"),
    82: ("Heavy showers", "\U0001f327"),
    85: ("Light snow showers", "\u2744\ufe0f"),
    86: ("Snow showers", "\u2744\ufe0f"),
    95: ("Thunderstorm", "\u26c8\ufe0f"),
    96: ("Light T-storm w/ hail", "\U0001f9ca"),
    99: ("T-storm w/ hail", "\U0001f9ca"),
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
