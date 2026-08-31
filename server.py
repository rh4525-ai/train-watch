"""열차 좌석 감시 서비스의 안전한 작업 관리 API 골격.

실제 철도사 연동 전 단계입니다. 자격증명과 결제정보는 저장하지 않습니다.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import uuid
import os
import threading
import time
import smtplib
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime, timezone

JOBS = {}
JOB_EVENTS = {}
ROOT = Path(__file__).resolve().parent

def now():
    return datetime.now(timezone.utc).isoformat()

def send_notifications(payload):
    message = payload.get("message", "열차 감시 알림")
    sent = []
    errors = []
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = payload.get("telegram_target")
    if bot_token and chat_id:
        try:
            body = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
            request = urllib.request.Request(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=body)
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    sent.append("telegram")
        except Exception as exc:
            errors.append(f"telegram: {exc.__class__.__name__}")

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    email_target = payload.get("email_target")
    if smtp_host and smtp_user and smtp_password and email_target:
        try:
            mail = EmailMessage()
            mail["Subject"] = payload.get("subject", "열차 좌석 감시 알림")
            mail["From"] = smtp_user
            mail["To"] = email_target
            mail.set_content(message)
            with smtplib.SMTP_SSL(os.environ.get("SMTP_PORT", "465"), timeout=10) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(mail)
            sent.append("email")
        except Exception as exc:
            errors.append(f"email: {exc.__class__.__name__}")
    return {"sent": sent, "errors": errors}

def watch_job(job_id):
    event = JOB_EVENTS[job_id]
    while not event.wait(JOBS[job_id]["interval_seconds"]):
        job = JOBS.get(job_id)
        if not job:
            return
        job["check_count"] += 1
        job["last_checked_at"] = now()
        # 실제 잔여좌석 조회 어댑터는 공식 연동 확인 후 이 위치에 연결합니다.

class Handler(BaseHTTPRequestHandler):
    def reply(self, code, body):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/health":
            return self.reply(200, {"ok": True, "service": "train-watch", "time": now(), "korail_key_configured": bool(os.environ.get("KORAIL_SERVICE_KEY"))})
        if self.path == "/api/jobs":
            return self.reply(200, {"jobs": list(JOBS.values())})
        if self.path.startswith("/api/jobs/"):
            job = JOBS.get(self.path[len("/api/jobs/"):])
            return self.reply(200, job) if job else self.reply(404, {"error": "job_not_found"})
        if self.path == "/api/notify/configured":
            return self.reply(200, {"telegram": bool(os.environ.get("TELEGRAM_BOT_TOKEN")), "email": bool(os.environ.get("SMTP_HOST"))})
        if self.path in ("/", "/index.html"):
            return self.static("index.html", "text/html; charset=utf-8")
        if self.path == "/styles.css":
            return self.static("styles.css", "text/css; charset=utf-8")
        if self.path == "/app.js":
            return self.static("app.js", "application/javascript; charset=utf-8")
        return self.reply(404, {"error": "not_found"})

    def static(self, filename, content_type):
        try:
            data = (ROOT / filename).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except OSError:
            self.reply(404, {"error": "file_not_found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.reply(400, {"error": "invalid_json"})

        if self.path == "/api/jobs":
            required = ["departure_station", "arrival_station", "departure_date"]
            if any(not payload.get(key) for key in required):
                return self.reply(400, {"error": "missing_search_condition"})
            job_id = str(uuid.uuid4())
            job = {
                "id": job_id,
                "departure_station": payload["departure_station"],
                "arrival_station": payload["arrival_station"],
                "departure_date": payload["departure_date"],
                "interval_seconds": max(10, int(payload.get("interval_seconds", 10))),
                "any_seat": bool(payload.get("any_seat", True)),
                "status": "queued",
                "last_checked_at": None,
                "check_count": 0,
                "last_error": None,
                "created_at": now(),
            }
            JOBS[job_id] = job
            JOB_EVENTS[job_id] = threading.Event()
            threading.Thread(target=watch_job, args=(job_id,), daemon=True).start()
            return self.reply(201, job)
        if self.path == "/api/notify/test":
            result = send_notifications({
                "message": payload.get("message", "열차 감시 테스트 알림입니다."),
                "telegram_target": payload.get("telegram_target"),
                "email_target": payload.get("email_target"),
                "subject": "열차 감시 테스트 알림",
            })
            if not result["sent"] and result["errors"]:
                return self.reply(502, result)
            return self.reply(200, result)
        return self.reply(404, {"error": "not_found"})

    def do_DELETE(self):
        prefix = "/api/jobs/"
        if self.path.startswith(prefix):
            job_id = self.path[len(prefix):]
            if JOBS.pop(job_id, None):
                if job_id in JOB_EVENTS:
                    JOB_EVENTS[job_id].set()
                    JOB_EVENTS.pop(job_id, None)
                return self.reply(200, {"deleted": True})
            return self.reply(404, {"error": "job_not_found"})
        return self.reply(404, {"error": "not_found"})

    def log_message(self, *_):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"Train Watch: http://0.0.0.0:{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
