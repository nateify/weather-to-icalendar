weather-to-icalendar - Serves a dynamic ICS iCalendar file based on API data returned by [AccuWeather](https://developer.accuweather.com/accuweather-forecast-api/apis/get/forecasts/v1/daily/5day/%7BlocationKey%7D)

# Usage
* HTTP server serves over port 8080 by default - can be overwritten by PORT environment variable
* Navigating to "http://localhost:8080/" shows an HTML form which can be used to generate a link with correct query parameters
* API key can alternatively be set by environment variable ACCUWEATHER_API_KEY

# Limitations
I created this project for personal use. No support is provided and no contributions are accepted.

* Only accepts US postal codes
* Only daytime conditions are displayed (relative to the timezone that the zipcode resides in)
* Requests to the forecast API are cached for 60 minutes - set your iCal client accordingly
* Requests to the location API are cached indefinitely
  * No function is included to invalidate the cache, however the location key should not change
* [http.server](https://docs.python.org/3/library/http.server.html) module is used for simplicity - serves HTTP 1.0 and no compression