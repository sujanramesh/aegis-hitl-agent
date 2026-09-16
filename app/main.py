from fastapi import FastAPI

from app.models import IncidentRequest
from app.tools.service_health import get_service_health
from app.tools.deployments import get_recent_deployments
from app.tools.log_search import search_logs


app = FastAPI(
    title="Aegis",
    description="Human-in-the-Loop AI Operations Agent",
    version="0.1.0"
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "aegis"
    }


@app.post("/incidents")
def create_incident(incident: IncidentRequest):
    return {
        "message": "Incident received",
        "incident": incident
    }


@app.get("/services/{service_name}/health")
def service_health(service_name: str):
    return get_service_health(service_name)

@app.get("/services/{service_name}/deployments")
def recent_deployments(service_name: str):
    return get_recent_deployments(service_name)

@app.get("/services/{service_name}/logs")
def service_logs(service_name: str, query: str):
    return search_logs(service_name, query)