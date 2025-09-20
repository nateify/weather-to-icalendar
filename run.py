import os
import sys

from bottle import run

from weather_ical.app import app


def main():
    if os.getenv("PYTHON_STDOUT_TO_STDERR") == "1":
        sys.stdout = sys.stderr

    server_port = int(os.getenv("PORT", 8080))
    server_address = os.getenv("HOST_ADDRESS", "127.0.0.1")

    print(f"Server started on {server_address}:{server_port}")
    run(app, host=server_address, port=server_port, debug=False)


if __name__ == "__main__":
    main()
