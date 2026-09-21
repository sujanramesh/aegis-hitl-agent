import { useState } from "react";

import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";

import Overview from "./pages/Overview";
import Incidents from "./pages/Incidents";
import Approvals from "./pages/Approvals";
import Login from "./pages/Login";
import Services from "./pages/Services";
import Audit from "./pages/Audit";
import Observability from "./pages/Observability";

import { useAuth } from "./context/AuthContext";

const pageInformation = {
  services: {
    eyebrow: "Infrastructure",
    title: "Services",
    description:
      "Inspect operational service health and deployments.",
  },

  observability: {
    eyebrow: "Observe",
    title: "Observability",
    description:
      "Inspect Aegis runtime health and operational telemetry.",
  },

  audit: {
    eyebrow: "Governance",
    title: "Audit trail",
    description:
      "Review durable operational and authorization history.",
  },
};

function LoadingScreen() {
  return (
    <main className="auth-loading">
      <div className="auth-loading__mark">
        A
      </div>

      <span>
        Establishing secure session...
      </span>
    </main>
  );
}

export default function App() {
  const {
    isAuthenticated,
    isInitializing,
  } = useAuth();

  const [activePage, setActivePage] =
    useState("overview");

  if (isInitializing) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  function renderPage() {
    if (activePage === "overview") {
      return <Overview />;
    }

    if (activePage === "incidents") {
      return <Incidents />;
    }

    if (activePage === "approvals") {
      return <Approvals />;
    }

    if (activePage === "services") {
      return <Services />;
    }

    if (activePage === "audit") {
      return <Audit />;
    }

    if (activePage === "observability") {
      return <Observability />;
    }

    return (
      <div className="page-heading">
        <span className="eyebrow">
          {
            pageInformation[activePage]
              .eyebrow
          }
        </span>

        <h1>
          {
            pageInformation[activePage]
              .title
          }
        </h1>

        <p>
          {
            pageInformation[activePage]
              .description
          }
        </p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
      />

      <div className="workspace">
        <Topbar />

        <main className="main-content">
          {renderPage()}
        </main>
      </div>
    </div>
  );
}