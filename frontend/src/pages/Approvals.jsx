import {
    CheckCircle2,
    RefreshCw,
    ShieldCheck,
  } from "lucide-react";
  import {
    useCallback,
    useEffect,
    useState,
  } from "react";
  
  import ApprovalCard from "../components/approvals/ApprovalCard";
  import { getPendingApprovals } from "../services/api.js";
  
  export default function Approvals() {
    const [
      pendingIncidents,
      setPendingIncidents,
    ] = useState([]);
  
    const [isLoading, setIsLoading] =
      useState(true);
  
    const [error, setError] =
      useState("");
  
    const loadApprovals = useCallback(
      async () => {
        setIsLoading(true);
        setError("");
  
        try {
          const incidents =
            await getPendingApprovals();
  
          setPendingIncidents(
            Array.isArray(incidents)
              ? incidents
              : []
          );
        } catch (requestError) {
          setError(
            requestError.message ||
              "Unable to load pending approvals."
          );
        } finally {
          setIsLoading(false);
        }
      },
      []
    );
  
    useEffect(() => {
      loadApprovals();
    }, [loadApprovals]);
  
    function handleDecisionCompleted(
      updatedIncident
    ) {
      setPendingIncidents(
        (currentIncidents) =>
          currentIncidents.filter(
            (incident) =>
              incident.incident_id !==
              updatedIncident.incident_id
          )
      );
    }
  
    return (
      <>
        <div className="overview-heading">
          <div className="page-heading">
            <span className="eyebrow">
              Human-in-the-loop
            </span>
  
            <h1>Approvals</h1>
  
            <p>
              Review consequential actions
              awaiting explicit human
              authorization.
            </p>
          </div>
  
          <button
            type="button"
            className="button"
            onClick={loadApprovals}
            disabled={isLoading}
          >
            <RefreshCw
              size={15}
              className={
                isLoading
                  ? "spinner"
                  : ""
              }
            />
  
            Refresh
          </button>
        </div>
  
        {error && (
          <div
            className="incident-form__error"
            role="alert"
          >
            <span>{error}</span>
          </div>
        )}
  
        <section className="approval-summary">
          <div>
            <ShieldCheck size={18} />
  
            <div>
              <span className="panel-kicker">
                Authorization queue
              </span>
  
              <strong>
                {isLoading
                  ? "Checking workflows..."
                  : `${pendingIncidents.length} pending ${
                      pendingIncidents.length === 1
                        ? "approval"
                        : "approvals"
                    }`}
              </strong>
            </div>
          </div>
  
          <span>
            Consequential operations remain
            blocked until explicitly reviewed.
          </span>
        </section>
  
        {isLoading ? (
          <section className="dashboard-panel">
            <div className="approvals-empty">
              <RefreshCw
                size={19}
                className="spinner"
              />
  
              <div>
                <strong>
                  Checking authorization queue
                </strong>
  
                <span>
                  Inspecting checkpointed
                  workflows...
                </span>
              </div>
            </div>
          </section>
        ) : pendingIncidents.length === 0 ? (
          <section className="dashboard-panel">
            <div className="approvals-empty">
              <CheckCircle2 size={20} />
  
              <div>
                <strong>
                  No approvals pending
                </strong>
  
                <span>
                  No incident is currently
                  blocked by the human
                  authorization policy.
                </span>
              </div>
            </div>
          </section>
        ) : (
          <div className="approvals-list">
            {pendingIncidents.map(
              (incident) => (
                <ApprovalCard
                  key={
                    incident.incident_id
                  }
                  incident={incident}
                  onDecisionCompleted={
                    handleDecisionCompleted
                  }
                />
              )
            )}
          </div>
        )}
      </>
    );
  }