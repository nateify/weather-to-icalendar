from datetime import datetime, timedelta, timezone

import numpy as np
import polars as pl


def get_timezone_info(response):
    """Extract timezone information from API response."""
    utc_offset_seconds = response.UtcOffsetSeconds()
    offset_hours = utc_offset_seconds // 3600
    offset_minutes = abs(utc_offset_seconds % 3600) // 60
    polars_tz = f"{offset_hours:+03d}:{offset_minutes:02d}"
    location_timezone = timezone(timedelta(seconds=utc_offset_seconds))
    return polars_tz, location_timezone


def create_timestamps(time_obj, location_timezone):
    """Create local timestamps from API time object."""
    timestamps = np.arange(time_obj.Time(), time_obj.TimeEnd(), time_obj.Interval())
    return [datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(location_timezone) for ts in timestamps]


def create_hourly_dataframe(response, location_timezone, polars_tz, variable_names=None):
    """Create DataFrame from hourly weather data."""
    hourly = response.Hourly()
    local_timestamps = create_timestamps(hourly, location_timezone)

    data_dict = {"local_datetime": local_timestamps}
    for i in range(hourly.VariablesLength()):
        key = variable_names[i] if variable_names and i < len(variable_names) else f"var_{i}"
        data_dict[key] = hourly.Variables(i).ValuesAsNumpy()

    return pl.DataFrame(data_dict).with_columns(pl.col("local_datetime").dt.convert_time_zone(polars_tz))


def create_minutely_dataframe(response, location_timezone, polars_tz):
    """Create DataFrame from 15-minute precipitation data."""
    minutely_15 = response.Minutely15()
    local_timestamps = create_timestamps(minutely_15, location_timezone)
    precipitation_data = minutely_15.Variables(0).ValuesAsNumpy()

    data_dict = {"local_datetime": local_timestamps, "precipitation": precipitation_data}
    return pl.DataFrame(data_dict).with_columns(pl.col("local_datetime").dt.convert_time_zone(polars_tz))


def calculate_vector_wind_direction(directions, speeds):
    """Calculate vector average wind direction weighted by wind speed."""
    directions_rad = np.radians(directions)
    x_component = np.sum(speeds * np.cos(directions_rad))
    y_component = np.sum(speeds * np.sin(directions_rad))
    avg_direction_rad = np.arctan2(y_component, x_component)
    avg_direction = np.degrees(avg_direction_rad)
    return avg_direction + 360 if avg_direction < 0 else avg_direction


def get_daily_wind_vectors(df):
    """Calculate daily vector-averaged wind directions."""
    wind_data = []
    for date in df.select("date").unique().to_series():
        day_data = df.filter(pl.col("date") == date)
        directions = day_data.select("wind_direction_10m").to_numpy().flatten()
        speeds = day_data.select("wind_speed_10m").to_numpy().flatten()

        valid_mask = ~(np.isnan(directions) | np.isnan(speeds))
        if valid_mask.any():
            vector_avg = calculate_vector_wind_direction(directions[valid_mask], speeds[valid_mask])
        else:
            vector_avg = float("nan")

        wind_data.append({"date": date, "vector_avg_wind_direction_10m": vector_avg})

    return pl.DataFrame(wind_data)


def get_daily_precipitation_data(minutely_df):
    """Aggregate minutely precipitation data to daily totals and duration."""
    return (
        minutely_df.with_columns(pl.col("local_datetime").dt.date().alias("date"))
        .filter(pl.col("precipitation") > 0)
        .group_by("date")
        .agg(
            pl.col("precipitation").count().alias("precipitation_intervals"),
            pl.col("precipitation").sum().alias("precipitation_sum"),
        )
        .with_columns((pl.col("precipitation_intervals") * 15 / 60).alias("precipitation_hours"))
        .select(["date", "precipitation_hours", "precipitation_sum"])
    )


def aggregate_daily_data(df, end_date):
    """Aggregate hourly weather data to daily statistics."""
    return (
        df.with_columns(pl.col("local_datetime").dt.date().alias("date"))
        .filter(pl.col("date") <= pl.lit(end_date))
        .group_by("date")
        .agg(
            pl.col("us_aqi").max().alias("aqi_max"),
            pl.col("temperature_2m").min().alias("temperature_min"),
            pl.col("temperature_2m").max().alias("temperature_max"),
            pl.col("apparent_temperature").min().alias("apparent_temperature_min"),
            pl.col("apparent_temperature").max().alias("apparent_temperature_max"),
            pl.col("relative_humidity_2m").max().alias("relative_humidity_max"),
            pl.col("precipitation_probability").max().alias("precipitation_probability_max"),
            pl.col("rain").sum().alias("rain_sum"),
            pl.col("showers").sum().alias("showers_sum"),
            pl.col("snowfall").sum().alias("snowfall_sum"),
            pl.col("cloud_cover").mean().alias("cloud_cover_mean"),
            pl.col("wind_speed_10m").mean().alias("wind_speed_mean"),
            pl.col("wind_gusts_10m").max().alias("wind_gusts_max"),
            pl.col("uv_index").max().alias("uv_index_max"),
            pl.col("weather_code").max().alias("wmo"),
            pl.col("us_aqi").count().alias("hours_count"),
        )
        .sort("date")
    )


def round_final_data(df):
    """Apply final rounding to numeric columns."""
    return df.with_columns(
        pl.col("aqi_max").round(0).cast(pl.Int32),
        pl.col("temperature_min").round(0),
        pl.col("temperature_max").round(0),
        pl.col("apparent_temperature_min").round(0),
        pl.col("apparent_temperature_max").round(0),
        pl.col("rain_sum").round(2),
        pl.col("showers_sum").round(2),
        pl.col("snowfall_sum").round(2),
        pl.col("precipitation_sum").round(2),
        pl.col("cloud_cover_mean").round(0),
        pl.col("wind_speed_mean").round(0),
        pl.col("wind_gusts_max").round(0),
        pl.col("vector_avg_wind_direction_10m").round(0).cast(pl.Int32),
        pl.col("uv_index_max").round(0).cast(pl.Int32),
        pl.col("wmo").cast(pl.Int32),
    )


def process_weather_data(aqi_response, weather_response, weather_params, forecast_days=5):
    """Main function to process weather and air quality data."""

    # Get timezone info
    polars_tz, location_timezone = get_timezone_info(aqi_response)

    # Create DataFrames
    aqi_df = create_hourly_dataframe(aqi_response, location_timezone, polars_tz, ["us_aqi"])
    weather_df = create_hourly_dataframe(weather_response, location_timezone, polars_tz, weather_params["hourly"])
    minutely_df = create_minutely_dataframe(weather_response, location_timezone, polars_tz)

    # Join hourly data
    df = aqi_df.join(weather_df, on="local_datetime", how="inner")

    # Calculate aggregations
    current_local_date = df.select(pl.col("local_datetime").dt.date().min()).item()
    end_date = current_local_date + timedelta(days=forecast_days - 1)

    daily_data = aggregate_daily_data(df, end_date)
    wind_vector_df = get_daily_wind_vectors(df.with_columns(pl.col("local_datetime").dt.date().alias("date")))
    minutely_daily = get_daily_precipitation_data(minutely_df)

    # Join and finalize
    final_data = (
        daily_data.join(wind_vector_df, on="date", how="left")
        .join(minutely_daily, on="date", how="left")
        .with_columns(pl.col("precipitation_hours").fill_null(0.0), pl.col("precipitation_sum").fill_null(0.0))
    )

    return round_final_data(final_data)
