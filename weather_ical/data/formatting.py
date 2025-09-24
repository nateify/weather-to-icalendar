import re
from typing import Any


def format_hours_minutes(hours: float) -> str:
    if hours == 0.0:
        return "0h"

    whole_hours = int(hours)
    minutes_decimal = hours - whole_hours

    # Convert decimal to minutes and round to nearest minute
    minutes = round(minutes_decimal * 60)

    # Handle case where rounding minutes gives us 60
    if minutes == 60:
        whole_hours += 1
        minutes = 0

    # Format output
    if whole_hours == 0:
        return f"{minutes}m"
    if minutes == 0:
        return f"{whole_hours}h"

    return f"{whole_hours}h {minutes}m"


def format_float(value: float, decimals: int = 2) -> str:
    return f"{value:.{decimals}f}".rstrip("0").rstrip(".")


def clean_description(s: str) -> str:
    # Standardize line endings
    s = s.replace("\r\n", "\n")
    lines = [line.lstrip() for line in s.splitlines()]

    # Collapse consecutive blank lines
    cleaned_lines = []
    for line in lines:
        if (line == "" and (not cleaned_lines or cleaned_lines[-1] != "")) or line != "":
            cleaned_lines.append(line)

    # Join without trailing newline
    return "\n".join(cleaned_lines).rstrip("\n")


def validate_zip(zip_code: str) -> str | None:
    if not zip_code:
        return None

    re_zip = re.compile(r"^(\d{5})[-\s]?(?:\d{4})?$")
    match = re_zip.match(zip_code)

    if match:
        zip5 = match.group(1)

        # Naive check for valid ZIP code numbers
        if 501 <= int(zip5) <= 99950:
            return zip5

    return None


def format_precipitation_description(forecast: dict[str, Any], cutoff: float, unit: str) -> tuple[str, int]:
    """Formats the precipitation part of the weather description."""

    if not (forecast["precipitation_sum"] > cutoff or forecast["precipitation_hours"] > 0):
        if forecast["precipitation_probability_max"] > 1:
            return f"Chance of precipitation: {forecast['precipitation_probability_max']:.0f}%", 0
        return "", 0

    precip_types = []
    if forecast["rain_sum"] > 0:
        precip_types.append(("Rain", forecast["rain_sum"]))
    if forecast["showers_sum"] > 0:
        precip_types.append(("Showers", forecast["showers_sum"]))
    if forecast["snowfall_sum"] > 0:
        precip_types.append(("Snow", forecast["snowfall_sum"]))

    if not precip_types:
        return "", 0

    # Group precipitation events by duration and chance to consolidate descriptions
    precip_groups = {}
    duration_str = format_hours_minutes(forecast["precipitation_hours"])
    chance = forecast["precipitation_probability_max"]
    group_key = (duration_str, chance)

    # Select the dominant precipitation type for the description
    # Prefers the type with the highest amount, defaulting to Rain in a tie.
    dominant_type, max_value = max(precip_types, key=lambda item: (item[1], item[0] == "Rain"))
    precip_groups[group_key] = (dominant_type, max_value)

    precip_parts = []
    for (duration, chance), (precip_type, value) in precip_groups.items():
        precip_parts.extend(
            [
                f"{precip_type}: {format_float(value)} {unit}",
                f"Length of {precip_type.lower()}: {duration}",
                f"Chance of {precip_type.lower()}: {chance:.0f}%",
            ]
        )

    max_amount = max((amount for _, amount in precip_types if amount > 0), default=0)

    return "\n".join(precip_parts), max_amount
