import SectionHeading from "../ui/SectionHeading";
import CapabilityIcon from "./CapabilityIcon";
import "./Capabilities.css";

const CAPABILITIES = [
  {
    id: "messaging",
    icon: "messaging",
    title: "Real-time messaging",
    copy: "Messages appear on every screen the instant they are sent, pushed over Server-Sent Events. Reconnect and only what you missed is replayed — no gaps, no duplicates.",
  },
  {
    id: "files",
    icon: "files",
    title: "File & photo sharing",
    copy: "Send images, PDFs, documents and short videos up to 25 MB. Photos preview inline; everything else downloads straight from the Pi.",
  },
  {
    id: "voice",
    icon: "voice",
    title: "Voice notes",
    copy: "Tap the mic, talk, send — like WhatsApp or Telegram. Notes play back inline with a scrubber and duration.",
  },
  {
    id: "network",
    icon: "network",
    title: "Live network monitor",
    copy: "A dashboard everyone can open: who is in the chat with their name and IP, every device on the Wi-Fi, the Pi's health — and a rule-based spam guard that throttles floods.",
  },
  {
    id: "sos",
    icon: "sos",
    title: "Emergency SOS",
    copy: "Add a health card at sign-up. One tap on SOS sends a full-screen alarm to everyone nearby with your name, IP and health details — and shows you who is coming.",
  },
  {
    id: "storage",
    icon: "storage",
    title: "Local storage",
    copy: "Chat history, files and profiles live in SQLite on the Pi's SD card — no cloud, no server to run, and it all survives a reboot.",
  },
];

/**
 * The core capabilities. Separated by rules rather than boxed into
 * cards, so the section stays as light as the rest of the page.
 */
function Capabilities() {
  return (
    <section
      className="depot-capabilities depot-section"
      id="capabilities"
      aria-labelledby="capabilities-title"
    >
      <div className="depot-shell">
        <SectionHeading
          id="capabilities-title"
          eyebrow="Capabilities"
          title="Everything stays on the local network."
          description="DEPOT handles what a disconnected group actually needs — talking, sharing and calling for help — without a cloud account or an external connection."
        />

        <ul className="depot-capabilities__list">
          {CAPABILITIES.map((capability) => (
            <li
              className="depot-capabilities__item"
              id={capability.id}
              key={capability.id}
            >
              <CapabilityIcon name={capability.icon} />

              <h3 className="depot-capabilities__title">{capability.title}</h3>

              <p className="depot-capabilities__copy">{capability.copy}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export default Capabilities;
