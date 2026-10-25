import "./CapabilityIcon.css";

const ICON_PATHS = {
  messaging: (
    <>
      <path d="M3.5 5.5A2 2 0 0 1 5.5 3.5h13a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9l-4.2 3.2A.6.6 0 0 1 4 18.2V15.5h-.5a2 2 0 0 1-2-2v-8Z" />
      <path d="M7 8.5h10M7 12h6" />
    </>
  ),
  files: (
    <>
      <path d="M13 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9.5l-6-6Z" />
      <path d="M13 3.5v6h6" />
    </>
  ),
  voice: (
    <>
      <rect x="9" y="3.5" width="6" height="11" rx="3" />
      <path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v2.5M9 20.5h6" />
    </>
  ),
  network: (
    <>
      <path d="M3 9.5a13 13 0 0 1 18 0" />
      <path d="M6.2 12.8a8.5 8.5 0 0 1 11.6 0" />
      <path d="M9.4 16a4 4 0 0 1 5.2 0" />
      <circle cx="12" cy="19" r="0.9" />
    </>
  ),
  sos: (
    <>
      <path d="M12 3.5 21 19a1 1 0 0 1-.87 1.5H3.87A1 1 0 0 1 3 19L12 3.5Z" />
      <path d="M12 9.5v4.5M12 17.2v.3" />
    </>
  ),
  storage: (
    <>
      <ellipse cx="12" cy="6" rx="7.5" ry="2.8" />
      <path d="M4.5 6v12c0 1.55 3.36 2.8 7.5 2.8s7.5-1.25 7.5-2.8V6" />
      <path d="M4.5 12c0 1.55 3.36 2.8 7.5 2.8s7.5-1.25 7.5-2.8" />
    </>
  ),
};

/**
 * Restrained line glyph for each capability. Purely presentational, so it is
 * hidden from assistive technology — the adjacent heading carries the meaning.
 */
function CapabilityIcon({ name }) {
  const path = ICON_PATHS[name];

  if (!path) {
    return null;
  }

  return (
    <svg
      className="depot-capability-icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {path}
    </svg>
  );
}

export default CapabilityIcon;
