import { DEPOT_URL, DEPOT_SOURCE_URL } from "../../config/depot";
import "./Footer.css";

const FOOTER_LINKS = [
  { label: "Overview", href: "#overview" },
  { label: "Features", href: "#capabilities" },
  { label: "Stack", href: "#stack" },
  { label: "System", href: "#system" },
  { label: "How it works", href: "#how-it-works" },
  { label: "Open DEPOT", href: DEPOT_URL },
  { label: "Source", href: DEPOT_SOURCE_URL },
];

function Footer() {
  return (
    <footer className="depot-footer">
      <div className="depot-shell depot-footer__inner">
        <div className="depot-footer__identity">
          <p className="depot-footer__brand">DEPOT</p>
          <p className="depot-footer__tagline">
            Offline Digital Communication and File-Sharing Hub
          </p>
          <p className="depot-footer__credit">Built on a Raspberry Pi 1 — hostapd, dnsmasq, Flask and SQLite.</p>
        </div>

        <nav className="depot-footer__nav" aria-label="Footer">
          <ul>
            {FOOTER_LINKS.map((link) => (
              <li key={link.label}>
                <a className="depot-footer__link" href={link.href}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </footer>
  );
}

export default Footer;
