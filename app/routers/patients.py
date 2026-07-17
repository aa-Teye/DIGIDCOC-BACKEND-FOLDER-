from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import PatientProfile, User
from app.schemas import PatientProfileIn

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/me/profile", status_code=status.HTTP_200_OK)
def save_my_profile(
    payload: PatientProfileIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patient accounts have a medical profile")

    profile = (
        db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
    )
    if profile is None:
        profile = PatientProfile(user_id=current_user.id)
        db.add(profile)

    profile.date_of_birth = payload.date_of_birth
    profile.sex = payload.sex
    profile.blood_type = payload.blood_type
    profile.conditions = ", ".join(payload.conditions) if payload.conditions else None
    profile.other_conditions = payload.other_conditions
    profile.medication_allergies = (
        ", ".join(payload.medication_allergies) if payload.medication_allergies else None
    )
    profile.food_allergies = payload.food_allergies
    profile.medications = payload.medications

    db.commit()
    return {"status": "saved"}
