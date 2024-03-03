from datetime import datetime

from icalendar import Calendar, Event

from get_weather_data import generate_weather_data


def return_calendar_content(weather_data_dict):
    cal = Calendar()

    cal.add("prodid", "-//nateify//Weather to iCalendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("X-WR-CALNAME", "Weather")
    cal.add("X-WR-CALDESC", "Local weather prediction for up to 5 days.", parameters={"VALUE": "TEXT"})
    cal.add("X-PUBLISHED-TTL", "P1H", parameters={"VALUE": "TEXT"})
    cal.add("REFRESH-INTERVAL", "P1H", parameters={"VALUE": "DURATION"})

    for forecast_timestamp, forecast_data in weather_data_dict.items():
        date_fmt = datetime.fromtimestamp(forecast_timestamp).date()

        event = Event()
        event.add("X-MICROSOFT-CDO-ALLDAYEVENT", "TRUE")
        event.add("X-FUNAMBOL-ALLDAY", "1")
        event.add("X-MICROSOFT-CDO-BUSYSTATUS", "FREE")
        event.add("X-APPLE-TRAVEL-ADVISORY-BEHAVIOR", "DISABLED")
        event.add("STATUS", "CONFIRMED")
        event.add("TRANSP", "TRANSPARENT")
        event.add("CLASS", "PUBLIC")
        event.add("summary", forecast_data[0])
        event.add("description", forecast_data[1])
        event.add("url", forecast_data[2])
        event.add("uid", forecast_timestamp)
        event.add("dtstart", date_fmt)
        event.add("dtend", date_fmt)
        event.add("dtstamp", datetime.now())

        cal.add_component(event)

    return cal.to_ical()
