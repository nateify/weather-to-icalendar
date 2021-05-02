weather-to-icalendar - Serves a dynamic ICS iCalendar file based on API data returned by [AccuWeather](https://developer.accuweather.com/)

# Usage
* Runs on http://localhost:8080/ by default
* Input a US postal code as path
  * Example: http://localhost:8080/90210
* Metric units can enabled by adding /metric to the URL

# Limitations
The project is a hobbyist effort intended for my personal use

* Hard coded for postal code input limited to the United States
* Additional details and summary provided for rainfall but not snowfall
* No sunrise/sunset data displayed
* No moon phase data displayed
* Requests to the forecast API are cached for 60 minutes - set your iCal client accordingly
  * AccuWeather API allows for 50 free calls per 24-hour period
* Requests to the location API are cached indefinitely after the first request for a given postal code
  * No way to programatically invalidate the cache, however the location key should not change
