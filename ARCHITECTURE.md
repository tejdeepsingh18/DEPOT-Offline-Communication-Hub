# DEPOT — Architecture

## Overview

```
  Phones ──► Wi-Fi "depot" (hostapd, 2.4 GHz WPA2) ──► Raspberry Pi 1 (10.42.0.1)
                                                          ├─ dnsmasq    DHCP + local DNS
                                                          ├─ Flask      :80 http, :443 https
                                                          ├─ SSE        one open stream per tab
                                                          ├─ SQLite     depot.db
                                                          └─ uploads/   files & voice notes
```

Three systemd services bring it all up at boot, in order:
`hostapd-depot` → `dnsmasq-depot` → `depot`. The Pi's own address
(`10.42.0.1/24` on `wlan0`) is assigned by `hostapd-depot.service`, so the network
needs **no cable, laptop or internet** to exist.

## Why these choices

| Decision | Reason |
|---|---|
| **Server-Sent Events**, not WebSockets | A WebSocket library silently failed to fan out to several clients on the Pi 1 (shown with an automated two-client test). SSE over threaded Flask is reliable and simple: server → phone is a stream, phone → server is a normal POST. |
| **SQLite** | One file, no server process, crash-safe; ideal for 512 MB of RAM. |
| **Threads, not async** | Fewer moving parts and lower memory on a single-core board. |
| **Single-file UI** | `index.html` has no build step or dependencies; it loads instantly over Wi-Fi. |
| **Rule-based spam guard** | Scoring rules need no extra packages and cost microseconds per message. |
| **HTTPS on 443 (self-signed)** | Browsers only allow microphone recording on secure pages. Plain http still works. |

## Data model

```sql
messages(id, user, text, ts, kind, meta, token)   -- kind: text | file | voice | sos
users(token, name, health, created, last_ip, last_seen)
```

* `meta` is a JSON blob: file name/size/type, voice duration, or the SOS payload
  (name, IP, health card, note, acks, active).
* `token` is a random id kept in the phone's browser; the **health card** is stored
  against it and only ever sent inside an SOS.
* Files live in `uploads/` as `<random>__<original-name>`.

## HTTP API

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Chat UI |
| GET | `/api/stream?token=&after=` | **SSE** stream: `msg`, `system`, `connected`, `presence`, `sos_update`, `clear` |
| POST | `/api/register` | `{name, health, token?}` → `{token}` (create/update profile) |
| GET | `/api/me?token=` | Own profile (for editing) |
| POST | `/api/send` | `{token, text}` — subject to the spam guard |
| POST | `/api/upload` | multipart: `file`, `token`, `kind=file\|voice`, `duration`, `caption` |
| GET | `/files/<name>` | View inline (images, audio, video, PDF) or download (`?dl=1`) |
| POST | `/api/sos` | `{token, note}` — never throttled (10 s cooldown per person) |
| POST | `/api/sos/ack` | `{token, id}` — "I'm coming" |
| POST | `/api/sos/resolve` | `{token, id}` — sender marks themselves safe |
| GET | `/api/network` | Dashboard data: users, Wi-Fi devices, Pi stats, counts, spam-guard state (CORS-enabled) |
| GET | `/api/status` | Compact status for the presentation site (CORS-enabled) |
| POST | `/api/clear` | Wipe messages and shared files |

## Real-time flow

1. A phone opens `EventSource('/api/stream?token=…&after=<last id>')`.
2. The server registers it, replays anything newer than `after`, sends `connected`,
   and broadcasts a `presence` update to everyone.
3. A POST (message, upload, SOS…) is saved, then broadcast as an event to every
   open stream; each phone draws it once, keyed by message id.
4. If the connection drops the browser reconnects with its last id — no gaps, no duplicates.

## SOS

* Health card fields: blood group, allergies, conditions, medications, emergency
  contact, notes — all optional, set at sign-up, editable by tapping your name.
* `POST /api/sos` creates a message of kind `sos` containing the sender's name, IP,
  note and health card, and broadcasts it.
* Every other phone shows a full-screen flashing alert (plus vibration and a beep
  pattern once the page has had a tap). Phones that join within 30 minutes of an
  active SOS get the alert too.
* Responders send `ack`; the list is shown on the sender's card and alert.
  Only the sender can `resolve`.

## Network monitor

* **In DEPOT**: live list of open streams grouped per person — name, IP, time online.
* **On the Wi-Fi**: every lease in dnsmasq's lease file merged with the kernel's
  neighbour (ARP) table for `wlan0`, marking each device connected or away.
* **Pi health**: uptime, CPU temperature, load, RAM and SD-card usage, message counts.

## Spam guard

Every send attempt earns penalty points that fade after 60 s:

| Rule | Trigger | Points |
|---|---|---|
| Rapid burst | more than 8 messages in 10 s | +2 |
| Repeated message | same or ≥ 90 % similar text, 3× in 60 s | +3 |
| Very long message | over 1,000 characters | +1 |
| Suspicious repetition | one character or word dominates | +2 |
| Upload flood | more than 4 files in 30 s | +2 |

At **5 points** the person is blocked for 30 s, then 60 s, then 120 s for repeat
offences (strikes reset after 5 quiet minutes). The browser shows a countdown and
keeps the typed text; everyone sees a 🛡️ notice. All limits are in `SPAM_RULES` in
`pi/server.py`.

## Installing on a Pi

> Tested on Raspberry Pi OS (32-bit) on a Raspberry Pi 1 with the built-in or a USB Wi-Fi adapter that supports AP mode.

```bash
# on the Pi
sudo apt install hostapd dnsmasq openssl python3-venv
python3 -m venv ~/depot-venv && ~/depot-venv/bin/pip install flask
mkdir -p ~/depot/static ~/depot/uploads ~/depot/tls
# copy from this repo's pi/ folder:
#   server.py, hostapd.conf, dnsmasq-depot.conf  ->  ~/depot/
#   index.html                                   ->  ~/depot/static/
# self-signed certificate (enables in-browser voice recording)
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=depot" \
  -addext "subjectAltName=IP:10.42.0.1,DNS:depot" \
  -keyout ~/depot/tls/key.pem -out ~/depot/tls/cert.pem
# stop NetworkManager from managing the Wi-Fi interface
sudo nmcli dev set wlan0 managed no
# services
sudo cp pi/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl disable --now hostapd dnsmasq 2>/dev/null   # use our own units instead
sudo systemctl enable --now hostapd-depot dnsmasq-depot depot
```

The unit files assume the user **`netpie`** and the folder **`/home/netpie/depot`** —
edit the paths in `pi/systemd/*.service` and the settings at the top of
`pi/server.py` (`DEPOT_BASE` environment variable) if yours differ. Use
`sudo systemctl status depot` and `journalctl -u depot -f` to inspect it.

### Updating a running Pi (Windows)

With the Pi cabled to a Windows laptop (Internet Connection Sharing), double-click
`pi/tools/deploy_pi.bat`. It finds the Pi, **backs up** the running version, installs the
new files, creates the HTTPS certificate if missing, restarts the service and
prints a health check. `rollback_pi.bat` restores the previous version, and
`pi_check.bat` writes a full status report.

## Presentation website

`website/` is a React 19 + Vite single-page site (no UI framework). Its *Open DEPOT*
button and Wi-Fi details come from `website/src/config/depot.js`; the live status panel
polls `http://10.42.0.1/api/status` and falls back to a labelled sample when the Pi is
not reachable.
