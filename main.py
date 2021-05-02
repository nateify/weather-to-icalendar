import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from create_ical import output_icalendar

hostName = "localhost"
serverPort = 8080

re_zip = re.compile(r"^(\d{5})[-\s]?(?:\d{4})?$")


class SharedCalendarServer(BaseHTTPRequestHandler):
    def do_GET(self):

        http_request = self.path.split("/")[1:]

        if re.match(re_zip, http_request[0]):
            zip_code = re.match(re_zip, http_request[0])[1]

            if len(http_request) > 1 and http_request[1] == "metric":
                metric_mode = True
            else:
                metric_mode = False

            http_response = output_icalendar(zip_code, metric_mode)

            self.send_response(200)
            self.send_header("Content-Type", "text/calendar")
            self.end_headers()
            self.wfile.write(http_response)

        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bytes(f"Invalid request: {self.path}", "utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), SharedCalendarServer)
    print(f"Server started http://{hostName}:{serverPort}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
