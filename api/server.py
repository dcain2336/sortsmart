"""SortSmart Business Advisor — REST API + demo UI server (stdlib only).

Endpoints:
  GET  /api/health          -> {"ok": true, "model": "..."}
  POST /api/ask             -> {"question": str, ...} => advisor answer + grounded data
  POST /api/brief           -> business profile JSON => full business brief
  GET  /                    -> demo UI

Run:  python3 -m api.server  (or: python3 api/server.py)
Env:  LLM_BASE_URL, LLM_API_KEY, LLM_MODEL  (or LLM_MOCK=true)
"""
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sortsmart_llm import BusinessAdvisor, LLMError  # noqa: E402
from sortsmart_business import business_brief  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(os.path.dirname(HERE), "ui")

_advisor = None


def get_advisor():
    global _advisor
    if _advisor is None:
        _advisor = BusinessAdvisor()
    return _advisor


class Handler(BaseHTTPRequestHandler):
    server_version = "SortSmartBusiness/1.0"

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            try:
                adv = get_advisor()
                self._send_json({"ok": True, "model": repr(adv.llm)})
            except LLMError as e:
                self._send_json({"ok": False, "error": str(e)}, status=503)
            return
        if path in ("/", "/index.html"):
            fpath = os.path.join(UI_DIR, "index.html")
            if os.path.exists(fpath):
                with open(fpath, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/ask":
            data = self._read_json()
            question = (data.get("question") or "").strip()
            if not question:
                self._send_json({"error": "question is required"}, status=400)
                return
            try:
                adv = get_advisor()
                result = adv.ask(
                    question,
                    business_type=data.get("business_type"),
                    monthly_shipments=data.get("monthly_shipments"),
                    packaging=data.get("packaging", "poly_mailer"),
                )
                self._send_json(result)
            except LLMError as e:
                self._send_json({"error": str(e)}, status=502)
            except Exception as e:  # fail safe, never leak tracebacks
                self._send_json({"error": f"advisor failed: {type(e).__name__}"}, status=500)
            return
        if path == "/api/brief":
            data = self._read_json()
            try:
                brief = business_brief(
                    business_type=data.get("business_type", "retail"),
                    monthly_shipments=int(data.get("monthly_shipments", 0) or 0),
                    packaging=data.get("packaging", "poly_mailer"),
                    diversion_rate_pct=float(data.get("diversion_rate_pct", 25) or 25),
                    composts_food=bool(data.get("composts_food", False)),
                    ewaste_program=bool(data.get("ewaste_program", False)),
                    hazmat_program=bool(data.get("hazmat_program", False)),
                )
                self._send_json(brief)
            except (ValueError, TypeError) as e:
                self._send_json({"error": str(e)}, status=400)
            return
        self._send_json({"error": "not found"}, status=404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("[api] " + fmt % args + "\n")


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"SortSmart Business Advisor on http://127.0.0.1:{port}/")
    try:
        adv = get_advisor()
        print(f"LLM backend: {adv.llm}")
    except LLMError as e:
        print(f"WARNING: {e}")
    server.serve_forever()


if __name__ == "__main__":
    main()
