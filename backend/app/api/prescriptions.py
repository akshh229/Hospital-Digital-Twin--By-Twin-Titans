"""
Prescriptions API Endpoints
Shows encrypted vs decrypted medication names
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.identity import PatientAlias
from app.schemas.prescription import PrescriptionResponse
from app.services.recovery_projection import RECOVERY_CTES

router = APIRouter()


@router.get(
    "/patients/{patient_id}/prescriptions", response_model=List[PrescriptionResponse]
)
async def get_patient_prescriptions(
    patient_id: UUID, limit: int = 100, db: Session = Depends(get_db)
):
    """Get medications for patient with both encrypted and decrypted names."""
    alias = db.query(PatientAlias).filter(PatientAlias.patient_id == patient_id).first()

    if not alias:
        raise HTTPException(status_code=404, detail="Patient not found")

    prescriptions = db.execute(
        text(
            RECOVERY_CTES
            + """
            SELECT
                cp.id,
                cp.timestamp,
                cp.age,
                cp.med_cipher_text,
                cp.med_decoded_name,
                cp.dosage,
                cp.route
            FROM clean_prescriptions cp
            JOIN recovered_demographics rd
              ON rd.patient_raw_id = cp.patient_raw_id
             AND rd.age = cp.age
            WHERE rd.patient_raw_id = :patient_raw_id
              AND rd.parity_flag = :parity_flag
            ORDER BY cp.timestamp DESC
            LIMIT :limit
            """
        ),
        {
            "patient_raw_id": alias.patient_raw_id,
            "parity_flag": alias.parity_flag,
            "limit": limit,
        },
    ).mappings()

    return [
        {
            "id": p["id"],
            "timestamp": p["timestamp"],
            "age": p["age"],
            "med_cipher_text": p["med_cipher_text"],
            "med_decoded_name": p["med_decoded_name"],
            "dosage": p["dosage"],
            "route": p["route"],
        }
        for p in prescriptions
    ]
