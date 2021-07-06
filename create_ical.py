from get_weather_data import output_weather_data
from icalendar import Calendar, Event
from datetime import datetime


def output_icalendar(zip_code, metric):
    cal = Calendar()

    cal.add("prodid", "-//nateify//Weather to iCalendar//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("X-WR-CALNAME", "Weather")
    cal.add("X-WR-CALDESC", "Local weather prediction for up to 5 days.", parameters={"VALUE": "TEXT"})
    cal.add("X-PUBLISHED-TTL", "P1H", parameters={"VALUE": "TEXT"})
    cal.add("REFRESH-INTERVAL", "P1H", parameters={"VALUE": "DURATION"})

    weather_data_dict = output_weather_data(zip_code, metric)

    for forecast_timestamp, forecast_data in weather_data_dict.items():
        event = Event()
        event.add("X-MICROSOFT-CDO-ALLDAYEVENT", "TRUE")
        event.add("X-FUNAMBOL-ALLDAY", "1")
        event.add("X-MICROSOFT-CDO-BUSYSTATUS", "FREE")
        event.add("X-APPLE-TRAVEL-ADVISORY-BEHAVIOR", "DISABLED")
        event.add("STATUS", "CONFIRMED")
        event.add("CLASS", "PUBLIC")
        event.add("summary", forecast_data[0])
        event.add("description", forecast_data[1])
        event.add("url", forecast_data[2])
        event.add("dtstart", datetime.fromtimestamp(forecast_timestamp).date())
        event.add("dtend", datetime.fromtimestamp(forecast_timestamp).date())
        event.add("dtstamp", datetime.now())

        cal.add_component(event)

    return cal.to_ical()
