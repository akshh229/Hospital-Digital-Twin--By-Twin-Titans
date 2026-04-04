"""Operations API for the ICU command center."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.operations import (
    OperationsOverviewResponse,
    SimulationControlRequest,
)
from app.services.operations_center import (
    apply_simulation_action,
    get_operations_overview,
)

router = APIRouter()


@router.get("/ops/overview", response_model=OperationsOverviewResponse)
def operations_overview(db: Session = Depends(get_db)):
    """Return the current hospital digital twin snapshot."""
    return get_operations_overview(db)


@router.post("/ops/control", response_model=OperationsOverviewResponse)
def control_simulation(
    payload: SimulationControlRequest,
    db: Session = Depends(get_db),
):
    """Apply a simulator action and return the refreshed operations snapshot."""
    return apply_simulation_action(
        db,
        action=payload.action,
        speed=payload.speed,
        scenario=payload.scenario,
        severity=payload.severity,
        patient_count=payload.patient_count,
        intervention_id=payload.intervention_id,
    )
