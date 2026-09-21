const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const TOKEN_KEY = "aegis_access_token";


export function getAccessToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}


export function setAccessToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}


export function clearAccessToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}


async function parseResponse(response) {
  const contentType =
    response.headers.get("content-type");

  if (
    contentType &&
    contentType.includes("application/json")
  ) {
    return response.json();
  }

  return null;
}


export async function loginRequest(
  username,
  password
) {
  const formData = new URLSearchParams();

  formData.append("username", username);
  formData.append("password", password);

  const response = await fetch(
    `${API_BASE_URL}/auth/token`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    }
  );

  const data = await parseResponse(response);

  if (!response.ok) {
    throw new Error(
      data?.detail ||
        "Unable to sign in. Please check your credentials."
    );
  }

  if (!data?.access_token) {
    throw new Error(
      "Authentication succeeded but no access token was returned."
    );
  }

  return data;
}


export async function authenticatedRequest(
  path,
  options = {}
) {
  const token = getAccessToken();

  if (!token) {
    throw new Error(
      "Authentication required."
    );
  }

  const headers = new Headers(
    options.headers || {}
  );

  headers.set(
    "Authorization",
    `Bearer ${token}`
  );

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set(
      "Content-Type",
      "application/json"
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  const data = await parseResponse(response);

  if (response.status === 401) {
    clearAccessToken();

    window.dispatchEvent(
      new Event("aegis:unauthorized")
    );

    throw new Error(
      "Your session has expired. Please sign in again."
    );
  }

  if (!response.ok) {
    let errorMessage =
      `Request failed with status ${response.status}.`;

    if (typeof data?.detail === "string") {
      errorMessage = data.detail;
    } else if (Array.isArray(data?.detail)) {
      errorMessage = data.detail
        .map(
          (error) =>
            error.msg || "Validation error"
        )
        .join(", ");
    }

    throw new Error(errorMessage);
  }

  return data;
}


export async function getCurrentUser() {
  return authenticatedRequest("/auth/me");
}


export async function createIncident({
  title,
  description,
  service,
}) {
  return authenticatedRequest(
    "/incidents",
    {
      method: "POST",
      body: JSON.stringify({
        title,
        description,
        service,
      }),
    }
  );
}

export async function getIncident(
  incidentId
) {
  if (!incidentId) {
    throw new Error(
      "Incident ID is required."
    );
  }

  return authenticatedRequest(
    `/incidents/${encodeURIComponent(
      incidentId
    )}`
  );
}

export async function submitIncidentDecision({
  incidentId,
  decision,
  reason,
}) {
  if (!incidentId) {
    throw new Error(
      "Incident ID is required."
    );
  }

  if (
    decision !== "approved" &&
    decision !== "rejected"
  ) {
    throw new Error(
      "Decision must be approved or rejected."
    );
  }

  if (!reason?.trim()) {
    throw new Error(
      "A decision reason is required."
    );
  }

  return authenticatedRequest(
    `/incidents/${encodeURIComponent(
      incidentId
    )}/decision`,
    {
      method: "POST",
      body: JSON.stringify({
        decision,
        reason: reason.trim(),
      }),
    }
  );
}

export async function getServiceHealth(
  serviceName
) {
  if (!serviceName) {
    throw new Error(
      "Service name is required."
    );
  }

  return authenticatedRequest(
    `/services/${encodeURIComponent(
      serviceName
    )}/health`
  );
}

export async function getIncidents(
  limit = 50
) {
  return authenticatedRequest(
    `/incidents?limit=${encodeURIComponent(limit)}`
  );
}

export async function getServiceDeployments(
  serviceName
) {
  if (!serviceName) {
    throw new Error(
      "Service name is required."
    );
  }

  return authenticatedRequest(
    `/services/${encodeURIComponent(
      serviceName
    )}/deployments`
  );
}

export async function getServiceLogs(
  serviceName,
  query
) {
  if (!serviceName) {
    throw new Error(
      "Service name is required."
    );
  }

  if (!query?.trim()) {
    throw new Error(
      "Log search query is required."
    );
  }

  return authenticatedRequest(
    `/services/${encodeURIComponent(
      serviceName
    )}/logs?query=${encodeURIComponent(
      query.trim()
    )}`
  );
}

export async function getPendingApprovals() {
  return authenticatedRequest(
    "/approvals/pending"
  );
}

export async function getAuditEvents(limit = 100) {
  return authenticatedRequest(
    `/audit-events?limit=${encodeURIComponent(limit)}`
  );
}

export async function getObservabilitySummary() {
  return authenticatedRequest("/observability/summary");
}