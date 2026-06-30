import json
import mimetypes
import pathlib
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import jinja2

BASE_DIR = pathlib.Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
DATA_FILE = STORAGE_DIR / "data.json"

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(BASE_DIR / "templates"))


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path).path

        if route == "/":
            self.send_html_file("index.html")
        elif route == "/message.html":
            self.send_html_file("message.html")
        elif route == "/read":
            self.send_read_page()
        else:
            self.send_static(route)

    def do_POST(self):
        if urllib.parse.urlparse(self.path).path != "/message":
            self.send_html_file("error.html", 404)
            return

        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        parsed = urllib.parse.parse_qs(body.decode())
        message_data = {key: value[0] for key, value in parsed.items()}

        self.save_message(message_data)

        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def save_message(self, message_data):
        STORAGE_DIR.mkdir(exist_ok=True)

        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                try:
                    all_messages = json.load(file)
                except json.JSONDecodeError:
                    all_messages = {}
        else:
            all_messages = {}

        timestamp = str(datetime.now())
        all_messages[timestamp] = message_data

        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(all_messages, file, ensure_ascii=False, indent=2)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(BASE_DIR / filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, route):
        file_path = (BASE_DIR / route.lstrip("/")).resolve()

        if BASE_DIR not in file_path.parents or not file_path.is_file():
            self.send_html_file("error.html", 404)
            return

        self.send_response(200)
        mime_type, _ = mimetypes.guess_type(str(file_path))
        self.send_header("Content-type", mime_type or "application/octet-stream")
        self.end_headers()
        with open(file_path, "rb") as file:
            self.wfile.write(file.read())

    def send_read_page(self):
        if DATA_FILE.exists():
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                try:
                    messages = json.load(file)
                except json.JSONDecodeError:
                    messages = {}
        else:
            messages = {}

        sorted_messages = dict(sorted(messages.items(), reverse=True))

        template = jinja_env.get_template("read.html")
        html = template.render(messages=sorted_messages)

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http_server = server_class(server_address, handler_class)
    print("Server running on http://localhost:3000")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


if __name__ == "__main__":
    run()
