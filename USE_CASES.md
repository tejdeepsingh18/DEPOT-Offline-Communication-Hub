# DEPOT — Use cases

DEPOT is useful wherever **a group of people are physically close, need to
coordinate, and cannot rely on the internet or mobile networks.** One Pi, one
power bank, nothing to install.

## At a glance

| # | Scenario | Why internet fails | DEPOT features used |
|---|---|---|---|
| 1 | Disaster relief & emergency response | Towers down or overloaded | SOS, chat, files, network monitor |
| 2 | Treks, camps & expeditions | No coverage in the wilderness | SOS + health cards, voice notes, photos |
| 3 | College fests, exhibitions & hackathons | Venue Wi-Fi congested, mobile data saturated | Chat, file sharing, network monitor |
| 4 | Classrooms & labs without internet | Restricted or no connectivity | File sharing, chat, spam guard |
| 5 | Convoys, road trips & events on the move | Highways, tunnels, hills | Voice notes, chat, SOS |
| 6 | Remote worksites & field research | Mines, farms, sites, islands | Files, photos, status, SOS |
| 7 | Privacy-sensitive local sharing | Nothing should leave the room | Everything stays on the Pi |

---

## 1. Disaster relief & emergency response

**Situation.** After a flood, earthquake or storm, cell towers are down or jammed.
Volunteers and affected people are in one shelter or relief camp.

**With DEPOT.** A Pi on a power bank (or a vehicle charger) makes a local network.
Volunteers coordinate by chat and voice note, share photos of damage and
supply lists as files, and the **network monitor** shows how many devices are
present. Anyone who is hurt or needs help hits **SOS**: every phone shows their name,
IP, a note and their **health card** (blood group, allergies, medications), and
responders tap **"I'm coming"** so the person knows help is on the way.

**Why it fits.** Zero infrastructure, powered from a power bank, and works with
whatever phones people already have.

## 2. Treks, camps and expeditions

**Situation.** A group spreads out over a campsite or a trail section with no signal.

**With DEPOT.** Keep the Pi at the base camp or in the lead vehicle. Group members
send **voice notes** (easier than typing with gloves on), share photos, and share
route information. The sign-up **health card** means that if someone is injured,
whoever responds immediately sees allergies and medical conditions.

**Note.** Range is limited to the Wi-Fi coverage around the Pi — suited to a camp,
not a long trail.

## 3. College fests, exhibitions and hackathons

**Situation.** Thousands of phones overload the venue network; organisers cannot
reach volunteers reliably.

**With DEPOT.** A stall or control room runs its own network. Volunteers get
instant chat, schedules and posters as files, and the **network monitor** shows who
is online. The **spam guard** keeps a busy public channel usable by throttling
floods and copy-paste spam automatically. It is also a strong live demo of
networking, embedded Linux and web engineering in one device.

## 4. Classrooms and labs without internet

**Situation.** A rural school or a lab with restricted access wants to share
material and let students ask questions.

**With DEPOT.** The teacher drops PDFs, notes and photos of the board into the
chat; students download them over Wi-Fi. Questions go into the chat; the spam
guard prevents disruption. All history stays on the Pi for the next session.

## 5. Convoys, road trips and events on the move

**Situation.** A group of vehicles or a procession passes through areas with
patchy coverage.

**With DEPOT.** A Pi in the lead vehicle (or a central point at a stop) lets
everyone in range send voice notes, share photos and raise an SOS if there is a
breakdown or medical need — no mobile data needed.

## 6. Remote worksites and field research

**Situation.** Survey teams, farms, construction sites and research stations
often have no or very poor connectivity.

**With DEPOT.** Workers share photos of equipment and samples, send short voice
reports, and see on the dashboard who is on site. The **SOS** with health card
adds a safety layer in places where help is far away.

## 7. Privacy-sensitive local sharing

**Situation.** A group wants to share files or talk without anything touching a
cloud service.

**With DEPOT.** Everything — messages, files, voice notes, profiles — lives on
the Pi's SD card and never leaves the local network. "Clear chat" wipes
messages **and** shared files from the device.

*(DEPOT is protected by the Wi-Fi password only and is not end-to-end encrypted;
see the limitations in the [README](../README.md#honest-limitations).)*

---

## Feature-to-need map

| Need | DEPOT answer |
|---|---|
| "Talk to everyone nearby right now" | Real-time chat, voice notes |
| "Send this document / photo to the group" | File & photo sharing (25 MB each) |
| "Who is here?" | Network monitor: name, IP, time online |
| "Someone needs help" | SOS with name, IP, note, health card and responder list |
| "The channel is being flooded" | Spam guard with escalating timeouts |
| "It must work with no infrastructure" | Pi hosts its own Wi-Fi, DHCP, web server and database |
| "Keep our data private and local" | Everything on the Pi; one-tap wipe |

## What DEPOT is *not* for

* **Long distances or large areas** — it is a single Wi-Fi hub, not a mesh or radio link.
* **Calling emergency services** — SOS alerts people nearby only.
* **Strong anonymity or confidentiality** — it is not end-to-end encrypted and names are self-declared.
