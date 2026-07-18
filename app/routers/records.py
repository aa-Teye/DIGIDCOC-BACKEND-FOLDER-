from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import ActivityEvent, FamilyMember, Invoice, MedicalRecord, NotificationPreference, User
from app.schemas import (
    ActivityEventOut,
    FamilyMemberIn,
    FamilyMemberOut,
    InvoiceOut,
    MedicalRecordIn,
    MedicalRecordOut,
    NotificationPreferenceIn,
    NotificationPreferenceOut,
)

router = APIRouter(prefix="/patients/me", tags=["patient-records"])


def _require_patient(user: User) -> None:
    if user.role != "patient":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patient accounts have this data")


# TODO(sprint-11+): this is demo/getting-started seed data so a freshly signed-up
# patient doesn't land on an empty screen during a demo. Drop before real launch —
# real patients should start with nothing until a provider/lab actually creates it.
_SEED_RECORDS = [
    ("Reports", "Comprehensive Metabolic Panel", "City Lab Diagnostics", "Oct 15, 2024"),
    ("Prescriptions", "Lisinopril 10mg Prescription", "Dr. Derrick", "Oct 12, 2024"),
    ("Imaging", "Chest X-Ray", "Accra Diagnostic Imaging", "Sep 28, 2024"),
    ("Reports", "Annual Physical Summary", "Dr. Derrick", "Sep 10, 2024"),
    ("Prescriptions", "Atorvastatin 20mg Prescription", "Dr. Abenea Owusu", "Aug 30, 2024"),
    ("Imaging", "Abdominal Ultrasound", "Accra Diagnostic Imaging", "Jul 22, 2024"),
]

_SEED_FAMILY = [
    ("Mark Owusu", "Spouse", "Active"),
    ("Leo Owusu", "Child", "Needs update"),
]

_SEED_ACTIVITY = [
    (
        "telehealth",
        "Follow-up Consultation",
        "Dr. Derrick, Primary Care",
        None,
        "Oct 24, 2024 · 10:30 AM",
    ),
    (
        "in_person",
        "Immunization Administration",
        "Nurse Adjoa Boateng, RN",
        "Annual influenza vaccine administered in left deltoid. Patient observed for 15 minutes post-injection with no adverse reactions.",
        "Oct 20, 2024 · 2:15 PM",
    ),
    (
        "record_upload",
        "Comprehensive Metabolic Panel",
        "Uploaded from City Lab Diagnostics",
        None,
        "Oct 15, 2024 · 9:00 AM",
    ),
    (
        "prescription",
        "Prescription Renewed",
        "Lisinopril 10mg - 90 Day Supply",
        None,
        "Oct 10, 2024 · 4:45 PM",
    ),
]

_SEED_INVOICES = [
    ("Oct 15, 2024", "Family Package - Monthly", 380.00),
    ("Sep 15, 2024", "Family Package - Monthly", 380.00),
    ("Aug 15, 2024", "Family Package - Monthly", 380.00),
    ("Jul 15, 2024", "Family Package - Monthly", 380.00),
    ("Jun 15, 2024", "Pediatrician Consultation (Copay)", 70.00),
]


@router.get("/records", response_model=list[MedicalRecordOut])
def list_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_patient(current_user)
    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.patient_id == current_user.id)
        .order_by(MedicalRecord.id.desc())
        .all()
    )
    if not records:
        for category, title, prescriber, record_date in _SEED_RECORDS:
            db.add(
                MedicalRecord(
                    patient_id=current_user.id,
                    category=category,
                    title=title,
                    prescriber=prescriber,
                    record_date=record_date,
                )
            )
        db.commit()
        records = (
            db.query(MedicalRecord)
            .filter(MedicalRecord.patient_id == current_user.id)
            .order_by(MedicalRecord.id.desc())
            .all()
        )
    return records


@router.post("/records", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
def add_record(
    payload: MedicalRecordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    record = MedicalRecord(patient_id=current_user.id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/family", response_model=list[FamilyMemberOut])
def list_family(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_patient(current_user)
    members = (
        db.query(FamilyMember)
        .filter(FamilyMember.primary_user_id == current_user.id)
        .order_by(FamilyMember.id)
        .all()
    )
    if not members:
        for name, relation, member_status in _SEED_FAMILY:
            db.add(
                FamilyMember(
                    primary_user_id=current_user.id,
                    name=name,
                    relation=relation,
                    status=member_status,
                )
            )
        db.commit()
        members = (
            db.query(FamilyMember)
            .filter(FamilyMember.primary_user_id == current_user.id)
            .order_by(FamilyMember.id)
            .all()
        )
    return members


@router.post("/family", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED)
def add_family_member(
    payload: FamilyMemberIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    existing_count = (
        db.query(FamilyMember).filter(FamilyMember.primary_user_id == current_user.id).count()
    )
    if existing_count >= 4:  # + the primary account holder = 5, matching the Family Package cap
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Family plan is at its 5-member limit")
    member = FamilyMember(primary_user_id=current_user.id, status="Active", **payload.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("/activity", response_model=list[ActivityEventOut])
def list_activity(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_patient(current_user)
    events = (
        db.query(ActivityEvent)
        .filter(ActivityEvent.patient_id == current_user.id)
        .order_by(ActivityEvent.id.asc())  # seed data is listed newest-first already
        .all()
    )
    if not events:
        for event_type, title, subtitle, note, event_date in _SEED_ACTIVITY:
            db.add(
                ActivityEvent(
                    patient_id=current_user.id,
                    event_type=event_type,
                    title=title,
                    subtitle=subtitle,
                    note=note,
                    event_date=event_date,
                )
            )
        db.commit()
        events = (
            db.query(ActivityEvent)
            .filter(ActivityEvent.patient_id == current_user.id)
            .order_by(ActivityEvent.id.asc())
            .all()
        )
    return events


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_patient(current_user)
    invoices = (
        db.query(Invoice).filter(Invoice.user_id == current_user.id).order_by(Invoice.id.desc()).all()
    )
    if not invoices:
        for invoice_date, description, amount in _SEED_INVOICES:
            db.add(
                Invoice(
                    user_id=current_user.id,
                    description=description,
                    amount_ghc=amount,
                    invoice_date=invoice_date,
                )
            )
        db.commit()
        invoices = (
            db.query(Invoice)
            .filter(Invoice.user_id == current_user.id)
            .order_by(Invoice.id.desc())
            .all()
        )
    return invoices


def _get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
    prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("/notification-preferences", response_model=NotificationPreferenceOut)
def get_notification_preferences(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return _get_or_create_preferences(db, current_user.id)


@router.put("/notification-preferences", response_model=NotificationPreferenceOut)
def update_notification_preferences(
    payload: NotificationPreferenceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = _get_or_create_preferences(db, current_user.id)
    for field, value in payload.model_dump().items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs
