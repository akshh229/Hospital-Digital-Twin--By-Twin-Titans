"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import alerts, devtools, patients, prescriptions, vitals
from app.websocket import vitals_stream

app = FastAPI(
    title=settings.APP_NAME,
    description="Medical forensic recovery dashboard for St. Jude's Research Hospital",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(patients.router, prefix="/api", tags=["patients"])
app.include_router(vitals.router, prefix="/api", tags=["vitals"])
app.include_router(prescriptions.router, prefix="/api", tags=["prescriptions"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(devtools.router, prefix="/api", tags=["devtools"])
app.include_router(vitals_stream.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "lazarus-backend", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Lazarus Medical Forensic Recovery System API",
        "docs": "/docs",
        "health": "/health",
    }
