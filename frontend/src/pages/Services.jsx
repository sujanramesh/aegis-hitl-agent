import {
    FileText,
    GitBranch,
    RefreshCw,
    Search,
    Server,
  } from "lucide-react";
  import {
    useCallback,
    useEffect,
    useState,
  } from "react";
  
  import ServiceHealth from "../components/incidents/ServiceHealth";
  import StatusBadge from "../components/common/StatusBadge";
  import {
    getServiceDeployments,
    getServiceLogs,
  } from "../services/api.js";
  
  const SERVICE_NAMES = [
    "payment-service",
    "auth-service",
    "order-service",
  ];
  
  function formatDate(value) {
    if (!value) {
      return "—";
    }
  
    const date = new Date(value);
  
    if (Number.isNaN(date.getTime())) {
      return value;
    }
  
    return date.toLocaleString([], {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  
  export default function Services() {
    const [selectedService, setSelectedService] =
      useState("payment-service");
  
    const [deployments, setDeployments] =
      useState([]);
  
    const [logs, setLogs] =
      useState([]);
  
    const [logQuery, setLogQuery] =
      useState("ERROR");
  
    const [
      isLoadingDeployments,
      setIsLoadingDeployments,
    ] = useState(true);
  
    const [
      isSearchingLogs,
      setIsSearchingLogs,
    ] = useState(false);
  
    const [
      deploymentError,
      setDeploymentError,
    ] = useState("");
  
    const [logError, setLogError] =
      useState("");
  
    const loadDeployments = useCallback(
      async (serviceName) => {
        setIsLoadingDeployments(true);
        setDeploymentError("");
  
        try {
          const data =
            await getServiceDeployments(
              serviceName
            );
  
          setDeployments(
            Array.isArray(data)
              ? data
              : []
          );
        } catch (error) {
          setDeploymentError(
            error.message ||
              "Unable to load deployments."
          );
  
          setDeployments([]);
        } finally {
          setIsLoadingDeployments(false);
        }
      },
      []
    );
  
    const searchServiceLogs = useCallback(
      async (serviceName, query) => {
        const cleanQuery =
          query.trim();
  
        if (!cleanQuery) {
          setLogError(
            "Enter a log level or message to search."
          );
          return;
        }
  
        setIsSearchingLogs(true);
        setLogError("");
  
        try {
          const data =
            await getServiceLogs(
              serviceName,
              cleanQuery
            );
  
          setLogs(
            Array.isArray(data)
              ? data
              : []
          );
        } catch (error) {
          setLogError(
            error.message ||
              "Unable to search service logs."
          );
  
          setLogs([]);
        } finally {
          setIsSearchingLogs(false);
        }
      },
      []
    );
  
    useEffect(() => {
      loadDeployments(
        selectedService
      );
  
      setLogs([]);
      setLogError("");
    }, [
      selectedService,
      loadDeployments,
    ]);
  
    function handleLogSearch(event) {
      event.preventDefault();
  
      searchServiceLogs(
        selectedService,
        logQuery
      );
    }
  
    return (
      <>
        <div className="services-heading">
          <div className="page-heading">
            <span className="eyebrow">
              Infrastructure
            </span>
  
            <h1>Services</h1>
  
            <p>
              Inspect live service health,
              deployment history and
              operational logs.
            </p>
          </div>
        </div>
  
        <section className="services-health-section">
          <ServiceHealth />
        </section>
  
        <section className="service-inspection-toolbar">
          <div className="service-inspection-label">
            <div className="service-inspection-icon">
              <Server size={16} />
            </div>
  
            <div>
              <span className="panel-kicker">
                Service inspection
              </span>
  
              <strong>
                Infrastructure target
              </strong>
            </div>
          </div>
  
          <select
            className="service-selector"
            value={selectedService}
            onChange={(event) =>
              setSelectedService(
                event.target.value
              )
            }
            aria-label="Select service"
          >
            {SERVICE_NAMES.map(
              (serviceName) => (
                <option
                  key={serviceName}
                  value={serviceName}
                >
                  {serviceName}
                </option>
              )
            )}
          </select>
        </section>
  
        <section className="services-detail-grid">
          <article className="dashboard-panel services-detail-panel">
            <div className="panel-heading">
              <div>
                <span className="panel-kicker">
                  Deployments
                </span>
  
                <h3>Recent releases</h3>
              </div>
  
              <button
                type="button"
                className="service-refresh"
                onClick={() =>
                  loadDeployments(
                    selectedService
                  )
                }
                disabled={
                  isLoadingDeployments
                }
              >
                <RefreshCw
                  size={15}
                  className={
                    isLoadingDeployments
                      ? "spinner"
                      : ""
                  }
                />
  
                <span>Refresh</span>
              </button>
            </div>
  
            {deploymentError ? (
              <div
                className="incident-form__error"
                role="alert"
              >
                <span>
                  {deploymentError}
                </span>
              </div>
            ) : isLoadingDeployments ? (
              <div className="service-detail-state">
                <RefreshCw
                  size={17}
                  className="spinner"
                />
  
                <span>
                  Loading deployments...
                </span>
              </div>
            ) : deployments.length === 0 ? (
              <div className="service-detail-state">
                <GitBranch size={18} />
  
                <div>
                  <strong>
                    No deployments recorded
                  </strong>
  
                  <span>
                    No release history is
                    available for{" "}
                    {selectedService}.
                  </span>
                </div>
              </div>
            ) : (
              <div className="deployment-list">
                {deployments.map(
                  (deployment) => (
                    <div
                      className="deployment-row"
                      key={`${deployment.version}-${deployment.deployed_at}`}
                    >
                      <div className="deployment-version">
                        <div className="deployment-icon">
                          <GitBranch size={14} />
                        </div>
  
                        <div>
                          <strong>
                            {deployment.version}
                          </strong>
  
                          <span>
                            {formatDate(
                              deployment.deployed_at
                            )}
                          </span>
                        </div>
                      </div>
  
                      <StatusBadge
                        status={
                          deployment.status
                        }
                      >
                        {deployment.status}
                      </StatusBadge>
                    </div>
                  )
                )}
              </div>
            )}
          </article>
  
          <article className="dashboard-panel services-detail-panel">
            <div className="panel-heading">
              <div>
                <span className="panel-kicker">
                  Runtime logs
                </span>
  
                <h3>Log search</h3>
              </div>
  
              <FileText
                size={17}
                className="panel-heading-icon"
              />
            </div>
  
            <form
              className="service-log-search"
              onSubmit={handleLogSearch}
            >
              <div className="service-log-input">
                <Search size={15} />
  
                <input
                  type="text"
                  value={logQuery}
                  onChange={(event) =>
                    setLogQuery(
                      event.target.value
                    )
                  }
                  placeholder="ERROR, WARN, credential..."
                  disabled={isSearchingLogs}
                />
              </div>
  
              <button
                type="submit"
                className="button button--secondary"
                disabled={isSearchingLogs}
              >
                {isSearchingLogs ? (
                  <RefreshCw
                    size={15}
                    className="spinner"
                  />
                ) : (
                  <Search size={15} />
                )}
  
                {isSearchingLogs
                  ? "Searching"
                  : "Search"}
              </button>
            </form>
  
            {logError && (
              <div
                className="incident-form__error"
                role="alert"
              >
                <span>{logError}</span>
              </div>
            )}
  
            {!logError &&
              !isSearchingLogs &&
              logs.length === 0 && (
                <div className="service-detail-state">
                  <FileText size={18} />
  
                  <div>
                    <strong>
                      Search operational logs
                    </strong>
  
                    <span>
                      Query logs for{" "}
                      {selectedService} by
                      level or message.
                    </span>
                  </div>
                </div>
              )}
  
            {logs.length > 0 && (
              <div className="service-log-list">
                {logs.map(
                  (log, index) => (
                    <div
                      className="service-log-entry"
                      key={`${log.timestamp}-${index}`}
                    >
                      <div className="service-log-meta">
                        <span
                          className={`log-level log-level--${log.level?.toLowerCase()}`}
                        >
                          {log.level}
                        </span>
  
                        <span>
                          {formatDate(
                            log.timestamp
                          )}
                        </span>
                      </div>
  
                      <p>
                        {log.message}
                      </p>
                    </div>
                  )
                )}
              </div>
            )}
          </article>
        </section>
      </>
    );
  }