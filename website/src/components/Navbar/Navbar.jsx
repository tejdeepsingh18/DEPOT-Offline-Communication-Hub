import { useEffect, useState } from "react";
import "./Navbar.css";

const NAV_LINKS = [
  { label: "Overview", href: "#overview" },
  { label: "Features", href: "#capabilities" },
  { label: "Stack", href: "#stack" },
  { label: "System", href: "#system" },
];

const SCROLL_THRESHOLD_PX = 8;

function Navbar({ networkLabel = "LOCAL NETWORK", networkState = "active" }) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > SCROLL_THRESHOLD_PX);
    };

    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // A fixed bar must not leave the page scrollable behind the open panel.
  useEffect(() => {
    if (!isMenuOpen) {
      return undefined;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isMenuOpen]);

  return (
    <header
      className={`depot-nav${isScrolled ? " depot-nav--scrolled" : ""}`}
      data-menu-open={isMenuOpen ? "true" : "false"}
    >
      <div className="depot-nav__inner depot-shell">
        <a className="depot-nav__brand" href="#top">
          DEPOT
        </a>

        <nav className="depot-nav__links" aria-label="Primary">
          <ul>
            {NAV_LINKS.map((link) => (
              <li key={link.label}>
                <a className="depot-nav__link" href={link.href}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <p className="depot-nav__status">
          <span
            className={`depot-nav__status-dot depot-nav__status-dot--${networkState}`}
            aria-hidden="true"
          />
          <span className="depot-nav__status-text">{networkLabel}</span>
        </p>

        <button
          className="depot-nav__toggle"
          type="button"
          aria-expanded={isMenuOpen}
          aria-controls="depot-nav-panel"
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          <span className="depot-visually-hidden">
            {isMenuOpen ? "Close navigation" : "Open navigation"}
          </span>
          <span className="depot-nav__toggle-bars" aria-hidden="true" />
        </button>
      </div>

      <div
        className="depot-nav__panel"
        id="depot-nav-panel"
        hidden={!isMenuOpen}
      >
        <nav aria-label="Primary mobile">
          <ul>
            {NAV_LINKS.map((link) => (
              <li key={link.label}>
                <a
                  className="depot-nav__panel-link"
                  href={link.href}
                  onClick={() => setIsMenuOpen(false)}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      </div>
    </header>
  );
}

export default Navbar;
