import { Plus } from "lucide-react";
import { useEffect, useState } from "react";

import MetricCard from "../components/common/MetricCard";
import ApprovalCard from "../components/approvals/ApprovalCard";
import ActiveIncident from "../components/incidents/ActiveIncident";
import AgentTimeline from "../components/incidents/AgentTimeline";
import NewIncidentModal from "../components/incidents/NewIncidentModal";
import ServiceHealth from "../components/incidents/ServiceHealth";
import { useAuth } from "../context/AuthContext";
import {
  getIncident,
  getIncidents,
} from "../services/api.js";

export default function Overview() {
  const { hasRole } = useAuth();

  const [showNewIncident, setShowNewIncident] =
    useState(false);

  const [latestIncident, setLatestIncident] =
    useState(null);

  const [isLoadingIncident, setIsLoadingIncident] =
    useState(true);

  const [incidentLoadError, setIncidentLoadError] =
    useState("");

  const canCreateIncident = hasRole(
    "operator",
    "approver"
  );

  useEffect(() => {
    async function loadLatestIncident() {
      try {
        setIncidentLoadError("");

        const incidents =
          await getIncidents(1);

        if (
          !Array.isArray(incidents) ||
          incidents.length === 0
        ) {
          setLatestIncident(null);
          return;
        }

        const incident =
          await getIncident(
            incidents[0].incident_id
          );

        setLatestIncident(incident);
      } catch (error) {
        console.error(
          "Unable to load latest incident:",
          error
        );

        setIncidentLoadError(
          error.message ||
            "Unable to load the latest incident."
        );
      } finally {
        setIsLoadingIncident(false);
      }
    }

    loadLatestIncident();
  }, []);

  function handleIncidentCreated(incident) {
    setLatestIncident(incident);
    setIncidentLoadError("");
  }

  function handleDecisionCompleted(
    updatedIncident
  ) {
    setLatestIncident(updatedIncident);
  }

  const isIncidentActive =
    latestIncident &&
    ![
      "completed",
      "resolved",
      "rejected",
      "failed",
      "llm_unavailable",
    ].includes(latestIncident.status);

  const activeIncidentCount =
    isIncidentActive ? "01" : "00";

  const awaitingApprovalCount =
    latestIncident?.awaiting_approval
      ? "01"
      : "00";

  const recoveredCount =
    latestIncident?.verification_result
      ?.recovered === true ||
    latestIncident?.verification_result
      ?.healthy === true
      ? "01"
      : "00";

  const serviceRefreshKey = [
    latestIncident?.incident_id || "none",
    latestIncident?.status || "idle",
  ].join(":");

  return (
    <>
      <div className="overview-heading">
        <div className="page-heading">
          <span className="eyebrow">
            Operations
          </span>

          <h1>Incident command</h1>

          <p>
            Monitor autonomous investigations,
            human authorization and recovery.
          </p>
        </div>

        {canCreateIncident && (
          <button
            type="button"
            className="button button--primary"
            onClick={() =>
              setShowNewIncident(true)
            }
          >
            <Plus
              size={15}
              strokeWidth={2}
            />
            New incident
          </button>
        )}
      </div>

      {isLoadingIncident && (
        <div
          className="incident-created-banner"
          role="status"
        >
          <div>
            <strong>
              Loading investigation
            </strong>

            <span>
              Recovering latest workflow
              state...
            </span>
          </div>
        </div>
      )}

      {!isLoadingIncident &&
        incidentLoadError && (
          <div
            className="incident-form__error"
            role="alert"
          >
            <span>
              {incidentLoadError}
            </span>
          </div>
        )}

      {latestIncident && (
        <div
          className="incident-created-banner"
          role="status"
        >
          <div>
            <strong>
              Latest investigation
            </strong>

            <span>
              Incident{" "}
              {latestIncident.incident_id}
            </span>
          </div>

          <span className="status-badge">
            {latestIncident.awaiting_approval
              ? "Awaiting approval"
              : latestIncident.status?.replaceAll(
                  "_",
                  " "
                )}
          </span>
        </div>
      )}

      <section className="metric-grid">
        <MetricCard
          label="Active incidents"
          value={activeIncidentCount}
          detail={
            isIncidentActive
              ? "Current incident active"
              : "No active incident"
          }
          tone={
            isIncidentActive
              ? "warning"
              : undefined
          }
        />

        <MetricCard
          label="Awaiting approval"
          value={awaitingApprovalCount}
          detail={
            latestIncident?.awaiting_approval
              ? "Human action required"
              : "No authorization pending"
          }
          tone={
            latestIncident?.awaiting_approval
              ? "warning"
              : undefined
          }
        />

        <MetricCard
          label="Recovered"
          value={recoveredCount}
          detail={
            recoveredCount === "01"
              ? "Recovery verified"
              : "No verified recovery"
          }
          tone={
            recoveredCount === "01"
              ? "success"
              : undefined
          }
        />

        <MetricCard
          label="Risk level"
          value={
            latestIncident?.risk_level
              ?.slice(0, 4)
              .toUpperCase() || "—"
          }
          detail={
            latestIncident?.risk_level
              ? `${latestIncident.risk_level} risk operation`
              : "No risk assessment loaded"
          }
          tone={
            latestIncident?.risk_level ===
            "high"
              ? "warning"
              : undefined
          }
        />
      </section>

      <section className="dashboard-grid">
        <ActiveIncident
          incident={latestIncident}
        />

        <AgentTimeline
          incident={latestIncident}
        />
      </section>

      {latestIncident?.awaiting_approval && (
        <section className="dashboard-section">
          <ApprovalCard
            incident={latestIncident}
            onDecisionCompleted={
              handleDecisionCompleted
            }
          />
        </section>
      )}

      <section className="dashboard-section">
        <ServiceHealth
          refreshKey={serviceRefreshKey}
        />
      </section>

      <NewIncidentModal
        open={showNewIncident}
        onClose={() =>
          setShowNewIncident(false)
        }
        onCreated={
          handleIncidentCreated
        }
      />
    </>
  );
}