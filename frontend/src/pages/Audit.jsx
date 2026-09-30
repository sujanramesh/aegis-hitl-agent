import { useEffect, useState } from "react";
import {
  RefreshCw,
  ShieldCheck,
  UserCheck,
  Bot,
  Activity,
} from "lucide-react";

import { getAuditEvents } from "../services/api.js";

function formatEventType(eventType) {
  if (!eventType) return "Unknown event";

  return eventType
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function shortenIncidentId(incidentId) {
  if (!incidentId) return "—";

  return incidentId.length > 12
    ? `${incidentId.slice(0, 8)}…`
    : incidentId;
}

function parseDetails(details) {
  if (!details) return "—";

  try {
    const parsed = JSON.parse(details);

    return Object.entries(parsed)
      .map(([key, value]) => {
        const label = key
          .replaceAll("_", " ")
          .replace(/\b\w/g, (character) =>
            character.toUpperCase()
          );

        const formattedValue =
          typeof value === "object"
            ? JSON.stringify(value)
            : String(value);

        return `${label}: ${formattedValue}`;
      })
      .join(" · ");
  } catch {
    return details;
  }
}

function getEventIcon(eventType) {
  if (
    eventType === "HUMAN_APPROVED" ||
    eventType === "HUMAN_REJECTED"
  ) {
    return UserCheck;
  }

  if (
    eventType === "ACTION_EXECUTED" ||
    eventType === "RECOVERY_VERIFIED"
  ) {
    return Activity;
  }

  if (
    eventType === "INVESTIGATION_COMPLETED" ||
    eventType === "WORKFLOW_COMPLETED"
  ) {
    return Bot;
  }

  return ShieldCheck;
}

function Audit() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAuditEvents() {
    setLoading(true);
    setError("");

    try {
      const data = await getAuditEvents(100);

      setEvents(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to load audit trail."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAuditEvents();
  }, []);

  const chronologicalEvents = [...events].sort((left, right) => {
    const leftTime = new Date(left.created_at || 0).getTime();
    const rightTime = new Date(right.created_at || 0).getTime();
    return leftTime - rightTime || left.id - right.id;
  });

  return (
    <div className="audit-page">
      <div className="page-heading audit-page-heading">
        <div>
          <div className="eyebrow">
            Governance
          </div>

          <h1>Audit Trail</h1>

          <p>
            Durable operational history of agent activity,
            human authorization, execution, and recovery.
          </p>
        </div>

        <button
          className="button audit-refresh-button"
          type="button"
          onClick={loadAuditEvents}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? "audit-refresh-icon spinning"
                : "audit-refresh-icon"
            }
          />

          {loading ? "Refreshing" : "Refresh"}
        </button>
      </div>

      <div className="audit-summary">
        <div>
          <span className="audit-summary-label">
            Recorded events
          </span>

          <strong>
            {loading ? "—" : events.length}
          </strong>
        </div>

        <div>
          <span className="audit-summary-label">
            Source
          </span>

          <strong>MySQL</strong>
        </div>

        <div>
          <span className="audit-summary-label">
            Access
          </span>

          <strong>Authenticated</strong>
        </div>
      </div>

      <section className="dashboard-panel audit-panel">
        <div className="panel-heading">
          <div>
            <div className="panel-kicker">
              Operational history
            </div>

            <h2>Recorded events</h2>
          </div>

          <span className="audit-event-count">
            {events.length} events · oldest first
          </span>
        </div>

        {error && (
          <div className="audit-state audit-error">
            {error}
          </div>
        )}

        {!error && loading && (
          <div className="audit-state">
            Loading audit records…
          </div>
        )}

        {!error &&
          !loading &&
          events.length === 0 && (
            <div className="audit-state">
              No audit events have been recorded yet.
            </div>
          )}

        {!error &&
          !loading &&
          events.length > 0 && (
            <div className="audit-event-list">
              {chronologicalEvents.map((event) => {
                    const EventIcon =
                      getEventIcon(
                        event.event_type
                      );

                    return (
                      <article className="audit-event" key={event.id}>
                        <div className="audit-event__rail">
                          <span className="audit-event-icon"><EventIcon size={15} /></span>
                        </div>
                        <div className="audit-event__body">
                          <div className="audit-event__heading">
                            <strong>{formatEventType(event.event_type)}</strong>
                            <time className="audit-time">{formatDate(event.created_at)}</time>
                          </div>
                          <p className="audit-details">{parseDetails(event.details)}</p>
                          <div className="audit-event__meta">
                            <span>Actor <b>{event.actor || "—"}</b></span>
                            <span>Incident <b className="audit-incident-id" title={event.incident_id || undefined}>{shortenIncidentId(event.incident_id)}</b></span>
                          </div>
                        </div>
                      </article>
                    );
                  })}
            </div>
          )}
      </section>
    </div>
  );
}

export default Audit;
