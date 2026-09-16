from pydantic import BaseModel


class IncidentRequest(BaseModel):
    title: str
    description: str
    service: str