import re
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from create_ical import output_icalendar


class SharedCalendarServer(BaseHTTPRequestHandler):
    def do_GET(self):

        http_request = self.path.split("/")[1:]

        re_zipcode = re.compile(r"^(\d{5})[-\s]?(?:\d{4})?$")

        if re.match(re_zipcode, http_request[0]):
            zip_code: str = re.match(re_zipcode, http_request[0])[1]

            if len(http_request) > 1 and http_request[1] == "metric":
                metric_mode = True
            else:
                metric_mode = False

            http_response = output_icalendar(zip_code, metric_mode)

            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.end_headers()
            self.wfile.write(http_response)

        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(f"Invalid request: {self.path}", "utf-8"))


if __name__ == "__main__":
    server_port = os.environ.get("PORT", "5000")
    server_address = ("", int(server_port))
    webServer = HTTPServer(server_address, SharedCalendarServer)
    print(f"Server started on port {server_port}")

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
