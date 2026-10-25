# DEPOT — Demonstration guide

A script for a **6–8 minute live demo**, plus a pre-flight checklist and fixes
for the things that most often go wrong.

## What you need

| Item | Notes |
|---|---|
| Raspberry Pi with DEPOT installed | Powered from a **proper 5 V / 2 A+ supply or power bank**. A weak phone charger causes brown-outs. |
| 2–3 phones | Android or iPhone, any browser. A second phone is essential for the SOS and chat demo. |
| Presenter laptop | Optional but useful: shows the website and the network monitor on the big screen. |
| This repo's `website/` | `cd website && npm install && npm run dev` — open `http://localhost:5173`. |

## Pre-flight checklist (15 minutes before)

1. **Power the Pi** and wait ~60 s. The red LED must be solid; the green LED flickers while booting.
2. On a phone, check that Wi-Fi **`depot`** appears. Join it (password `depot321`).
3. Open **`https://10.42.0.1`** → *Advanced → Proceed* (self-signed certificate; this is needed for the microphone).
4. Sign up on **Phone A** (e.g. "Asha") **with a health card** — blood group, allergy, a medication, a contact.
5. Sign up on **Phone B** (e.g. "Ravi"), also with a health card.
6. Send a test message, a photo and one voice note. Confirm all three arrive on the other phone.
7. Press **🗑 Clear chat** so the demo starts clean.
8. Join the laptop to `depot` too if you want the website's *System information* panel to show **live** values
   (the site must be served over `http`, e.g. `npm run dev`).
9. Mute phone media volume only if you do **not** want the SOS alarm to be audible.

## The script

### 0:00 — The problem (30 s)
> "When there is no internet — a disaster, a trek, a crowded venue — people still need
> to talk, share files and call for help. DEPOT is a Raspberry Pi that creates its own
> network so they can."

Show the **website**: the hero ("Communication without the internet") and the
*Open DEPOT* button.

### 0:30 — Join the network (45 s)
* Hold up the Pi. Point out it is **not connected to the internet** (no Ethernet cable).
* Show Wi-Fi **`depot`** on a phone → join → open the address (button on the website, or type it).
* Say: *"No app, no account, just a browser."*

### 1:15 — Chat, files and voice (90 s)
1. Phone A: type a message → it appears instantly on Phone B.
2. Phone A: tap **📎**, send a photo → inline preview on Phone B.
3. Phone B: send a PDF → tap to download on Phone A.
4. Phone A: tap **🎤**, speak for 5 s, send → Phone B taps ▶ and hears it.
5. Say: *"The Pi pushes every event to every phone over one open connection (Server-Sent Events)."*

### 2:45 — Live network monitor (60 s)
* Tap **📡** on any phone, or show it on the laptop.
* Point at **In DEPOT right now**: display name, **IP** and time online for each person.
* Point at **Devices on the Wi-Fi**: everyone who got an address, and the Pi's own temperature, load, RAM and SD usage.
* Say: *"Everyone can see who is on the network — useful for headcount in a camp or shelter."*

### 3:45 — Emergency SOS (90 s)  ← the highlight
1. Phone B: tap the red **SOS**, type "Near the north gate, trouble breathing", confirm.
2. **Phone A** instantly shows a flashing full-screen alert with **name, IP, note and health card** (and vibrates/beeps).
3. Phone A taps **I'm coming** → Phone B's SOS card now shows *Responding: Asha*.
4. Phone B taps **I'm safe** → the alert turns green on every phone.
5. Say: *"The health card is collected at sign-up and only shown when someone presses SOS."*

### 5:15 — Spam guard (45 s)
* On Phone A, send the same message 4 times quickly (or hold Enter).
* The sender sees **"Slow down — try again in 30 s"** (their text is kept); everyone sees *🛡️ … was throttled*.
* Open **📡** → the **Spam guard** card lists the throttle event and the active rules.
* Say: *"Intelligent rule-based detection — bursts, repeats, floods — with escalating timeouts. No machine learning needed, so it costs almost nothing on a Pi 1. And SOS is never throttled."*

### 6:00 — Under the hood (45 s)
Scroll the website to **Under the hood**: hostapd, dnsmasq, Flask, SSE, SQLite, systemd.
* *"Everything starts by itself at boot — no laptop, no cable, no internet."*
* *"We chose SSE over WebSockets because WebSockets failed to fan out to several clients on the Pi 1 — we measured it."*

### 6:45 — Close (15 s)
Show the **use cases** (disaster relief, treks, fests, classrooms) and end on
*"No internet. No cloud. No dependency."*

## Likely questions

| Question | Answer |
|---|---|
| How far does it reach? | The Wi-Fi range of the Pi — tens of metres, less indoors. It is one hub, not a mesh. |
| Is it secure? | WPA2 password on the Wi-Fi; not end-to-end encrypted. Fine for a group, not for secrets. |
| What if the Pi loses power? | History is in SQLite on the SD card; it comes back at the next boot and the network rebuilds itself. |
| How many users? | A classroom-sized group on a Pi 1; a newer Pi would handle more. |
| Does SOS call anyone? | No — it alerts everyone on the network. |
| Why a Raspberry Pi 1? | Deliberately constrained hardware proves the design is lightweight. |
| Is the spam guard machine learning? | No, rule-based scoring — simple, explainable and cheap. |

## Troubleshooting

| Symptom | Fix |
|---|---|
| `depot` Wi-Fi not visible | Wait 60–90 s after power-up; check the red LED is solid; use a proper supply. |
| Phone says "no internet" and drops the network | Normal on some phones — choose **Stay connected** / **Use as is**. |
| Page won't load | Use `https://10.42.0.1` or `http://10.42.0.1` (not `depot.local`); turn off mobile data / VPN / "Private DNS". |
| 🎤 opens the phone's recorder instead of recording | You are on `http://`. Use `https://10.42.0.1` and accept the warning. |
| Browser blocks the microphone | Allow the microphone permission for the page; tap 🎤 again. |
| Message not sent, orange banner | The spam guard paused you — wait for the countdown. |
| No SOS sound | Phones only play sound after one tap on the page; tap anywhere after joining. Vibration needs a phone that supports it. |
| Website *System information* shows "Sample readout" | The laptop is not on `depot`, or the site is served over https. Sample values are expected then. |
| Everything is stuck | Power-cycle the Pi; services restart automatically. |

## After the demo

* **🗑 Clear chat** wipes messages **and** shared files — do it before handing the Pi to anyone.
* Change the Wi-Fi password in `pi/hostapd.conf` if the device will be used outside a demo.
