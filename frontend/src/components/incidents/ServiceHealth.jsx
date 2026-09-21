import {
  RefreshCw,
  Server,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import StatusBadge from "../common/StatusBadge";
import { getServiceHealth } from "../../services/api.js";

const SERVICE_NAMES = [
  "payment-service",
  "auth-service",
  "order-service",
];

function formatLatency(latency) {
  if (
    latency === null ||
    latency === undefined
  ) {
    return "—";
  }

  if (typeof latency === "number") {
    return `${latency} ms`;
  }

  return String(latency).includes("ms")
    ? String(latency)
    : `${latency} ms`;
}

export default function ServiceHealth({
  refreshKey,
}) {
  const [services, setServices] =
    useState([]);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isRefreshing, setIsRefreshing] =
    useState(false);

  const [error, setError] =
    useState("");

  const loadServices = useCallback(
    async (refreshing = false) => {
      if (refreshing) {
        setIsRefreshing(true);
      } else {
        setIsLoading(true);
      }

      setError("");

      try {
        const results =
          await Promise.all(
            SERVICE_NAMES.map(
              async (serviceName) => {
                const health =
                  await getServiceHealth(
                    serviceName
                  );

                return {
                  name:
                    health.service ||
                    health.service_name ||
                    serviceName,

                  status:
                    health.status ||
                    "unknown",

                  latency:
                    health.latency_ms ??
                    health.latency ??
                    null,
                };
              }
            )
          );

        setServices(results);
      } catch (requestError) {
        setError(
          requestError.message ||
            "Unable to load service health."
        );
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    []
  );

  useEffect(() => {
    loadServices();
  }, [loadServices, refreshKey]);

  return (
    <article className="dashboard-panel service-panel">
      <div className="panel-heading">
        <div>
          <span className="panel-kicker">
            Infrastructure
          </span>

          <h3>Service health</h3>
        </div>

        <button
          type="button"
          className="service-refresh"
          aria-label="Refresh service health"
          title="Refresh service health"
          disabled={
            isLoading ||
            isRefreshing
          }
          onClick={() =>
            loadServices(true)
          }
        >
          <RefreshCw
            size={15}
            className={
              isRefreshing
                ? "spinner"
                : ""
            }
          />

          <span>
            {isRefreshing
              ? "Refreshing"
              : "Refresh"}
          </span>
        </button>
      </div>

      {isLoading ? (
        <div className="service-state">
          <Server size={17} />

          <span>
            Loading service health...
          </span>
        </div>
      ) : error ? (
        <div
          className="incident-form__error"
          role="alert"
        >
          <span>{error}</span>
        </div>
      ) : (
        <div className="service-list">
          {services.map((service) => (
            <div
              className="service-row"
              key={service.name}
            >
              <div className="service-name">
                <strong>
                  {service.name}
                </strong>
              </div>

              <span className="service-latency">
                {formatLatency(
                  service.latency
                )}
              </span>

              <StatusBadge
                status={service.status}
              >
                {service.status}
              </StatusBadge>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}