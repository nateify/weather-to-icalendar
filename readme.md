weather-to-icalendar - Serves a dynamic ICS iCalendar file based on API data returned by [Open-Meteo](https://open-meteo.com/)

# Usage
* HTTP server serves over port 8080 by default - can be overwritten by PORT environment variable
* Navigating to "http://localhost:8080/" shows an HTML form which can be used to generate a link with correct query parameters

# Limitations
I created this project for personal use. No support is provided.

* Only accepts US postal codes
* Requests to the weather and air quality APIs are cached for 60 minutes - set your iCal client accordingly
* Requests to the geocoding API are cached indefinitely
