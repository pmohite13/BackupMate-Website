#!/usr/bin/env python3
"""Look at the built site locally: python preview.py, then open http://localhost:8080

Python's own file server would do, except that the site links to /pricing and
the file is pricing.html. The real host resolves that; this does the same, so
that what you click through here is what visitors will get.
"""
import http.server
import os
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent / "public"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC), **kwargs)

    def translate_path(self, path):
        full = super().translate_path(path)
        if not os.path.exists(full) and os.path.exists(full + ".html"):
            return full + ".html"
        return full

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (PUBLIC / "404.html").exists():
            body = (PUBLIC / "404.html").read_bytes()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().send_error(code, message, explain)


if __name__ == "__main__":
    print("http://localhost:8080  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8080), Handler).serve_forever()
