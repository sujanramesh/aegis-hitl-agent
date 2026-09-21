import {
  Check,
  Clock3,
  Search,
  ShieldAlert,
} from "lucide-react";

function cleanMarkdown(text) {
  if (!text) {
    return "";
  }

  return text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^[-*]\s+/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

function formatActionType(actionType) {
  if (!actionType) {
    return "remediation action";
  }

  return actionType
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function buildEvents(incident) {
  if (!incident) {
    return [];
  }

  const events = [
    {
      title: "Incident received",
      detail: `${incident.service} incident submitted to Aegis`,
      status: "complete",
    },
  ];

  if (
    Array.isArray(incident.evidence) &&
    incident.evidence.length > 0
  ) {
    events.push({
      title: "Evidence collected",
      detail: `${incident.evidence.length} evidence item${
        incident.evidence.length === 1
          ? ""
          : "s"
      } collected from operational sources`,
      status: "complete",
    });
  }

  if (incident.hypothesis) {
    events.push({
      title: "Hypothesis generated",
      detail:
        "Aegis correlated the collected evidence and generated an incident hypothesis.",
      status: "complete",
    });
  }

  if (incident.proposed_action) {
    events.push({
      title: "Remediation proposed",
      detail: formatActionType(
        incident.proposed_action.action_type
      ),
      status: "complete",
    });
  }

  if (incident.awaiting_approval) {
    events.push({
      title: "Awaiting authorization",
      detail: `${
        incident.risk_level
          ? incident.risk_level
              .charAt(0)
              .toUpperCase() +
            incident.risk_level.slice(1)
          : "Consequential"
      } risk action requires human approval`,
      status: "current",
    });
  } else if (
    incident.approval_decision ===
    "approved"
  ) {
    events.push({
      title: "Action authorized",
      detail: incident.approval_reason
        ? cleanMarkdown(
            incident.approval_reason
          )
        : "An authorized approver approved the proposed action.",
      status: "complete",
    });
  } else if (
    incident.approval_decision ===
    "rejected"
  ) {
    events.push({
      title: "Action rejected",
      detail:
        cleanMarkdown(
          incident.approval_reason
        ) ||
        "The proposed action was rejected.",
      status: "complete",
    });
  }

  if (incident.execution_result) {
    events.push({
      title: "Action executed",
      detail:
        cleanMarkdown(
          incident.execution_result.message
        ) ||
        "The authorized remediation action was executed.",
      status: "complete",
    });
  }

  if (incident.verification_result) {
    events.push({
      title: "Recovery verified",
      detail:
        cleanMarkdown(
          incident.verification_result.message
        ) ||
        "Post-action service health was verified.",
      status: "complete",
    });
  }

  return events;
}

export default function AgentTimeline({
  incident,
}) {
  const events = buildEvents(incident);

  const agentState =
    incident?.awaiting_approval
      ? "Paused"
      : incident
        ? "Completed"
        : "Idle";

  return (
    <article className="dashboard-panel timeline-panel">
      <div className="panel-heading">
        <div>
          <span className="panel-kicker">
            Agent activity
          </span>

          <h3>
            Investigation timeline
          </h3>
        </div>

        <div className="agent-state">
          <span />
          {agentState}
        </div>
      </div>

      {events.length > 0 ? (
        <div className="timeline">
          {events.map(
            (event, index) => (
              <div
                className={`timeline-event timeline-event--${event.status}`}
                key={`${event.title}-${index}`}
              >
                <div className="timeline-marker">
                  {event.status ===
                  "complete" ? (
                    <Check
                      size={12}
                      strokeWidth={2.5}
                    />
                  ) : (
                    <Clock3
                      size={12}
                      strokeWidth={2}
                    />
                  )}
                </div>

                {index <
                  events.length - 1 && (
                  <span className="timeline-line" />
                )}

                <div className="timeline-content">
                  <strong>
                    {event.title}
                  </strong>

                  <span>
                    {event.detail}
                  </span>
                </div>
              </div>
            )
          )}
        </div>
      ) : (
        <div className="incident-summary">
          <p>
            No investigation activity is
            available yet.
          </p>
        </div>
      )}

      <div className="timeline-footer">
        <Search size={14} />

        <span>
          Evidence-grounded investigation
        </span>

        <ShieldAlert size={14} />

        <span>
          Policy-controlled execution
        </span>
      </div>
    </article>
  );
}