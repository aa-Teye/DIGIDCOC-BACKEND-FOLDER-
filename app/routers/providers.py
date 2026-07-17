from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, VerificationRequest
from app.schemas import VerificationRequestIn

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/verification-requests", status_code=status.HTTP_201_CREATED)
def submit_verification_request(
    payload: VerificationRequestIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("doctor", "nurse"):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only doctor/nurse accounts submit credentials"
        )
    existing = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Verification request already submitted")

    request = VerificationRequest(
        user_id=current_user.id,
        role=payload.role,
        license_number=payload.license_number,
        specialty=payload.specialty,
        years_experience=payload.years_experience,
    )
    db.add(request)
    db.commit()
    return {"status": "submitted"}
