from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

Role = Literal["patient", "doctor", "nurse", "admin"]


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    role: Literal["patient", "doctor", "nurse"]


class LoginRequest(BaseModel):
    identifier: str  # email or phone
    password: str


class VerifyOtpRequest(BaseModel):
    user_id: int
    code: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str
    role: Role
    phone_verified: bool

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterResponse(BaseModel):
    user_id: int
    # Dev-mode only: the OTP is normally sent via SMS. No SMS gateway is wired up
    # yet (Sprint 5+), so it's returned here so the flow is testable end to end.
    dev_otp_code: str


class PatientProfileIn(BaseModel):
    date_of_birth: str | None = None
    sex: str | None = None
    blood_type: str | None = None
    conditions: list[str] = []
    other_conditions: str | None = None
    medication_allergies: list[str] = []
    food_allergies: str | None = None
    medications: str | None = None


class VerificationRequestIn(BaseModel):
    full_name: str
    license_number: str
    role: Literal["doctor", "nurse", "specialist"]
    specialty: str | None = None
    years_experience: int | None = None


class VerificationRequestOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    role: str
    specialty: str | None
    license_number: str
    status: str
    submitted_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionIn(BaseModel):
    plan: Literal["basic", "personal", "family"]


class SubscriptionOut(BaseModel):
    plan: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicalRecordIn(BaseModel):
    category: Literal["Reports", "Prescriptions", "Imaging"]
    title: str
    prescriber: str
    record_date: str


class MedicalRecordOut(MedicalRecordIn):
    id: int

    model_config = {"from_attributes": True}


class FamilyMemberIn(BaseModel):
    name: str
    relation: str


class FamilyMemberOut(FamilyMemberIn):
    id: int
    status: str

    model_config = {"from_attributes": True}


class MessageIn(BaseModel):
    text: str


class MessageOut(BaseModel):
    id: int
    sender: Literal["patient", "provider"]
    text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    provider_name: str
    provider_role: str
    messages: list[MessageOut]

    model_config = {"from_attributes": True}


class InvoiceOut(BaseModel):
    id: int
    description: str
    amount_ghc: float
    invoice_date: str

    model_config = {"from_attributes": True}


class ActivityEventOut(BaseModel):
    id: int
    event_type: Literal["telehealth", "in_person", "record_upload", "prescription"]
    title: str
    subtitle: str
    note: str | None
    event_date: str

    model_config = {"from_attributes": True}


class NotificationPreferenceOut(BaseModel):
    appointments_push: bool
    appointments_email: bool
    appointments_sms: bool
    records_push: bool
    records_email: bool
    records_sms: bool
    messages_push: bool
    messages_email: bool
    messages_sms: bool
    news_push: bool
    news_email: bool
    news_sms: bool
    emergency_alerts: bool
    quiet_hours: bool

    model_config = {"from_attributes": True}


class NotificationPreferenceIn(NotificationPreferenceOut):
    pass
