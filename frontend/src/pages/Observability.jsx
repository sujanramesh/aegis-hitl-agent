import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CheckCircle2,
  Clock3,
  RefreshCw,
  ShieldCheck,
  Workflow,
} from "lucide-react";

import { getObservabilitySummary } from "../services/api.js";


function sumValues(samples = []) {
  return samples.reduce(
    (total, sample) =>
      total + Number(sample.value || 0),
    0
  );
}


function milliseconds(seconds) {
  return `${(Number(seconds || 0) * 1000).toFixed(1)} ms`;
}


function formatLabel(value) {
  if (!value) return "Unknown";

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}


function Observability() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");


  async function loadSummary() {
    setLoading(true);
    setError("");

    try {
      const data =
        await getObservabilitySummary();

      setSummary(data);
    } catch (requestError) {
      setError(
        requestError.message ||
          "Unable to load operational metrics."
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(() => {
    loadSummary();
  }, []);


  const metrics = useMemo(() => {
    if (!summary) {
      return {
        requests: 0,
        incidents: 0,
        approvals: 0,
        recoveries: 0,
        averageHttpLatency: 0,
      };
    }

    const httpRequests = sumValues(
      summary.http_requests
    );

    const incidents = sumValues(
      summary.incidents
    );

    const approvals = sumValues(
      summary.approval_decisions
    );

    const recoveries = (
      summary.recovery_verifications || []
    )
      .filter(
        (sample) =>
          sample.labels?.outcome ===
          "recovered"
      )
      .reduce(
        (total, sample) =>
          total +
          Number(sample.value || 0),
        0
      );

    const latencyEntries =
      summary.http_latency || [];

    const totalLatencyCount =
      latencyEntries.reduce(
        (total, entry) =>
          total +
          Number(entry.count || 0),
        0
      );

    const totalLatencySeconds =
      latencyEntries.reduce(
        (total, entry) =>
          total +
          Number(entry.sum_seconds || 0),
        0
      );

    const averageHttpLatency =
      totalLatencyCount > 0
        ? totalLatencySeconds /
          totalLatencyCount
        : 0;

    return {
      requests: httpRequests,
      incidents,
      approvals,
      recoveries,
      averageHttpLatency,
    };
  }, [summary]);


  const requestRows = useMemo(() => {
    return [...(summary?.http_requests || [])]
      .sort(
        (a, b) =>
          Number(b.value || 0) -
          Number(a.value || 0)
      )
      .slice(0, 12);
  }, [summary]);


  const workflowRows = useMemo(() => {
    return [...(summary?.workflow_latency || [])]
      .sort(
        (a, b) =>
          Number(b.count || 0) -
          Number(a.count || 0)
      );
  }, [summary]);


  return (
    <div className="observability-page">
      <div className="page-heading observability-heading">
        <div>
          <div className="eyebrow">
            Runtime telemetry
          </div>

          <h1>Observability</h1>

          <p>
            Operational telemetry for Aegis API traffic,
            workflow execution, human authorization, and
            verified recovery.
          </p>
        </div>

        <button
          className="button observability-refresh"
          type="button"
          onClick={loadSummary}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? "observability-refresh-icon spinning"
                : "observability-refresh-icon"
            }
          />

          {loading ? "Refreshing" : "Refresh"}
        </button>
      </div>

      {error && (
        <div className="observability-error">
          {error}
        </div>
      )}

      <div className="observability-metrics">
        <div className="observability-metric">
          <div className="observability-metric-icon">
            <Activity size={17} />
          </div>

          <div>
            <span>HTTP requests</span>
            <strong>
              {loading ? "—" : metrics.requests}
            </strong>
          </div>
        </div>

        <div className="observability-metric">
          <div className="observability-metric-icon">
            <Workflow size={17} />
          </div>

          <div>
            <span>Incidents started</span>
            <strong>
              {loading ? "—" : metrics.incidents}
            </strong>
          </div>
        </div>

        <div className="observability-metric">
          <div className="observability-metric-icon">
            <ShieldCheck size={17} />
          </div>

          <div>
            <span>Human decisions</span>
            <strong>
              {loading ? "—" : metrics.approvals}
            </strong>
          </div>
        </div>

        <div className="observability-metric">
          <div className="observability-metric-icon">
            <CheckCircle2 size={17} />
          </div>

          <div>
            <span>Verified recoveries</span>
            <strong>
              {loading ? "—" : metrics.recoveries}
            </strong>
          </div>
        </div>

        <div className="observability-metric">
          <div className="observability-metric-icon">
            <Clock3 size={17} />
          </div>

          <div>
            <span>Avg API latency</span>
            <strong>
              {loading
                ? "—"
                : milliseconds(
                    metrics.averageHttpLatency
                  )}
            </strong>
          </div>
        </div>
      </div>

      <div className="observability-grid">
        <section className="dashboard-panel observability-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">
                API telemetry
              </div>

              <h2>Request activity</h2>
            </div>
          </div>

          {loading ? (
            <div className="observability-state">
              Loading request metrics…
            </div>
          ) : requestRows.length === 0 ? (
            <div className="observability-state">
              No request metrics recorded.
            </div>
          ) : (
            <div className="observability-table-wrapper">
              <table className="observability-table">
                <thead>
                  <tr>
                    <th>Method</th>
                    <th>Route</th>
                    <th>Status</th>
                    <th>Requests</th>
                  </tr>
                </thead>

                <tbody>
                  {requestRows.map(
                    (sample, index) => (
                      <tr
                        key={`${sample.labels?.method}-${sample.labels?.path}-${sample.labels?.status_code}-${index}`}
                      >
                        <td>
                          <span className="http-method">
                            {sample.labels?.method ||
                              "—"}
                          </span>
                        </td>

                        <td>
                          <span className="metric-route">
                            {sample.labels?.path ||
                              "—"}
                          </span>
                        </td>

                        <td>
                          <span className="metric-status">
                            {sample.labels
                              ?.status_code || "—"}
                          </span>
                        </td>

                        <td>
                          {Number(
                            sample.value || 0
                          )}
                        </td>
                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="dashboard-panel observability-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">
                Agent runtime
              </div>

              <h2>Workflow latency</h2>
            </div>
          </div>

          {loading ? (
            <div className="observability-state">
              Loading workflow metrics…
            </div>
          ) : workflowRows.length === 0 ? (
            <div className="observability-state">
              No workflow latency recorded.
            </div>
          ) : (
            <div className="workflow-metric-list">
              {workflowRows.map(
                (entry, index) => (
                  <div
                    className="workflow-metric-row"
                    key={`${entry.labels?.operation}-${index}`}
                  >
                    <div>
                      <strong>
                        {formatLabel(
                          entry.labels?.operation
                        )}
                      </strong>

                      <span>
                        {Number(
                          entry.count || 0
                        )}{" "}
                        observations
                      </span>
                    </div>

                    <div className="workflow-latency-value">
                      <span>Average</span>

                      <strong>
                        {milliseconds(
                          entry.average_seconds
                        )}
                      </strong>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </section>
      </div>

      <div className="observability-grid">
        <section className="dashboard-panel observability-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">
                Human-in-the-loop
              </div>

              <h2>Approval decisions</h2>
            </div>
          </div>

          <div className="operational-breakdown">
            {(summary?.approval_decisions || [])
              .length === 0 &&
            !loading ? (
              <div className="observability-state">
                No approval decisions recorded.
              </div>
            ) : (
              (summary?.approval_decisions || []).map(
                (sample, index) => (
                  <div
                    className="breakdown-row"
                    key={`${sample.labels?.decision}-${index}`}
                  >
                    <span>
                      {formatLabel(
                        sample.labels?.decision
                      )}
                    </span>

                    <strong>
                      {Number(
                        sample.value || 0
                      )}
                    </strong>
                  </div>
                )
              )
            )}
          </div>
        </section>

        <section className="dashboard-panel observability-panel">
          <div className="panel-heading">
            <div>
              <div className="panel-kicker">
                Remediation
              </div>

              <h2>Recovery verification</h2>
            </div>
          </div>

          <div className="operational-breakdown">
            {(summary?.recovery_verifications ||
              []).length === 0 &&
            !loading ? (
              <div className="observability-state">
                No recovery checks recorded.
              </div>
            ) : (
              (
                summary?.recovery_verifications ||
                []
              ).map((sample, index) => (
                <div
                  className="breakdown-row"
                  key={`${sample.labels?.outcome}-${index}`}
                >
                  <span>
                    {formatLabel(
                      sample.labels?.outcome
                    )}
                  </span>

                  <strong>
                    {Number(
                      sample.value || 0
                    )}
                  </strong>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

export default Observability;