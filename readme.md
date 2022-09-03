weather-to-icalendar - Serves a dynamic ICS iCalendar file based on API data returned by [AccuWeather](https://developer.accuweather.com/)

# Usage
* Runs on http://localhost:8080/ by default
* Input a US postal code as path
  * Example: http://localhost:8080/90210
* Metric units can be enabled by appending /metric to the URL

# Limitations
I created this project for personal use. No support is provided and no contributions are accepted.

* Only accepts US postal codes
* Only daytime conditions are displayed (relative to the timezone that the zipcode resides in)
* Preciptation data is only displayed for rain, but the API supports snow, ice, and mixed
* Requests to the forecast API are cached for 60 minutes - set your iCal client accordingly
* Requests to the location API are cached indefinitely
  * No function is included to invalidate the cache, however the location key should not change
* [http.server](https://docs.python.org/3/library/http.server.html) module is used for simplicity - uses HTTP 1.0 and no compression