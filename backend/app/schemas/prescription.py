"""Prescription API response schemas"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class PrescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    age: int
    med_cipher_text: str
    med_decoded_name: Optional[str] = None
    dosage: Optional[str] = None
    route: Optional[str] = None
