from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models import User, VerificationRequest
from app.schemas import VerificationRequestOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/verification-requests", response_model=list[VerificationRequestOut])
def list_verification_requests(status_filter: str | None = None, db: Session = Depends(get_db)):
    query = db.query(VerificationRequest, User).join(User, VerificationRequest.user_id == User.id)
    if status_filter:
        query = query.filter(VerificationRequest.status == status_filter)
    rows = query.order_by(VerificationRequest.submitted_at.desc()).all()
    return [
        VerificationRequestOut(
            id=req.id,
            user_id=req.user_id,
            full_name=user.full_name,
            email=user.email,
            role=req.role,
            specialty=req.specialty,
            license_number=req.license_number,
            status=req.status,
            submitted_at=req.submitted_at,
        )
        for req, user in rows
    ]


@router.post("/verification-requests/{request_id}/approve")
def approve_verification_request(request_id: int, db: Session = Depends(get_db)):
    req = db.get(VerificationRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    req.status = "approved"
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"status": "approved"}


@router.post("/verification-requests/{request_id}/reject")
def reject_verification_request(request_id: int, db: Session = Depends(get_db)):
    req = db.get(VerificationRequest, request_id)
    if req is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Request not found")
    req.status = "rejected"
    req.reviewed_at = datetime.utcnow()
    db.commit()
    return {"status": "rejected"}


@router.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    patients = db.query(User).filter(User.role == "patient").count()
    providers = db.query(User).filter(User.role.in_(["doctor", "nurse"])).count()
    pending_verifications = (
        db.query(VerificationRequest).filter(VerificationRequest.status == "pending").count()
    )
    # TODO(sprint-5+): real consultation/response-time/satisfaction/revenue metrics
    # once appointments, messaging, and billing exist. These four are genuinely
    # computed from the database now; the rest of the dashboard is still mock data.
    return {
        "total_users": total_users,
        "patients": patients,
        "providers": providers,
        "pending_verifications": pending_verifications,
    }
