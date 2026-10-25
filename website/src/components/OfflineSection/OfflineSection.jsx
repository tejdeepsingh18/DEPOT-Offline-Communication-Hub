import "./OfflineSection.css";

const STATEMENT_LINES = ["internet.", "cloud.", "dependency."];

/**
 * The statement section — the one place on the page with inverted colour.
 *
 * A full-bleed near-black band is the strongest contrast available without
 * gradients or decoration, and it gives the page a deliberate midpoint.
 */
function OfflineSection() {
  return (
    <section
      className="depot-offline"
      id="offline"
      aria-labelledby="offline-title"
    >
      <div className="depot-shell depot-offline__layout">
        <h2 className="depot-offline__statement" id="offline-title">
          {STATEMENT_LINES.map((line) => (
            <span className="depot-offline__line" key={line}>
              <span className="depot-offline__negation">No</span> {line}
            </span>
          ))}
        </h2>

        <p className="depot-offline__copy">
          DEPOT operates entirely within its own wireless network. Plug the Pi
          into a battery bank and it builds the network by itself at every boot —
          for disaster zones, dead zones, or a road trip through nowhere.
        </p>
      </div>
    </section>
  );
}

export default OfflineSection;
