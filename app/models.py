from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    # Naive UTC, not tz-aware: SQLite silently drops tzinfo on round-trip, which
    # breaks naive/aware comparisons later. Keep every DB timestamp naive-UTC
    # consistently (this still works fine once DATABASE_URL points at Postgres).
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))  # patient | doctor | nurse | admin
    phone_verified: Mapped[bool] = mapped_column(default=False)
    otp_code: Mapped[str | None] = mapped_column(String(6), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    patient_profile: Mapped["PatientProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    verification_request: Mapped["VerificationRequest | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    date_of_birth: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sex: Mapped[str | None] = mapped_column(String(16), nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(8), nullable=True)
    conditions: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated
    other_conditions: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    medication_allergies: Mapped[str | None] = mapped_column(String(500), nullable=True)
    food_allergies: Mapped[str | None] = mapped_column(String(500), nullable=True)
    medications: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    user: Mapped["User"] = relationship(back_populates="patient_profile")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    role: Mapped[str] = mapped_column(String(16))  # doctor | nurse | specialist
    license_number: Mapped[str] = mapped_column(String(64))
    specialty: Mapped[str | None] = mapped_column(String(120), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | approved | rejected
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="verification_request")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    plan: Mapped[str] = mapped_column(String(16))  # basic | personal | family
    # TODO(sprint-5+): real values once Paystack is wired up. No PAYSTACK_SECRET_KEY
    # exists yet, so nothing here is ever actually charged.
    status: Mapped[str] = mapped_column(String(24), default="pending_payment")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    user: Mapped["User"] = relationship(back_populates="subscription")


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(24))  # Reports | Prescriptions | Imaging
    title: Mapped[str] = mapped_column(String(255))
    prescriber: Mapped[str] = mapped_column(String(255))
    record_date: Mapped[str] = mapped_column(String(32))  # display string, e.g. "Oct 15, 2024"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class FamilyMember(Base):
    __tablename__ = "family_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    primary_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    relation: Mapped[str] = mapped_column(String(32))  # Spouse | Child | ...
    status: Mapped[str] = mapped_column(String(24), default="Active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider_name: Mapped[str] = mapped_column(String(255))
    provider_role: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    sender: Mapped[str] = mapped_column(String(16))  # patient | provider
    text: Mapped[str] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    description: Mapped[str] = mapped_column(String(255))
    amount_ghc: Mapped[float] = mapped_column()
    invoice_date: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ActivityEvent(Base):
    __tablename__ = "activity_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(24))  # telehealth|in_person|record_upload|prescription
    title: Mapped[str] = mapped_column(String(255))
    subtitle: Mapped[str] = mapped_column(String(255))
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    event_date: Mapped[str] = mapped_column(String(32))  # display string, e.g. "Oct 24, 2024 · 10:30 AM"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    appointments_push: Mapped[bool] = mapped_column(default=True)
    appointments_email: Mapped[bool] = mapped_column(default=True)
    appointments_sms: Mapped[bool] = mapped_column(default=True)
    records_push: Mapped[bool] = mapped_column(default=True)
    records_email: Mapped[bool] = mapped_column(default=True)
    records_sms: Mapped[bool] = mapped_column(default=False)
    messages_push: Mapped[bool] = mapped_column(default=True)
    messages_email: Mapped[bool] = mapped_column(default=True)
    messages_sms: Mapped[bool] = mapped_column(default=False)
    news_push: Mapped[bool] = mapped_column(default=False)
    news_email: Mapped[bool] = mapped_column(default=False)
    news_sms: Mapped[bool] = mapped_column(default=False)
    emergency_alerts: Mapped[bool] = mapped_column(default=True)
    quiet_hours: Mapped[bool] = mapped_column(default=True)
