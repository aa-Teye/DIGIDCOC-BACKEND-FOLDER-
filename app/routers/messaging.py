import os

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Conversation, Message, User
from app.schemas import ConversationOut, MessageIn, MessageOut

router = APIRouter(prefix="/patients/me", tags=["patient-messaging"])

# See app/routers/records.py for the rationale — same toggle, same reasoning.
SEED_DEMO_DATA = os.getenv("SEED_DEMO_DATA", "true").lower() == "true"


def _require_patient(user: User) -> None:
    if user.role != "patient":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only patient accounts have conversations")


# TODO(sprint-11+): demo seed data, same reasoning as records.py — a fresh
# signup gets a starter inbox instead of an empty screen. These conversations
# aren't tied to a real assigned-doctor relationship yet (no such model exists),
# so provider replies are canned rather than sent by an actual other user.
_SEED_CONVERSATIONS = [
    (
        "Dr. Derrick",
        "General Practitioner",
        [
            ("provider", "Good morning! I've reviewed your latest lab results."),
            (
                "provider",
                "Your blood work results look great overall, cholesterol is trending down nicely.",
            ),
        ],
    ),
    (
        "Dr. Abenea Owusu",
        "Cardiologist",
        [
            ("provider", "How are you feeling since we adjusted your medication?"),
            ("patient", "Much better, fewer palpitations."),
            ("provider", "That's great news. Let's schedule a follow-up in 2 weeks."),
        ],
    ),
    (
        "Nurse Adjoa Boateng",
        "Care Coordinator",
        [("provider", "Confirmed your home visit for Friday at 2:00 PM.")],
    ),
]


def _seed_conversations(db: Session, patient_id: int) -> None:
    for provider_name, provider_role, messages in _SEED_CONVERSATIONS:
        convo = Conversation(patient_id=patient_id, provider_name=provider_name, provider_role=provider_role)
        db.add(convo)
        db.flush()  # get convo.id before inserting messages
        for sender, text in messages:
            db.add(Message(conversation_id=convo.id, sender=sender, text=text))
    db.commit()


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _require_patient(current_user)
    conversations = (
        db.query(Conversation)
        .filter(Conversation.patient_id == current_user.id)
        .order_by(Conversation.id)
        .all()
    )
    if not conversations and SEED_DEMO_DATA:
        _seed_conversations(db, current_user.id)
        conversations = (
            db.query(Conversation)
            .filter(Conversation.patient_id == current_user.id)
            .order_by(Conversation.id)
            .all()
        )
    return conversations


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    conversation_id: int,
    payload: MessageIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_patient(current_user)
    convo = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.patient_id == current_user.id)
        .first()
    )
    if convo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation not found")

    message = Message(conversation_id=convo.id, sender="patient", text=payload.text)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message
