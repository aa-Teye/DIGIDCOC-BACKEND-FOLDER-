from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import PatientProfile, Subscription, User
from app.schemas import PatientProfileIn, SubscriptionIn, SubscriptionOut

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


# TODO(sprint-5+): this doesn't touch Paystack — PAYSTACK_SECRET_KEY isn't set,
# so there's nothing to call. Records the chosen plan as "pending_payment" so the
# rest of the app (billing page, future entitlement checks) has something real to
# read instead of nothing. Swap for a real checkout-session flow once keys exist.
@router.post("/me/subscription", response_model=SubscriptionOut)
def select_my_plan(
    payload: SubscriptionIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "patient":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patient accounts have a subscription")

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if sub is None:
        sub = Subscription(user_id=current_user.id, plan=payload.plan)
        db.add(sub)
    else:
        sub.plan = payload.plan
        sub.status = "pending_payment"

    db.commit()
    db.refresh(sub)
    return SubscriptionOut.model_validate(sub)


@router.get("/me/subscription", response_model=SubscriptionOut | None)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    return SubscriptionOut.model_validate(sub) if sub else None
