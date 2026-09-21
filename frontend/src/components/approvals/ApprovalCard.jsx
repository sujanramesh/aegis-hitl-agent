import {
  ArrowRight,
  LoaderCircle,
  LockKeyhole,
  ShieldAlert,
} from "lucide-react";
import { useState } from "react";

import { useAuth } from "../../context/AuthContext";
import { submitIncidentDecision } from "../../services/api.js";

export default function ApprovalCard({
  incident,
  onDecisionCompleted,
}) {
  const { hasRole } = useAuth();

  const [reason, setReason] =
    useState("");

  const [error, setError] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [pendingDecision, setPendingDecision] =
    useState(null);

  if (
    !incident ||
    !incident.awaiting_approval ||
    !incident.proposed_action
  ) {
    return null;
  }

  const canApprove = hasRole("approver");

  const action =
    incident.proposed_action;

  const fromVersion =
    action.parameters?.from_version;

  const toVersion =
    action.parameters?.to_version;

  const actionLabel =
    action.action_type
      ?.replaceAll("_", " ")
      .replace(/\b\w/g, (character) =>
        character.toUpperCase()
      ) || "Proposed action";

  async function handleDecision(decision) {
    const cleanReason = reason.trim();

    if (cleanReason.length < 3) {
      setError(
        "Provide a reason of at least 3 characters."
      );
      return;
    }

    setError("");
    setIsSubmitting(true);
    setPendingDecision(decision);

    try {
      const updatedIncident =
        await submitIncidentDecision({
          incidentId:
            incident.incident_id,
          decision,
          reason: cleanReason,
        });

      if (onDecisionCompleted) {
        onDecisionCompleted(
          updatedIncident
        );
      }
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to submit the decision."
      );
    } finally {
      setIsSubmitting(false);
      setPendingDecision(null);
    }
  }

  return (
    <article className="approval-card">
      <div className="approval-icon">
        <ShieldAlert
          size={19}
          strokeWidth={1.8}
        />
      </div>

      <div className="approval-content">
        <div className="approval-heading">
          <div>
            <span className="panel-kicker">
              Human authorization required
            </span>

            <h3>
              {actionLabel}{" "}
              {incident.service}
            </h3>
          </div>

          <span className="risk-badge">
            {incident.risk_level
              ? `${incident.risk_level} risk`
              : "Risk assessed"}
          </span>
        </div>

        <p>
          Aegis has proposed a consequential
          infrastructure mutation. Execution
          remains blocked until an authorized
          approver explicitly reviews the
          action.
        </p>

        <div className="approval-action">
          <span>
            {action.action_type}
          </span>

          {(fromVersion ||
            toVersion) && (
            <div>
              <code>
                {fromVersion || "current"}
              </code>

              <ArrowRight size={13} />

              <code>
                {toVersion || "target"}
              </code>
            </div>
          )}
        </div>

        {canApprove ? (
          <>
            <label className="approval-reason">
              <span>
                Decision reason
              </span>

              <textarea
                value={reason}
                onChange={(event) =>
                  setReason(
                    event.target.value
                  )
                }
                placeholder="Explain why this action should be approved or rejected."
                minLength={3}
                maxLength={1000}
                rows={3}
                disabled={isSubmitting}
              />
            </label>

            {error && (
              <div
                className="incident-form__error"
                role="alert"
              >
                <ShieldAlert size={16} />
                <span>{error}</span>
              </div>
            )}
          </>
        ) : (
          <div className="policy-lock">
            <LockKeyhole size={14} />

            An authorized approver must
            review this action.
          </div>
        )}

        <div className="approval-footer">
          <div className="policy-lock">
            <LockKeyhole size={14} />
            Execution blocked by HITL policy
          </div>

          {canApprove && (
            <div className="approval-buttons">
              <button
                type="button"
                className="button button--secondary"
                disabled={isSubmitting}
                onClick={() =>
                  handleDecision(
                    "rejected"
                  )
                }
              >
                {isSubmitting &&
                pendingDecision ===
                  "rejected" ? (
                  <>
                    <LoaderCircle
                      size={14}
                      className="spinner"
                    />
                    Rejecting...
                  </>
                ) : (
                  "Reject"
                )}
              </button>

              <button
                type="button"
                className="button button--primary"
                disabled={isSubmitting}
                onClick={() =>
                  handleDecision(
                    "approved"
                  )
                }
              >
                {isSubmitting &&
                pendingDecision ===
                  "approved" ? (
                  <>
                    <LoaderCircle
                      size={14}
                      className="spinner"
                    />
                    Executing...
                  </>
                ) : (
                  "Review & authorize"
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </article>
  );
}