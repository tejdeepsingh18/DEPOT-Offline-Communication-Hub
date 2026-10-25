# DEPOT — Decentralized Exchange Portal for Offline Transmission

Presentation website for **DEPOT**: a Raspberry Pi that becomes the Wi-Fi network,
web server, database and router, so a group of phones can chat, share files, send
voice notes and raise an SOS with no internet.

- **Open the live system:** join Wi-Fi `depot` (password `depot321`) → **http://10.42.0.1**
  (the "Open DEPOT" button on this site goes there)
- Pi code: <https://github.com/tejdeepsingh18/DEPOT-Offline-Communication-Hub>

## Run the site

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # static build in dist/
```

The *System information* panel polls `http://10.42.0.1/api/status`. It shows live
values when the presenting laptop is on the `depot` Wi-Fi and the site is served
over **http** (e.g. `npm run dev`); otherwise it shows a sample snapshot.
The Pi's address and Wi-Fi details live in `src/config/depot.js`.
