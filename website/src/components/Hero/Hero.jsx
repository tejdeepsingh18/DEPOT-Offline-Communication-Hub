import Button from "../ui/Button";
import { DEPOT_URL, DEPOT_SSID, DEPOT_WIFI_PASSWORD } from "../../config/depot";
import "./Hero.css";

const HERO_FACTS = [
  { label: "Wi-Fi", value: `${DEPOT_SSID} · ${DEPOT_WIFI_PASSWORD}` },
  { label: "Address", value: DEPOT_URL.replace("http://", "") },
  { label: "Requires internet", value: "No" },
];

/**
 * Editorial opening statement. Deliberately text-only: the type hierarchy does
 * the work, so no illustration or decoration is needed.
 */
function Hero() {
  return (
    <section className="depot-hero" id="top">
      <div className="depot-shell depot-hero__inner">
        <p className="depot-eyebrow depot-hero__eyebrow">
          The internet, in a backpack
        </p>

        <h1 className="depot-hero__title">
          Communication without the internet.
        </h1>

        <p className="depot-hero__lede">
          A Raspberry Pi becomes the Wi-Fi network, the web server, the database
          and the router — so a group of phones can chat, share files, send voice
          notes and raise an SOS with zero internet and zero cell coverage.
        </p>

        <div className="depot-hero__actions">
          <Button href={DEPOT_URL} size="large">
            Open DEPOT
          </Button>

          <Button href="#how-it-works" variant="link" size="large">
            How it works
          </Button>
        </div>

        <dl className="depot-hero__facts">
          {HERO_FACTS.map((fact) => (
            <div className="depot-hero__fact" key={fact.label}>
              <dt>{fact.label}</dt>
              <dd>{fact.value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}

export default Hero;
