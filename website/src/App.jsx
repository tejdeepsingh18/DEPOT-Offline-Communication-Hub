import Navbar from "./components/Navbar/Navbar";
import Hero from "./components/Hero/Hero";
import SystemOverview from "./components/SystemOverview/SystemOverview";
import Capabilities from "./components/Capabilities/Capabilities";
import SystemStatus from "./components/SystemStatus/SystemStatus";
import Stack from "./components/Stack/Stack";
import HowItWorks from "./components/HowItWorks/HowItWorks";
import OfflineSection from "./components/OfflineSection/OfflineSection";
import Footer from "./components/Footer/Footer";
import "./App.css";

/**
 * The DEPOT landing page.
 *
 * Each section owns its own data source and styles; this file only decides the
 * order they appear in, so sections can be added, removed or reordered without
 * touching anything else.
 */
function App() {
  return (
    <div className="depot-page">
      <a className="depot-skip-link" href="#main">
        Skip to content
      </a>

      <Navbar />

      <main className="depot-page__main" id="main" tabIndex={-1}>
        <Hero />
        <SystemOverview />
        <Capabilities />
        <Stack />
        <SystemStatus />
        <HowItWorks />
        <OfflineSection />
      </main>

      <Footer />
    </div>
  );
}

export default App;
