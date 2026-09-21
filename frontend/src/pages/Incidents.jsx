import {
    AlertCircle,
    Clock,
    RefreshCw,
    Server,
  } from "lucide-react";
  import {
    useCallback,
    useEffect,
    useState,
  } from "react";
  
  import StatusBadge from "../components/common/StatusBadge";
  import {
    getIncident,
    getIncidents,
  } from "../services/api.js";
  
  function formatDate(value) {
    if (!value) {
      return "—";
    }
  
    const date = new Date(value);
  
    if (Number.isNaN(date.getTime())) {
      return "—";
    }
  
    return date.toLocaleString();
  }
  
  function formatStatus(status) {
    if (!status) {
      return "Unknown";
    }
  
    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) =>
        letter.toUpperCase()
      );
  }
  
  function shortIncidentId(id) {
    if (!id) {
      return "—";
    }
  
    return id.slice(0, 8);
  }
  
  export default function Incidents() {
    const [incidents, setIncidents] =
      useState([]);
  
    const [selectedIncident, setSelectedIncident] =
      useState(null);
  
    const [isLoading, setIsLoading] =
      useState(true);
  
    const [isLoadingDetail, setIsLoadingDetail] =
      useState(false);
  
    const [error, setError] =
      useState("");
  
    const loadIncidents = useCallback(
      async () => {
        setIsLoading(true);
        setError("");
  
        try {
          const data =
            await getIncidents(50);
  
          setIncidents(
            Array.isArray(data)
              ? data
              : []
          );
        } catch (requestError) {
          setError(
            requestError.message ||
              "Unable to load incidents."
          );
        } finally {
          setIsLoading(false);
        }
      },
      []
    );
  
    useEffect(() => {
      loadIncidents();
    }, [loadIncidents]);
  
    async function handleSelectIncident(
      incident
    ) {
      setIsLoadingDetail(true);
      setError("");
  
      try {
        const detail =
          await getIncident(
            incident.incident_id
          );
  
        setSelectedIncident(detail);
      } catch (requestError) {
        setError(
          requestError.message ||
            "Unable to load incident details."
        );
      } finally {
        setIsLoadingDetail(false);
      }
    }
  
    return (
      <>
        <div className="overview-heading">
          <div className="page-heading">
            <span className="eyebrow">
              Operations
            </span>
  
            <h1>Incidents</h1>
  
            <p>
              Review persisted incidents and
              inspect their latest workflow state.
            </p>
          </div>
  
          <button
            type="button"
            className="button"
            onClick={loadIncidents}
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
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}
  
        <section className="dashboard-panel incidents-panel">
          <div className="panel-heading">
            <div>
              <span className="panel-kicker">
                Incident registry
              </span>
  
              <h3>
                Operational incidents
              </h3>
            </div>
  
            <span className="incident-count">
              {incidents.length} records
            </span>
          </div>
  
          {isLoading ? (
            <div className="incidents-empty">
              <RefreshCw
                size={18}
                className="spinner"
              />
  
              <span>
                Loading incidents...
              </span>
            </div>
          ) : incidents.length === 0 ? (
            <div className="incidents-empty">
              <AlertCircle size={18} />
  
              <span>
                No incidents have been
                recorded.
              </span>
            </div>
          ) : (
            <div className="incident-table-wrapper">
              <table className="incident-table">
                <thead>
                  <tr>
                    <th>Incident</th>
                    <th>Service</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th />
                  </tr>
                </thead>
  
                <tbody>
                  {incidents.map(
                    (incident) => (
                      <tr
                        key={
                          incident.incident_id
                        }
                      >
                        <td>
                          <div className="incident-table__primary">
                            <strong>
                              {incident.title}
                            </strong>
  
                            <span>
                              #
                              {shortIncidentId(
                                incident.incident_id
                              )}
                            </span>
                          </div>
                        </td>
  
                        <td>
                          <div className="incident-table__service">
                            <Server size={14} />
  
                            <span>
                              {incident.service}
                            </span>
                          </div>
                        </td>
  
                        <td>
                          <StatusBadge
                            status={
                              incident.status
                            }
                          >
                            {formatStatus(
                              incident.status
                            )}
                          </StatusBadge>
                        </td>
  
                        <td>
                          <div className="incident-table__time">
                            <Clock size={14} />
  
                            <span>
                              {formatDate(
                                incident.created_at
                              )}
                            </span>
                          </div>
                        </td>
  
                        <td>
                          <button
                            type="button"
                            className="incident-inspect-button"
                            onClick={() =>
                              handleSelectIncident(
                                incident
                              )
                            }
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
  
        {isLoadingDetail && (
          <section className="dashboard-panel incident-detail-panel">
            <div className="incidents-empty">
              <RefreshCw
                size={18}
                className="spinner"
              />
  
              <span>
                Recovering workflow state...
              </span>
            </div>
          </section>
        )}
  
        {!isLoadingDetail &&
          selectedIncident && (
            <section className="dashboard-panel incident-detail-panel">
              <div className="panel-heading">
                <div>
                  <span className="panel-kicker">
                    Workflow state
                  </span>
  
                  <h3>
                    {selectedIncident.title}
                  </h3>
                </div>
  
                <StatusBadge
                  status={
                    selectedIncident.status
                  }
                >
                  {selectedIncident.awaiting_approval
                    ? "Awaiting approval"
                    : formatStatus(
                        selectedIncident.status
                      )}
                </StatusBadge>
              </div>
  
              <div className="incident-detail-grid">
                <div>
                  <span>Incident ID</span>
                  <strong>
                    {
                      selectedIncident.incident_id
                    }
                  </strong>
                </div>
  
                <div>
                  <span>Service</span>
                  <strong>
                    {
                      selectedIncident.service
                    }
                  </strong>
                </div>
  
                <div>
                  <span>Risk level</span>
                  <strong>
                    {selectedIncident.risk_level ||
                      "—"}
                  </strong>
                </div>
  
                <div>
                  <span>
                    Approval required
                  </span>
                  <strong>
                    {selectedIncident.requires_approval
                      ? "Yes"
                      : "No"}
                  </strong>
                </div>
              </div>
  
              <div className="incident-detail-description">
                <span>Description</span>
  
                <p>
                  {
                    selectedIncident.description
                  }
                </p>
              </div>
            </section>
          )}
      </>
    );
  }