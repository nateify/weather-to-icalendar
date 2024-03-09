from datetime import datetime, timedelta

from icalendar import Calendar, Event

from get_weather_data import generate_weather_data


def return_calendar_content(weather_data_dict):
    location = weather_data_dict["LocationString"]
    geo = weather_data_dict["LocationGeo"]

    cal = Calendar()

    cal.add("prodid", "-//nateify//Weather to iCalendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("NAME", "Weather")
    cal.add("X-WR-CALNAME", "Weather")
    cal.add("X-WR-CALDESC", f"Daily forecasts for {location}.", parameters={"VALUE": "TEXT"})
    cal.add("X-PUBLISHED-TTL", "P1H", parameters={"VALUE": "TEXT"})
    cal.add("REFRESH-INTERVAL", "P1H", parameters={"VALUE": "DURATION"})
    cal.add("COLOR", "gold")
    cal.add("X-APPLE-CALENDAR-COLOR", "#ffdc00")

    for forecast_data in weather_data_dict["ForecastEntries"]:
        forecast_timestamp = forecast_data[0]
        forecast_datetime = datetime.fromtimestamp(forecast_timestamp)
        forecast_datetime_midnight = forecast_datetime.replace(hour=0, minute=0, second=0, microsecond=0)

        event = Event()
        event.add("X-MICROSOFT-CDO-ALLDAYEVENT", "TRUE")
        event.add("X-FUNAMBOL-ALLDAY", "1")
        event.add("X-MICROSOFT-CDO-BUSYSTATUS", "FREE")
        event.add("X-APPLE-TRAVEL-ADVISORY-BEHAVIOR", "DISABLED")
        event.add("STATUS", "CONFIRMED")
        event.add("TRANSP", "TRANSPARENT")
        event.add("CLASS", "PUBLIC")
        event.add("CATEGORIES", "Weather")
        event.add("summary", forecast_data[1])
        event.add("description", forecast_data[2])
        event.add("url", forecast_data[3])
        event.add("uid", forecast_datetime_midnight.timestamp())
        event.add("dtstart", forecast_datetime.date())
        event.add("dtend", (forecast_datetime + timedelta(days=1)).date())
        event.add("dtstamp", forecast_datetime_midnight)
        event.add("LAST-MODIFIED", weather_data_dict["LastUpdated"])
        if geo:
            event.add("LOCATION", location)
            event.add("GEO", geo)

        cal.add_component(event)

    return cal.to_ical()
