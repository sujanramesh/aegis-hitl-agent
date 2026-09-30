import { Plus } from "lucide-react";
import { useEffect, useState } from "react";

import MetricCard from "../components/common/MetricCard";
import WorkflowGraphic from "../components/common/WorkflowGraphic";
import ApprovalCard from "../components/approvals/ApprovalCard";
import ActiveIncident from "../components/incidents/ActiveIncident";
import AgentTimeline from "../components/incidents/AgentTimeline";
import NewIncidentModal from "../components/incidents/NewIncidentModal";
import ServiceHealth from "../components/incidents/ServiceHealth";
import { useAuth } from "../context/AuthContext";
import {
  getAuditEvents,
  getIncident,
  getIncidents,
  getPendingApprovals,
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
  const [summaryLoadError, setSummaryLoadError] = useState("");
  const [approvalQueueUnavailable, setApprovalQueueUnavailable] = useState(false);
  const [auditStreamUnavailable, setAuditStreamUnavailable] = useState(false);
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [recentEvents, setRecentEvents] = useState([]);

  const canCreateIncident = hasRole(
    "operator",
    "approver"
  );

  useEffect(() => {
    async function loadLatestIncident() {
      try {
        setIncidentLoadError("");

        const [incidentResult, approvalResult, auditResult] =
          await Promise.allSettled([
            getIncidents(50),
            getPendingApprovals(),
            getAuditEvents(6),
          ]);

        const failedSources = [
          [incidentResult, "incident registry"],
          [approvalResult, "approval queue"],
          [auditResult, "audit stream"],
        ].filter(([result]) => result.status === "rejected");
        setSummaryLoadError(
          failedSources.length
            ? `Some overview data could not be loaded: ${failedSources.map(([, source]) => source).join(", ")}.`
            : "",
        );
        setApprovalQueueUnavailable(approvalResult.status === "rejected");
        setAuditStreamUnavailable(auditResult.status === "rejected");

        const incidents = incidentResult.status === "fulfilled" &&
          Array.isArray(incidentResult.value)
          ? incidentResult.value
          : [];
        setRecentIncidents(incidents);

        setPendingApprovals(
          approvalResult.status === "fulfilled" && Array.isArray(approvalResult.value)
            ? approvalResult.value
            : [],
        );
        setRecentEvents(
          auditResult.status === "fulfilled" && Array.isArray(auditResult.value)
            ? auditResult.value
            : [],
        );

        if (incidentResult.status === "rejected") {
          throw incidentResult.reason;
        }

        if (
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
    setRecentIncidents((current) => [incident, ...current].slice(0, 50));
    if (incident.awaiting_approval) {
      setPendingApprovals((current) => [incident, ...current]);
      setApprovalQueueUnavailable(false);
    }
    setIncidentLoadError("");
  }

  function handleDecisionCompleted(
    updatedIncident
  ) {
    setLatestIncident((current) =>
      current?.incident_id === updatedIncident.incident_id
        ? updatedIncident
        : current,
    );
    setPendingApprovals((current) => current.filter(
      (incident) => incident.incident_id !== updatedIncident.incident_id,
    ));
  }

  const terminalStatuses = ["completed", "resolved", "rejected", "failed", "llm_unavailable", "action_cancelled"];
  const activeIncidentCount = recentIncidents.filter(
    (incident) => !terminalStatuses.includes(incident.status),
  ).length;
  const resolvedIncidentCount = recentIncidents.filter(
    (incident) => ["completed", "resolved"].includes(incident.status),
  ).length;
  const featuredApproval =
    pendingApprovals.find(
      (incident) => incident.risk_level === "high",
    ) || pendingApprovals[0];

  const serviceRefreshKey = [
    latestIncident?.incident_id || "none",
    latestIncident?.status || "idle",
  ].join(":");

  return (
    <div className="overview-page">
      <div className="overview-heading">
        <div className="page-heading">
          <span className="eyebrow">
            Operations overview
          </span>

          <h1>Aegis Operations</h1>

          <p>
            Incidents, authorization and recovery across the latest operational activity.
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

      {!isLoadingIncident && summaryLoadError && (
        <div className="observability-error" role="status">
          {summaryLoadError} Displayed totals may be incomplete.
        </div>
      )}

      <section className="metric-grid">
        <MetricCard
          label="Active incidents"
          value={String(activeIncidentCount).padStart(2, "0")}
          detail="In latest 50 records"
          tone={
            activeIncidentCount > 0
              ? "warning"
              : undefined
          }
        />

        <MetricCard
          label="Awaiting approval"
          value={String(pendingApprovals.length).padStart(2, "0")}
          detail="Human authorization required"
          tone={
            pendingApprovals.length > 0
              ? "warning"
              : undefined
          }
        />

        <MetricCard
          label="Resolved"
          value={String(resolvedIncidentCount).padStart(2, "0")}
          detail="In latest 50 records"
          tone="success"
        />
      </section>

      <WorkflowGraphic />

      <section className="overview-command-grid">
        <div className="overview-primary-stack">
          <ActiveIncident incident={latestIncident} />
          <AgentTimeline incident={latestIncident} />
        </div>

        <aside className="overview-secondary-stack">
          <section className="overview-approval-queue">
            <div className="overview-queue-heading">
              <div>
                <span className="panel-kicker">Human authorization</span>
                <h2>Approval queue</h2>
              </div>
              <span className="overview-queue-count">
                {isLoadingIncident ? "—" : pendingApprovals.length}
              </span>
            </div>

            {isLoadingIncident ? (
              <div className="overview-queue-empty" role="status">
                Loading approval queue…
              </div>
            ) : approvalQueueUnavailable ? (
              <div className="overview-queue-empty" role="alert">
                The approval queue could not be loaded. Check the service connection and retry from Approvals.
              </div>
            ) : featuredApproval ? (
              <>
                <ApprovalCard
                  incident={featuredApproval}
                  onDecisionCompleted={handleDecisionCompleted}
                />
                {pendingApprovals.length > 1 && (
                  <p className="overview-queue-note">
                    {pendingApprovals.length - 1} more pending in the Approvals view.
                  </p>
                )}
              </>
            ) : (
              <div className="overview-queue-empty">
                No pending human authorizations.
              </div>
            )}
          </section>

          <ServiceHealth refreshKey={serviceRefreshKey} />
        </aside>
      </section>

      <section className="dashboard-panel recent-activity-panel">
        <div className="panel-heading">
          <div>
            <span className="panel-kicker">Audit stream</span>
            <h3>Recent operational activity</h3>
          </div>
          <span className="incident-count">Newest first</span>
        </div>
        {recentEvents.length ? (
          <div className="overview-activity-list">
            {recentEvents.map((event) => (
              <div className="overview-activity-row" key={event.id}>
                <span className="overview-activity-marker" />
                <div>
                  <strong>{event.event_type?.replaceAll("_", " ") || "Operational event"}</strong>
                  <span>{event.details || event.incident_id || "Recorded activity"}</span>
                </div>
                <time>{event.created_at ? new Date(event.created_at).toLocaleString() : "—"}</time>
              </div>
            ))}
          </div>
        ) : auditStreamUnavailable ? (
          <div className="overview-activity-empty" role="alert">
            Recent audit activity could not be loaded.
          </div>
        ) : (
          <div className="overview-activity-empty">No recent audit events are available.</div>
        )}
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
    </div>
  );
}
