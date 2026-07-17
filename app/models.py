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
