import {
  ArrowRight,
  Box,
  GitCommitHorizontal,
} from "lucide-react";

import StatusBadge from "../common/StatusBadge";

function formatIncidentId(incidentId) {
  if (!incidentId) {
    return "INCIDENT";
  }

  return `INC-${incidentId
    .split("-")[0]
    .toUpperCase()}`;
}

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

function extractPrimaryHypothesis(text) {
  if (!text) {
    return "";
  }

  const cleanedText = cleanMarkdown(text);

  const primaryMatch = cleanedText.match(
    /Primary hypothesis:\s*(.*?)(?=\s*(?:Supporting evidence|Relevant runbook guidance|Uncertainties|Causation vs\.? Correlation):|$)/i
  );

  if (primaryMatch?.[1]) {
    return primaryMatch[1].trim();
  }

  return cleanedText;
}

function formatActionType(actionType) {
  if (!actionType) {
    return "Proposed action";
  }

  return actionType
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

export default function ActiveIncident({
  incident,
}) {
  if (!incident) {
    return (
      <article className="dashboard-panel active-incident">
        <div className="incident-summary">
          <span>Incident command</span>

          <h4>No active incident</h4>

          <p>
            Create an incident to begin an
            evidence-grounded Aegis investigation.
          </p>
        </div>
      </article>
    );
  }

  const action = incident.proposed_action;

  const fromVersion =
    action?.parameters?.from_version;

  const toVersion =
    action?.parameters?.to_version;

  const displayStatus =
    incident.awaiting_approval
      ? "Awaiting approval"
      : incident.status
          ?.replaceAll("_", " ")
          .replace(/\b\w/g, (character) =>
            character.toUpperCase()
          ) || "Unknown";

  const hypothesis =
    extractPrimaryHypothesis(
      incident.hypothesis
    ) ||
    cleanMarkdown(
      incident.description
    ) ||
    "Aegis is investigating the incident.";

  return (
    <article className="dashboard-panel active-incident">
      <div className="incident-topline">
        <div className="incident-identity">
          <div className="service-icon">
            <Box
              size={17}
              strokeWidth={1.8}
            />
          </div>

          <div>
            <span className="incident-id">
              {formatIncidentId(
                incident.incident_id
              )}
            </span>

            <h3>
              {incident.service ||
                "Unknown service"}
            </h3>
          </div>
        </div>

        <StatusBadge
          status={
            incident.awaiting_approval
              ? "warning"
              : incident.status
          }
        >
          {displayStatus}
        </StatusBadge>
      </div>

      <div className="incident-summary">
        <span>
          {incident.status === "resolved"
            ? "Resolved incident"
            : "Active incident"}
        </span>

        <h4>
          {incident.title ||
            "Operational incident"}
        </h4>

        <p>{hypothesis}</p>
      </div>

      {Array.isArray(incident.evidence) &&
        incident.evidence.length > 0 && (
          <div className="incident-metadata">
            <div>
              <span>
                {incident.evidence.length} evidence{" "}
                {incident.evidence.length === 1
                  ? "item"
                  : "items"}{" "}
                collected
              </span>
            </div>
          </div>
        )}

      {action && (
        <div className="proposed-action-preview">
          <div>
            <span className="action-label">
              Proposed remediation
            </span>

            <strong>
              {formatActionType(
                action.action_type
              )}
            </strong>
          </div>

          {(fromVersion || toVersion) && (
            <div className="version-transition">
              <code>
                {fromVersion || "current"}
              </code>

              <ArrowRight size={14} />

              <code>
                {toVersion || "target"}
              </code>
            </div>
          )}
        </div>
      )}

      {fromVersion && (
        <div className="incident-metadata">
          <div>
            <GitCommitHorizontal
              size={14}
            />

            <span>
              Source deployment{" "}
              {fromVersion}
            </span>
          </div>
        </div>
      )}
    </article>
  );
}