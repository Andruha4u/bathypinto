#!/usr/bin/env python3
"""Local dev server for the bathypinto static site.

Stdlib only — no install step. It serves the folder the way Netlify will:
root-relative /assets/... paths resolve, /404.html is returned with a real 404
status, extensionless URLs fall back to <name>.html, and the security headers
from netlify.toml are applied so a CSP mistake shows up here rather than in
production.

On top of that it does two dev-only things:

  * Rewrites the production origin (https://example.netlify.app) to the local
    one inside HTML/XML/TXT/webmanifest responses, so canonical links, OG URLs,
    the JSON-LD Person block, robots.txt and sitemap.xml all point at the page
    you are actually looking at.
  * Injects a small poller that reloads the tab when a file on disk changes.
    Disable it with --no-reload.

    python3 dev-server.py [--port 8000] [--host 127.0.0.1] [--no-reload] [--no-open]
"""

from __future__ import annotations

import argparse
import functools
import http.server
import mimetypes
import os
import posixpath
import socketserver
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Must match the origin hard-coded in index.html / robots.txt / sitemap.xml.
# Update this line if you run the domain find-and-replace from the README.
PROD_ORIGIN = "https://example.netlify.app"

# Responses whose bodies get the origin rewrite.
REWRITABLE = {".html", ".xml", ".txt", ".webmanifest", ".json"}

RELOAD_ENDPOINT = "/__dev/reload"
RELOAD_SNIPPET = """
<script>
/* dev-server.py live reload — not part of the deployed site */
(function () {
  var current = null;
  function poll() {
    fetch("%s", { cache: "no-store" })
      .then(function (r) { return r.text(); })
      .then(function (stamp) {
        if (current === null) { current = stamp; }
        else if (stamp !== current) { location.reload(); }
      })
      .catch(function () {});
  }
  setInterval(poll, 1000);
  poll();
})();
</script>
""" % RELOAD_ENDPOINT

# Netlify serves these; Python's mimetypes table does not always know them.
mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")

# From netlify.toml. HSTS is deliberately omitted — it would pin localhost to
# HTTPS in your browser for a year.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), interest-cohort=()",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none'"
    ),
}


def fingerprint() -> str:
    """Cheap change signal: newest mtime + file count across the tree."""
    newest = 0.0
    count = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            try:
                newest = max(newest, os.stat(os.path.join(dirpath, name)).st_mtime)
            except OSError:
                continue
            count += 1
    return f"{newest:.6f}-{count}"


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "bathypinto-dev"
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, live_reload: bool = True, origin: str = "", **kwargs):
        self.live_reload = live_reload
        self.origin = origin
        super().__init__(*args, **kwargs)

    # -- routing ---------------------------------------------------------

    def resolve(self, url_path: str) -> tuple[Path | None, int]:
        """Map a URL path to a file on disk, mirroring Netlify's resolution."""
        path = urllib.parse.unquote(url_path.split("?", 1)[0].split("#", 1)[0])
        path = posixpath.normpath(path)
        if not path.startswith("/"):
            path = "/" + path

        target = (ROOT / path.lstrip("/")).resolve()
        # Refuse anything that escapes the site root.
        if ROOT != target and ROOT not in target.parents:
            return ROOT / "404.html", 404

        if target.is_dir():
            index = target / "index.html"
            if index.is_file():
                return index, 200
            return ROOT / "404.html", 404

        if target.is_file():
            return target, 200

        # Netlify's pretty URLs: /about -> /about.html
        pretty = target.with_suffix(".html")
        if not target.suffix and pretty.is_file():
            return pretty, 200

        return ROOT / "404.html", 404

    def build_body(self, file: Path) -> tuple[bytes, str]:
        suffix = file.suffix.lower()
        ctype = mimetypes.guess_type(file.name)[0] or "application/octet-stream"

        if suffix not in REWRITABLE:
            return file.read_bytes(), ctype

        text = file.read_text(encoding="utf-8")
        text = text.replace(PROD_ORIGIN, self.origin)
        if suffix == ".html" and self.live_reload:
            if "</body>" in text:
                text = text.replace("</body>", RELOAD_SNIPPET + "</body>", 1)
            else:
                text += RELOAD_SNIPPET
        if ctype.startswith("text/") or "json" in ctype or "xml" in ctype:
            ctype = f"{ctype}; charset=utf-8"
        return text.encode("utf-8"), ctype

    # -- verbs -----------------------------------------------------------

    def do_GET(self) -> None:
        self.respond(include_body=True)

    def do_HEAD(self) -> None:
        self.respond(include_body=False)

    def respond(self, include_body: bool) -> None:
        if self.path.split("?", 1)[0] == RELOAD_ENDPOINT:
            payload = fingerprint().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if include_body:
                self.wfile.write(payload)
            return

        file, status = self.resolve(self.path)
        if file is None or not file.is_file():
            file, status = ROOT / "404.html", 404

        try:
            body, ctype = self.build_body(file)
        except OSError as exc:
            self.send_error(500, explain=str(exc))
            return

        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Dev never caches, so an edit is one refresh away. Production caching
        # lives in netlify.toml.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        for key, value in SECURITY_HEADERS.items():
            self.send_header(key, value)
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        status = args[1] if len(args) > 1 else ""
        mark = "  " if status == "200" else "! "
        sys.stderr.write(f"{mark}{self.address_string()} {fmt % args}\n")


class Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the site locally.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-reload", action="store_true", help="disable live reload")
    parser.add_argument("--no-open", action="store_true", help="don't open a browser")
    args = parser.parse_args()

    origin = f"http://{args.host}:{args.port}"
    handler = functools.partial(
        Handler, live_reload=not args.no_reload, origin=origin
    )

    try:
        httpd = Server((args.host, args.port), handler)
    except OSError as exc:
        print(f"Cannot bind {origin}: {exc}", file=sys.stderr)
        print("Another server is probably running — try --port 8001.", file=sys.stderr)
        return 1

    print(f"bathypinto  →  {origin}")
    print(f"serving     {ROOT}")
    print(f"live reload {'off' if args.no_reload else 'on'}   ·   Ctrl+C to stop\n")

    if not args.no_open:
        threading.Timer(0.4, webbrowser.open, args=(origin,)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
