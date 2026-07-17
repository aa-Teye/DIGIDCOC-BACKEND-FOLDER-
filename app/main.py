import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, messaging, patients, providers, records
from app.security import hash_password

SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@digidoc.app")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "DigiDocAdmin123!")


def seed_admin(db):
    existing = db.query(models.User).filter(models.User.email == SEED_ADMIN_EMAIL).first()
    if existing:
        return
    db.add(
        models.User(
            full_name="Admin User",
            email=SEED_ADMIN_EMAIL,
            phone="+10000000000",
            hashed_password=hash_password(SEED_ADMIN_PASSWORD),
            role="admin",
            phone_verified=True,
        )
    )
    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin(db)
    finally:
        db.close()
    yield


app = FastAPI(title="DigiDoc API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(records.router)
app.include_router(messaging.router)
app.include_router(providers.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    return {"status": "ok"}
