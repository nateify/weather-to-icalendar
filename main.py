import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

from create_ical import return_calendar_content
from get_weather_data import generate_weather_data


def flat_opts(d):
    for key, value in d.items():
        if key == "precipitation_types":
            continue
        if isinstance(value, list) and len(value) == 1:
            d[key] = value[0]
    return d


def bool_eval(value):
    true_values = {"y", "yes", "t", "true", "on", "1", 1, True}
    return str(value).lower() in true_values


class SharedCalendarServer(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_components = parse_qs(parsed_url.query)

        if path == "/weather":

            weather_opts = {
                "zip_code": query_components.get("zip", None),
                "metric": query_components.get("metric", False),
                "api_key": query_components.get("api_key", os.environ["ACCUWEATHER_API_KEY"]),
            }

            weather_opts = flat_opts(weather_opts)

            weather_opts["metric"] = bool_eval(weather_opts["metric"])

            try:
                weather_data = generate_weather_data(**weather_opts)

                http_response = return_calendar_content(weather_data)

                self.send_response(200)
                self.send_header("Content-Type", "text/calendar; charset=utf-8")
                self.end_headers()
                self.wfile.write(http_response)
            except:
                self.send_response(400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(bytes(f"Invalid request: {self.path}", "utf-8"))

        elif path == "/link":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            html = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body>
                <a href="/weather?{urlencode(query_components, doseq=True)}">Link to iCalendar</a>
            </body>
            </html>
            """

            self.wfile.write(bytes(html, "utf-8"))

        elif path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Weather to iCalendar</title>
            </head>
            <body>
                <form action="/link" method="get">
                    Accuweather API Key: <input type="text" name="api_key"><br>
                    Zip Code: <input type="text" name="zip" pattern="\\d{5}" inputmode="numeric" required><br>
                    Units: 
                    <select name="metric">
                        <option value="false">Imperial</option>
                        <option value="true">Metric</option>
                    </select>
                    <input type="submit" value="Submit">
                </form>
            </body>
            </html>
            """

            self.wfile.write(bytes(html, "utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(f"Invalid request: {self.path}", "utf-8"))

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/calendar; charset=utf-8")
        self.end_headers()


if __name__ == "__main__":
    server_port = os.getenv("PORT", "8080")
    server_address = ("", int(server_port))
    webServer = HTTPServer(server_address, SharedCalendarServer)
    print(f"Server started on port {server_port}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
