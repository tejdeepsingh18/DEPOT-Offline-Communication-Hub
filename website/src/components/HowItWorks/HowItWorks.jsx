import SectionHeading from "../ui/SectionHeading";
import { DEPOT_URL, DEPOT_SSID, DEPOT_WIFI_PASSWORD } from "../../config/depot";
import "./HowItWorks.css";

const STEPS = [
  {
    number: "01",
    title: "Connect",
    copy: `Join the Wi-Fi network “${DEPOT_SSID}” (password ${DEPOT_WIFI_PASSWORD}). Any phone works — it is plain 2.4 GHz WPA2.`,
  },
  {
    number: "02",
    title: "Open",
    copy: `Open ${DEPOT_URL} in the browser and pick a display name. Nothing to install.`,
  },
  {
    number: "03",
    title: "Exchange",
    copy: "Chat in real time, share photos and documents, send voice notes — and hit SOS if something goes wrong.",
  },
];

/**
 * The three-step flow. Runs horizontally once there is room, and stacks into a
 * numbered list on phones, where most DEPOT users will actually read it.
 */
function HowItWorks() {
  return (
    <section
      className="depot-how depot-section"
      id="how-it-works"
      aria-labelledby="how-it-works-title"
    >
      <div className="depot-shell">
        <SectionHeading
          id="how-it-works-title"
          eyebrow="How it works"
          title="Three steps, no configuration."
          description="Nothing to install and no account to create — just a display name. A device only ever needs to join the network and open the interface."
        />

        <ol className="depot-how__steps">
          {STEPS.map((step) => (
            <li className="depot-how__step" key={step.number}>
              <span className="depot-how__number" aria-hidden="true">
                {step.number}
              </span>

              <h3 className="depot-how__title">
                <span className="depot-visually-hidden">
                  Step {step.number}:{" "}
                </span>
                {step.title}
              </h3>

              <p className="depot-how__copy">{step.copy}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

export default HowItWorks;
