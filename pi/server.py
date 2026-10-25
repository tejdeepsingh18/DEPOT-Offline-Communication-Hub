#!/usr/bin/env python3
# =====================================================================
#  DEPOT — offline chat server (v3)
#  Runs on the Raspberry Pi at http://10.42.0.1  (port 80, + 443 if a cert exists)
# =====================================================================
#
# WHAT IS THIS FILE?
#   The "brain" of DEPOT. Whenever someone opens the chat on their phone,
#   this program:
#     1) serves them the chat web-page (HTML + JS)
#     2) stores and relays text messages, files, images and voice notes
#     3) keeps a live list of who is connected (name + IP) for the
#        network dashboard
#     4) relays SOS alerts — with the sender's health card — to everyone
#
# HOW DOES THE "REAL-TIME" PUSH WORK?
#   Server-Sent Events (SSE). The Pi keeps one permanently-open HTTP
#   connection to every phone and "broadcasts" events down it. Phones send
#   things with ordinary HTTP POSTs (/api/send, /api/upload, /api/sos).
#
#   Why SSE and not WebSockets? We tried WebSockets first (flask-sock). On
#   the Pi 1 it silently failed to fan out to multiple clients — proven with
#   an automated 2-client test. SSE + Python threads is rock-solid.
#
# WHY ALSO HTTPS ON PORT 443?
#   Browsers only allow microphone access on "secure" pages (https:// or
#   localhost). Over plain http://10.42.0.1 phones fall back to their own
#   voice-recorder app. If /home/netpie/depot/tls/{cert,key}.pem exist we
#   ALSO serve https://10.42.0.1 so voice notes can be recorded in-app
#   (phones show a one-time "not private" warning for the self-signed cert).
#
# STORAGE
#   depot.db (SQLite)  — messages, user profiles (name + health card)
#   uploads/           — files, images and voice notes
#
# SPAM GUARD (rule-based, no ML — see SpamGuard below)
#   Every message/upload is scored against simple rules (rapid bursts,
#   repeated text, very long or repetitive messages, upload floods). If a
#   person's score over the last minute crosses a threshold they're blocked
#   from sending for 30 s, then 60 s, then 120 s if they keep at it.
#   SOS is NEVER throttled.
# =====================================================================

import collections
import difflib
import json
import mimetypes
import re
import os
import pathlib
import queue
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
import uuid

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from werkzeug.serving import make_server
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------
# Settings — the "knobs" you might want to tweak
# ---------------------------------------------------------------------
BASE = pathlib.Path(os.environ.get("DEPOT_BASE", "/home/netpie/depot"))
DB = BASE / "depot.db"                     # SQLite file (messages + users)
STATIC = BASE / "static"                   # folder with the web UI
UPLOADS = BASE / "uploads"                 # shared files / voice notes
CERT, KEY = BASE / "tls" / "cert.pem", BASE / "tls" / "key.pem"
HTTP_PORT = int(os.environ.get("DEPOT_HTTP_PORT", 80))
HTTPS_PORT = int(os.environ.get("DEPOT_HTTPS_PORT", 443))
SSID = "depot"
WIFI_IFACE = "wlan0"
LEASES = pathlib.Path("/var/lib/misc/dnsmasq.leases")   # who dnsmasq gave IPs to

MAX_HISTORY = 500            # chat lines replayed on refresh
MAX_UPLOAD_MB = 25           # per file — the Pi 1 has a small SD card + 512 MB RAM
MIN_FREE_MB = 200            # refuse uploads if the SD card gets this full
SOS_COOLDOWN_S = 10          # one SOS per person per 10 s (stops accidental spam)
HEALTH_FIELDS = ("blood", "allergies", "conditions", "medications", "contact", "notes")

UPLOADS.mkdir(parents=True, exist_ok=True)

app = Flask("depot", static_folder=str(STATIC), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
STARTED = time.time()

# ---------------------------------------------------------------------
# The "hub" — every currently-open SSE connection
# ---------------------------------------------------------------------
# One entry per open browser tab:  id -> {token, user, ip, since, q}
listeners = {}
seq = [0]
lock = threading.Lock()
last_sos = {}                # token -> time of last SOS (cooldown)

# ---------------------------------------------------------------------
# SQLite helpers
# ---------------------------------------------------------------------
def db():
    """Fresh short-lived connection per call — the safe way with threads."""
    conn = sqlite3.connect(DB, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables on first run, and upgrade an older v2 database in place."""
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS messages (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,  -- auto-numbered
            user TEXT NOT NULL,                      -- display name
            text TEXT NOT NULL,                      -- message text / caption
            ts   REAL NOT NULL                       -- unix time
        )""")
        cols = {r["name"] for r in c.execute("PRAGMA table_info(messages)")}
        # v3 columns: what kind of message it is, and a JSON blob of extras
        # (file name/size, voice duration, SOS health card, ...).
        if "kind" not in cols:
            c.execute("ALTER TABLE messages ADD COLUMN kind TEXT NOT NULL DEFAULT 'text'")
        if "meta" not in cols:
            c.execute("ALTER TABLE messages ADD COLUMN meta TEXT")
        if "token" not in cols:
            c.execute("ALTER TABLE messages ADD COLUMN token TEXT")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            token     TEXT PRIMARY KEY,   -- random id kept in the phone's browser
            name      TEXT NOT NULL,
            health    TEXT,               -- JSON health card (only shown on SOS)
            created   REAL NOT NULL,
            last_ip   TEXT,
            last_seen REAL
        )""")


def row_to_msg(r):
    d = {"id": r["id"], "user": r["user"], "text": r["text"], "ts": r["ts"],
         "kind": r["kind"] or "text"}
    if r["meta"]:
        try:
            d["meta"] = json.loads(r["meta"])
        except ValueError:
            pass
    return d


def push_message(user, text, kind="text", meta=None, token=None):
    """Save a message and return it (with its new id) as a dict."""
    ts = time.time()
    with db() as c:
        cur = c.execute(
            "INSERT INTO messages (user, text, ts, kind, meta, token) VALUES (?,?,?,?,?,?)",
            (user, text, ts, kind, json.dumps(meta) if meta is not None else None, token))
        row = c.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_msg(row)


def get_message(mid):
    with db() as c:
        row = c.execute("SELECT * FROM messages WHERE id=?", (mid,)).fetchone()
    return row_to_msg(row) if row else None


def update_meta(mid, meta):
    with db() as c:
        c.execute("UPDATE messages SET meta=? WHERE id=?", (json.dumps(meta), mid))


def get_history(limit=MAX_HISTORY, after_id=0):
    """The NEWEST <limit> messages after <after_id>, oldest first."""
    with db() as c:
        rows = c.execute(
            "SELECT * FROM (SELECT * FROM messages WHERE id > ? "
            "ORDER BY id DESC LIMIT ?) ORDER BY id ASC", (after_id, limit)).fetchall()
    return [row_to_msg(r) for r in rows]


def get_user(token):
    if not token:
        return None
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    if not row:
        return None
    u = dict(row)
    u["health"] = json.loads(u["health"]) if u["health"] else {}
    return u


def touch_user(token, ip):
    with db() as c:
        c.execute("UPDATE users SET last_ip=?, last_seen=? WHERE token=?",
                  (ip, time.time(), token))


def who(data):
    """Work out (token, display name) for a request. Old clients that only
    send {"user": name} still work — they just have no profile."""
    token = str(data.get("token") or "")[:64]
    u = get_user(token)
    if u:
        return token, u["name"]
    return None, (str(data.get("user") or "")[:20].strip() or "anon")


def client_ip():
    return request.remote_addr or "?"

# ---------------------------------------------------------------------
# SSE hub — register / unregister / broadcast
# ---------------------------------------------------------------------
def presence():
    """Everyone with at least one open tab, grouped per person."""
    with lock:
        entries = list(listeners.values())
    people = {}
    for e in entries:
        key = e["token"] or f"anon:{e['user']}:{e['ip']}"
        p = people.setdefault(key, {"name": e["user"], "ip": e["ip"],
                                    "since": e["since"], "tabs": 0,
                                    "profile": bool(e["token"])})
        p["tabs"] += 1
        p["since"] = min(p["since"], e["since"])
        p["ip"] = e["ip"]
    return sorted(people.values(), key=lambda p: p["since"])


def _sessions_for(token, user, ip):
    with lock:
        return sum(1 for e in listeners.values()
                   if (e["token"] == token if token else
                       (e["user"], e["ip"]) == (user, ip)))


def register(token, user, ip):
    q = queue.Queue(maxsize=500)
    with lock:
        seq[0] += 1
        cid = seq[0]
        listeners[cid] = {"token": token, "user": user, "ip": ip,
                          "since": time.time(), "q": q}
    if token:
        touch_user(token, ip)
    # Only announce a JOIN for a person's first tab — reconnects stay quiet.
    if _sessions_for(token, user, ip) == 1:
        broadcast({"type": "system", "text": f"{user} joined", "ts": time.time()},
                  exclude=cid)
    broadcast({"type": "presence", "users": presence()})
    return cid, q


def unregister(cid):
    with lock:
        e = listeners.pop(cid, None)
    if not e:
        return
    if _sessions_for(e["token"], e["user"], e["ip"]) == 0:
        broadcast({"type": "system", "text": f"{e['user']} left", "ts": time.time()})
    broadcast({"type": "presence", "users": presence()})


def broadcast(payload, exclude=None):
    data = json.dumps(payload)
    with lock:
        targets = [e["q"] for cid, e in listeners.items() if cid != exclude]
    for q in targets:
        try:
            q.put_nowait(data)
        except queue.Full:
            pass                       # a stuck client just misses this one


@app.route("/api/stream")
def stream():
    """One permanently-open 'radio channel' per browser tab."""
    token = request.args.get("token", "")[:64]
    u = get_user(token)
    user = u["name"] if u else (request.args.get("user", "")[:20] or "anon")
    if not u:
        token = None
    ip = client_ip()
    try:
        after = max(0, int(request.args.get("after", 0)))
    except ValueError:
        after = 0

    def gen():
        cid, q = register(token, user, ip)
        try:
            for m in get_history(after_id=after):            # catch-up first
                yield f"data: {json.dumps({'type': 'msg', **m})}\n\n"
            yield f"data: {json.dumps({'type': 'connected', 'ts': time.time(), 'ip': ip, 'users': presence()})}\n\n"
            while True:
                try:
                    yield f"data: {q.get(timeout=20)}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            unregister(cid)

    resp = Response(gen(), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache, no-store"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp

# ---------------------------------------------------------------------
# Sign-up / profile (name + optional health card)
# ---------------------------------------------------------------------
def clean_health(h):
    h = h if isinstance(h, dict) else {}
    return {k: str(h.get(k, "") or "")[:200].strip() for k in HEALTH_FIELDS}


@app.route("/api/register", methods=["POST"])
def register_user():
    """Create (or update) a profile. Returns the token the browser keeps."""
    data = request.get_json(force=True, silent=True) or {}
    name = str(data.get("name", "")).strip()[:20]
    if not name:
        return {"ok": False, "error": "name required"}, 400
    health = clean_health(data.get("health"))
    token = str(data.get("token") or "")[:64]
    now = time.time()
    with db() as c:
        exists = token and c.execute("SELECT 1 FROM users WHERE token=?", (token,)).fetchone()
        if exists:
            c.execute("UPDATE users SET name=?, health=?, last_ip=?, last_seen=? WHERE token=?",
                      (name, json.dumps(health), client_ip(), now, token))
        else:
            token = uuid.uuid4().hex
            c.execute("INSERT INTO users (token, name, health, created, last_ip, last_seen) "
                      "VALUES (?,?,?,?,?,?)",
                      (token, name, json.dumps(health), now, client_ip(), now))
    return {"ok": True, "token": token, "name": name, "health": health}


@app.route("/api/me")
def me():
    u = get_user(request.args.get("token", ""))
    if not u:
        return {"ok": False}, 404
    return {"ok": True, "name": u["name"], "health": u["health"], "ip": client_ip()}

# ---------------------------------------------------------------------
# Spam guard — "intelligent rule-based detection", deliberately not ML
# ---------------------------------------------------------------------
# Think of it as a referee with a notebook. For every person it keeps the
# last minute of what they sent. Each new message earns "penalty points" for
# looking spammy; points older than a minute fade away. Too many points at
# once → a timeout that grows each time they re-offend.
#
# Cost on the Pi 1: a few list operations per message, a few KB of RAM.
SPAM_RULES = {
    "burst_count": 8,        # more than 8 messages ...
    "burst_window": 10,      # ... within 10 s                  → +2 each
    "repeat_count": 3,       # same / near-identical text 3+ times
    "repeat_window": 60,     # ... within 60 s                  → +3 each
    "repeat_similarity": 0.9,
    "long_chars": 1000,      # message longer than this         → +1
    "upload_count": 4,       # more than 4 files ...
    "upload_window": 30,     # ... within 30 s                  → +2 each
    "score_window": 60,      # penalty points count for 60 s
    "threshold": 5,          # this many points → throttled
    "block_base": 30,        # first timeout (s); doubles each strike ...
    "block_max": 120,        # ... up to this
    "strike_reset": 300,     # behave for 5 min and strikes reset
}

_REASON_TEXT = {
    "burst": "rapid burst", "repeat": "repeated message", "long": "very long message",
    "repetitive": "suspicious repetition", "upload_flood": "too many uploads",
}


def _normalise(text):
    t = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", t).strip()[:300]


def _is_repetitive(text):
    """'aaaaaaaaaa', 'lol lol lol lol lol lol', '!!!!!!!!!!!!' and friends."""
    compact = re.sub(r"\s", "", text)
    if len(compact) < 12:
        return False
    if re.search(r"(.)\1{9,}", compact):                       # 10+ same char in a row
        return True
    top = collections.Counter(compact).most_common(1)[0][1]
    if top / len(compact) > 0.6:                                # one char dominates
        return True
    words = text.lower().split()
    return len(words) >= 6 and len(set(words)) / len(words) < 0.3   # few distinct words


class SpamGuard:
    def __init__(self, rules):
        self.r = rules
        self.lock = threading.Lock()
        self.people = {}                                   # key -> state
        self.events = collections.deque(maxlen=20)         # recent throttles (dashboard)
        self.flagged = 0                                   # messages that scored > 0

    def _state(self, key):
        return self.people.setdefault(key, {
            "msgs": collections.deque(maxlen=30),     # (ts, normalised text)
            "uploads": collections.deque(maxlen=30),  # ts
            "points": collections.deque(),            # (ts, points, reason)
            "blocked_until": 0.0, "strikes": 0, "last_strike": 0.0,
            "reasons": [], "name": "", "ip": "",
        })

    def blocked_for(self, key, now=None):
        now = now or time.time()
        with self.lock:
            st = self.people.get(key)
            return max(0.0, st["blocked_until"] - now) if st else 0.0

    def check(self, key, name, ip, text=None, upload=False):
        """Score one send attempt. Returns (allowed, retry_after_s, reasons)."""
        r, now = self.r, time.time()
        with self.lock:
            st = self._state(key)
            st["name"], st["ip"] = name, ip
            if st["blocked_until"] > now:
                return False, st["blocked_until"] - now, st["reasons"]

            hits = []
            if upload:
                st["uploads"].append(now)
                recent = [t for t in st["uploads"] if now - t <= r["upload_window"]]
                if len(recent) > r["upload_count"]:
                    hits.append(("upload_flood", 2))
            else:
                norm = _normalise(text)
                recent = [m for m in st["msgs"] if now - m[0] <= r["burst_window"]]
                if len(recent) + 1 > r["burst_count"]:
                    hits.append(("burst", 2))
                if norm:
                    same = 1
                    for ts, prev in st["msgs"]:
                        if now - ts > r["repeat_window"] or not prev:
                            continue
                        sm = difflib.SequenceMatcher(None, norm, prev)
                        if (prev == norm or (sm.real_quick_ratio() >= r["repeat_similarity"]
                                             and sm.quick_ratio() >= r["repeat_similarity"]
                                             and sm.ratio() >= r["repeat_similarity"])):
                            same += 1
                    if same >= r["repeat_count"]:
                        hits.append(("repeat", 3))
                if len(text) > r["long_chars"]:
                    hits.append(("long", 1))
                if _is_repetitive(text):
                    hits.append(("repetitive", 2))
                st["msgs"].append((now, norm))

            pts = st["points"]
            for reason, p in hits:
                pts.append((now, p, reason))
            while pts and now - pts[0][0] > r["score_window"]:
                pts.popleft()
            if hits:
                self.flagged += 1
            score = sum(p for _, p, _ in pts)
            if score < r["threshold"]:
                return True, 0.0, []

            # ---- over the line: throttle, escalating per strike ----
            if now - st["last_strike"] > r["strike_reset"]:
                st["strikes"] = 0
            st["strikes"] += 1
            st["last_strike"] = now
            block = min(r["block_base"] * 2 ** (st["strikes"] - 1), r["block_max"])
            st["blocked_until"] = now + block
            reasons = sorted({_REASON_TEXT[rs] for _, _, rs in pts},
                             key=lambda x: -sum(p for _, p, rs in pts if _REASON_TEXT[rs] == x))
            st["reasons"] = reasons
            pts.clear()
            self.events.appendleft({"name": name, "ip": ip, "ts": now, "seconds": block,
                                    "strike": st["strikes"], "reasons": reasons, "score": score})
        broadcast({"type": "system", "ts": now,
                   "text": f"🛡️ {name} was throttled for {block} s ({', '.join(reasons)})"})
        return False, float(block), reasons

    def status(self):
        now = time.time()
        with self.lock:
            active = [{"name": st["name"], "ip": st["ip"], "reasons": st["reasons"],
                       "remaining": round(st["blocked_until"] - now), "strikes": st["strikes"]}
                      for st in self.people.values() if st["blocked_until"] > now]
            return {"rules": self.r, "throttled": active,
                    "events": list(self.events), "flagged": self.flagged}

    def reset(self):
        with self.lock:
            self.people.clear(); self.events.clear(); self.flagged = 0


guard = SpamGuard(SPAM_RULES)


def spam_key(token):
    return token or f"ip:{client_ip()}"


def throttled_response(retry, reasons):
    secs = int(retry + 0.999)
    resp = jsonify({"ok": False, "error": "spam", "retry_after": secs, "reasons": reasons})
    resp.status_code = 429
    resp.headers["Retry-After"] = str(secs)
    return resp

# ---------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------
@app.route("/api/send", methods=["POST"])
def send_msg():
    data = request.get_json(force=True, silent=True) or {}
    token, user = who(data)
    text = str(data.get("text", ""))[:2000].strip()
    if not text:
        return {"ok": False, "error": "empty"}, 400
    ok, retry, reasons = guard.check(spam_key(token), user, client_ip(), text=text)
    if not ok:
        return throttled_response(retry, reasons)
    m = push_message(user, text, token=token)
    broadcast({"type": "msg", **m})
    return {"ok": True, **m}


@app.route("/api/clear", methods=["POST"])
def clear_chat():
    """Wipe all messages AND shared files, and blank every screen."""
    with db() as c:
        c.execute("DELETE FROM messages")
    for f in UPLOADS.iterdir():
        try:
            f.unlink()
        except OSError:
            pass
    guard.reset()
    broadcast({"type": "clear", "ts": time.time()})
    return jsonify({"ok": True, "ts": time.time()})

# ---------------------------------------------------------------------
# Files, images & voice notes
# ---------------------------------------------------------------------
INLINE_TYPES = ("image/", "audio/", "video/", "text/plain", "application/pdf")


@app.route("/api/upload", methods=["POST"])
def upload():
    """multipart/form-data: file=<blob>, token=..., kind=file|voice,
    duration=<seconds, voice only>, caption=<optional text>"""
    # Cheap check BEFORE reading the upload body: is this person in a timeout?
    early = request.args.get("token", "")[:64]
    if early and guard.blocked_for(early):
        return throttled_response(guard.blocked_for(early), ["slow down"])
    f = request.files.get("file")
    if not f or not f.filename:
        return {"ok": False, "error": "no file"}, 400
    if shutil.disk_usage(UPLOADS).free < MIN_FREE_MB * 1024 * 1024:
        return {"ok": False, "error": "Pi storage is full"}, 507
    token, user = who(request.form)
    ok, retry, reasons = guard.check(spam_key(token), user, client_ip(), upload=True)
    if not ok:
        return throttled_response(retry, reasons)
    kind = "voice" if request.form.get("kind") == "voice" else "file"
    orig = os.path.basename(f.filename)[:120] or "file"
    safe = secure_filename(orig) or "file"
    stored = f"{uuid.uuid4().hex[:12]}__{safe}"
    path = UPLOADS / stored
    f.save(path)
    size = path.stat().st_size
    mime = (f.mimetype if f.mimetype and f.mimetype != "application/octet-stream"
            else mimetypes.guess_type(orig)[0]) or "application/octet-stream"
    meta = {"file": stored, "name": orig, "size": size, "mime": mime}
    if kind == "voice":
        try:
            meta["duration"] = round(min(float(request.form.get("duration", 0)), 3600), 1)
        except ValueError:
            meta["duration"] = 0
    caption = str(request.form.get("caption", ""))[:500].strip()
    m = push_message(user, caption, kind=kind, meta=meta, token=token)
    broadcast({"type": "msg", **m})
    return {"ok": True, **m}


@app.route("/files/<path:stored>")
def get_file(stored):
    stored = os.path.basename(stored)
    if not (UPLOADS / stored).is_file():
        abort(404)
    name = stored.split("__", 1)[-1]
    mime = mimetypes.guess_type(name)[0] or ""
    inline = request.args.get("dl") != "1" and mime.startswith(INLINE_TYPES)
    try:
        return send_from_directory(UPLOADS, stored, as_attachment=not inline,
                                   download_name=name, conditional=True, max_age=86400)
    except TypeError:                     # Flask < 2.0 on an older Pi image
        return send_from_directory(UPLOADS, stored, as_attachment=not inline,
                                   attachment_filename=name, conditional=True)


@app.errorhandler(413)
def too_big(_e):
    return {"ok": False, "error": f"file too large (max {MAX_UPLOAD_MB} MB)"}, 413

# ---------------------------------------------------------------------
# SOS — emergency broadcast with the sender's health card
# ---------------------------------------------------------------------
@app.route("/api/sos", methods=["POST"])
def sos():
    data = request.get_json(force=True, silent=True) or {}
    token, user = who(data)
    key = token or client_ip()
    now = time.time()
    if now - last_sos.get(key, 0) < SOS_COOLDOWN_S:
        return {"ok": False, "error": "SOS already sent — wait a few seconds"}, 429
    last_sos[key] = now
    u = get_user(token) if token else None
    meta = {
        "name": user,
        "ip": client_ip(),
        "health": (u or {}).get("health") or {},
        "note": str(data.get("note", ""))[:300].strip(),
        "active": True,
        "acks": [],
    }
    m = push_message(user, f"SOS from {user}", kind="sos", meta=meta, token=token)
    broadcast({"type": "msg", **m})
    return {"ok": True, **m}


def _sos_change(mutator):
    data = request.get_json(force=True, silent=True) or {}
    token, user = who(data)
    try:
        mid = int(data.get("id"))
    except (TypeError, ValueError):
        return {"ok": False, "error": "bad id"}, 400
    m = get_message(mid)
    if not m or m["kind"] != "sos":
        return {"ok": False, "error": "no such SOS"}, 404
    err = mutator(m, token, user)
    if err:
        return {"ok": False, "error": err}, 403
    update_meta(mid, m["meta"])
    broadcast({"type": "sos_update", "id": mid, "meta": m["meta"]})
    return {"ok": True, "id": mid, "meta": m["meta"]}


@app.route("/api/sos/ack", methods=["POST"])
def sos_ack():
    """'I'm coming' — tells the person in trouble (and everyone) who responds."""
    def ack(m, token, user):
        if user not in m["meta"]["acks"]:
            m["meta"]["acks"].append(user)
    return _sos_change(ack)


@app.route("/api/sos/resolve", methods=["POST"])
def sos_resolve():
    """Only the person who raised the SOS can mark themselves safe."""
    def resolve(m, token, user):
        with db() as c:
            owner = c.execute("SELECT token FROM messages WHERE id=?", (m["id"],)).fetchone()[0]
        if owner and owner != token:
            return "only the sender can cancel this SOS"
        m["meta"]["active"] = False
        m["meta"]["resolved_ts"] = time.time()
    return _sos_change(resolve)

# ---------------------------------------------------------------------
# Live network monitor
# ---------------------------------------------------------------------
def _read(path, default=""):
    try:
        return pathlib.Path(path).read_text().strip()
    except OSError:
        return default


def pi_stats():
    up = _read("/proc/uptime", "0").split()[0]
    temp = _read("/sys/class/thermal/thermal_zone0/temp")
    mem = {}
    for line in _read("/proc/meminfo").splitlines():
        k, _, v = line.partition(":")
        mem[k] = int(v.split()[0]) if v.split() else 0
    disk = shutil.disk_usage(BASE)
    try:
        load = os.getloadavg()[0]
    except OSError:
        load = 0.0
    return {
        "hostname": socket.gethostname(),
        "ssid": SSID,
        "ip": "10.42.0.1",
        "uptime": float(up or 0),
        "server_uptime": time.time() - STARTED,
        "temp_c": round(int(temp) / 1000, 1) if temp.isdigit() else None,
        "load": round(load, 2),
        "mem_used_mb": round((mem.get("MemTotal", 0) - mem.get("MemAvailable", 0)) / 1024),
        "mem_total_mb": round(mem.get("MemTotal", 0) / 1024),
        "disk_used_gb": round(disk.used / 1e9, 2),
        "disk_total_gb": round(disk.total / 1e9, 2),
    }


def wifi_devices():
    """Every device that got an IP on the depot Wi-Fi (dnsmasq leases),
    marked live if the Pi has heard from it recently (kernel ARP table)."""
    neigh = {}
    try:
        out = subprocess.run(["ip", "neigh", "show", "dev", WIFI_IFACE],
                             capture_output=True, text=True, timeout=3).stdout
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0].count(".") == 3:          # IPv4 only
                neigh[parts[0]] = parts[-1]           # ip -> REACHABLE/STALE/FAILED...
    except (OSError, subprocess.SubprocessError):
        pass
    devices = {}
    for line in _read(LEASES).splitlines():
        parts = line.split()
        if len(parts) >= 4:
            _exp, mac, ip, host = parts[:4]
            devices[ip] = {"ip": ip, "mac": mac, "hostname": "" if host == "*" else host}
    for ip, state in neigh.items():
        devices.setdefault(ip, {"ip": ip, "mac": "", "hostname": ""})
    for ip, d in devices.items():
        st = neigh.get(ip, "")
        d["state"] = st or "UNKNOWN"
        d["live"] = st in ("REACHABLE", "STALE", "DELAY", "PROBE", "PERMANENT")
    return sorted(devices.values(), key=lambda d: tuple(int(x) for x in d["ip"].split(".")
                                                        if x.isdigit()))


@app.route("/api/network")
def network():
    users = presence()
    chat_ips = {u["ip"] for u in users}
    wifi = wifi_devices()
    for d in wifi:
        d["in_chat"] = d["ip"] in chat_ips
    with db() as c:
        counts = dict(c.execute(
            "SELECT COUNT(*) total, "
            "SUM(kind='file') files, SUM(kind='voice') voice, SUM(kind='sos') sos "
            "FROM messages").fetchone())
    spam = guard.status()
    blocked = {(t["name"], t["ip"]): t["remaining"] for t in spam["throttled"]}
    for u in users:
        u["throttled"] = blocked.get((u["name"], u["ip"]), 0)
    return {"ok": True, "ts": time.time(), "pi": pi_stats(), "users": users,
            "wifi": wifi, "counts": {k: v or 0 for k, v in counts.items()}, "spam": spam}


@app.route("/api/status")
def status():
    """Compact summary in the shape the DEPOT presentation website expects."""
    p = pi_stats()
    users = presence()
    return {
        "network": {"label": "LOCAL", "state": "ACTIVE", "ssid": SSID},
        "connectedDevices": len(users),
        "storage": {"usedGb": round(p["disk_used_gb"], 1), "totalGb": round(p["disk_total_gb"], 1)},
        "server": {"label": "RUNNING", "state": "running"},
        "uptimeSeconds": int(p["uptime"]),
    }


@app.after_request
def cors_for_readonly(resp):
    # The presentation website (served from elsewhere) may read these two.
    if request.path in ("/api/status", "/api/network"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp

# ---------------------------------------------------------------------
# Static routes — the chat web page
# ---------------------------------------------------------------------
@app.route("/")
def index():
    resp = send_from_directory(STATIC, "index.html")
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@app.route("/favicon.ico")
def favicon():
    return ("", 204)


@app.route("/<path:fname>")
def static_(fname):
    return send_from_directory(STATIC, fname)

# ---------------------------------------------------------------------
# Boot!
# ---------------------------------------------------------------------
init_db()


def serve():
    servers = [make_server("0.0.0.0", HTTP_PORT, app, threaded=True)]
    if CERT.exists() and KEY.exists():
        try:
            servers.append(make_server("0.0.0.0", HTTPS_PORT, app, threaded=True,
                                       ssl_context=(str(CERT), str(KEY))))
        except (OSError, ValueError) as e:
            print(f"[depot] https disabled: {e}")
    for s in servers[1:]:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    print(f"[depot] server ready → http://10.42.0.1"
          + (" + https://10.42.0.1" if len(servers) > 1 else "") + f"  (SSID: {SSID})",
          flush=True)
    servers[0].serve_forever()


if __name__ == "__main__":
    serve()
