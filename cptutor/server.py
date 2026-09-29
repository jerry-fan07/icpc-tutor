"""The website: a small stdlib HTTP server over `Api`.

    python3 cp.py serve              # http://127.0.0.1:8000
    python3 cp.py serve --port 9000

Static files come from web/; `/api/<op>` calls `Api.op_<op>`.  Reads may be GET with a
query string; anything that changes progress must be a POST with a JSON body.  Only JSON
is accepted, which keeps a form on another site from posting here.

SECURITY: judging compiles and runs whatever C++ is submitted, with time and output limits
but no sandbox.  That is what a local tutor needs, and it is why the server binds to
127.0.0.1 unless you pass --host.  Only do that on a network you control.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl

from . import judge, loader
from .api import Api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "web")
MAX_BODY = 1 << 20

# Ops that compile and run code.  They take seconds, so they run outside the progress
# lock; the ones that change progress book their result under the lock afterwards.
JUDGING = {"run", "custom", "playground"}
READS = {"today", "lessons", "lesson", "problem", "problems", "due", "stats", "env", "ping",
         "contest", "notebook"}

TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
         ".ico": "image/x-icon", ".json": "application/json", ".png": "image/png",
         ".woff2": "font/woff2"}


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


class Handler(BaseHTTPRequestHandler):
    server_version = "ICPCTutor/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        if not self.server.quiet:                               # type: ignore[attr-defined]
            sys.stderr.write("%s  %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, status: int, body: bytes, ctype: str, extra=()) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in extra:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8", [("Cache-Control", "no-store")])

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise HttpError(413, "request too large")
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        if ctype != "application/json":
            raise HttpError(415, "expected Content-Type: application/json")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise HttpError(400, "body is not valid JSON")
        return data if isinstance(data, dict) else {}

    def do_GET(self) -> None:
        self._serve()

    def do_HEAD(self) -> None:
        self._serve()

    def do_POST(self) -> None:
        self._serve()

    def _serve(self) -> None:
        path = self.path.split("?", 1)[0]
        try:
            if path.startswith("/api/"):
                self._api(path[len("/api/"):])
            elif self.command == "POST":
                raise HttpError(405, "method not allowed")
            else:
                self._static(path)
        except HttpError as e:
            self.close_connection = True
            self._json({"ok": False, "error": e.message}, e.status)
        except (KeyError, ValueError, IndexError) as e:
            msg = e.args[0] if e.args else str(e)
            self._json({"ok": False, "error": str(msg)}, 400)
        except judge.JudgeError as e:
            self._json({"ok": False, "error": f"judge: {e}"}, 500)
        except BrokenPipeError:
            pass
        except Exception as e:                                  # noqa: BLE001
            traceback.print_exc(file=sys.stderr)
            self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)

    def _static(self, path: str) -> None:
        rel = "index.html" if path in ("", "/") else path.lstrip("/")
        full = os.path.normpath(os.path.join(STATIC, rel))
        if not full.startswith(STATIC + os.sep) or not os.path.isfile(full):
            raise HttpError(404, "not found")
        with open(full, "rb") as f:
            body = f.read()
        ctype = TYPES.get(os.path.splitext(full)[1], "application/octet-stream")
        self._send(200, body, ctype, [("Cache-Control", "no-cache")])

    def _api(self, op: str) -> None:
        if not op.isidentifier():
            raise HttpError(404, "no such endpoint")
        api: Api = self.server.api                              # type: ignore[attr-defined]
        if self.command == "POST":
            args = self._body()
        else:
            if op not in READS:
                raise HttpError(405, f"{op} needs POST")
            args = dict(parse_qsl(self.path.split("?", 1)[1])) if "?" in self.path else {}
        if op == "run":
            res = api.judge_run(args)
            if args.get("contest"):
                res = api.contest_filter(res)
            with api.lock:
                data = api.record_run(args, res)
        elif op in JUDGING:
            data = api.dispatch(op, args)
        else:
            with api.lock:
                data = api.dispatch(op, args)
        self._json({"ok": True, "data": data})


def lan_addresses() -> list[str]:
    """Where the phone can find this machine: its Bonjour name and its LAN IP(s)."""
    out = []
    try:
        name = socket.gethostname()
        if name and not name.endswith(".local"):
            name = name.split(".")[0] + ".local"
        out.append(name)
    except OSError:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))          # no packet is sent; picks the LAN interface
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            out.append(ip)
    except OSError:
        pass
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="cp.py serve", description="ICPC tutor, in the browser")
    ap.add_argument("--host", default="127.0.0.1",
                    help="interface to bind (default 127.0.0.1; see the security note)")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--open", action="store_true", help="open the browser")
    ap.add_argument("--quiet", action="store_true", help="do not log every request")
    args = ap.parse_args(argv)

    api = Api()
    try:
        c = judge.compiler()
        comp = f"{c['version']}"
    except judge.JudgeError as e:
        comp = f"NONE ({e})"
    errors = loader.load_errors()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.api = api                                             # type: ignore[attr-defined]
    httpd.quiet = args.quiet                                    # type: ignore[attr-defined]
    httpd.daemon_threads = True
    shown = "127.0.0.1" if args.host in ("", "0.0.0.0") else args.host
    url = f"http://{shown}:{args.port}"
    print(f"icpc tutor  ->  {url}")
    print(f"  {len(api.lessons)} lessons, compiler: {comp}")
    print(f"  progress: {api.store.path}")
    for m, e in errors.items():
        print(f"  ! curriculum/{m}.py failed to load: {e.splitlines()[0][:100]}")
    if args.host not in ("127.0.0.1", "localhost"):
        for addr in lan_addresses():
            print(f"  on your phone: http://{addr}:{args.port}")
        print("  ! bound beyond localhost: anyone who can reach this port can run code here.")
    if args.open:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()
    return 0
