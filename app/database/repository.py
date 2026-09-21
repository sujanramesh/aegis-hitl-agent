from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database.entities import (
    IncidentEntity,
    AuditEventEntity,
)


def create_incident(
    db: Session,
    incident_id: str,
    title: str,
    description: str,
    service: str,
) -> IncidentEntity:
    incident = IncidentEntity(
        id=incident_id,
        title=title,
        description=description,
        service=service,
        status="received",
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def update_incident_status(
    db: Session,
    incident_id: str,
    status: str,
) -> IncidentEntity | None:
    incident = db.get(
        IncidentEntity,
        incident_id,
    )

    if incident is None:
        return None

    incident.status = status

    db.commit()
    db.refresh(incident)

    return incident


def get_incident(
    db: Session,
    incident_id: str,
) -> IncidentEntity | None:
    return db.get(
        IncidentEntity,
        incident_id,
    )


def list_incidents(
    db: Session,
    limit: int = 50,
) -> list[IncidentEntity]:
    return (
        db.query(IncidentEntity)
        .order_by(
            desc(IncidentEntity.created_at)
        )
        .limit(limit)
        .all()
    )


def create_audit_event(
    db: Session,
    incident_id: str,
    event_type: str,
    actor: str,
    details: str | None = None,
) -> AuditEventEntity:
    event = AuditEventEntity(
        incident_id=incident_id,
        event_type=event_type,
        actor=actor,
        details=details,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


def list_audit_events(
    db: Session,
    limit: int = 100,
) -> list[AuditEventEntity]:
    return (
        db.query(AuditEventEntity)
        .order_by(
            desc(AuditEventEntity.created_at),
            desc(AuditEventEntity.id),
        )
        .limit(limit)
        .all()
    )