"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import alerts, devtools, operations, patients, prescriptions, vitals
from app.websocket import ops_stream, vitals_stream

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
app.include_router(operations.router, prefix="/api", tags=["operations"])
app.include_router(vitals_stream.router, prefix="/ws", tags=["websocket"])
app.include_router(ops_stream.router, prefix="/ws/ops", tags=["operations-websocket"])


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "st-jude-icu-digital-twin-backend",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "St. Jude ICU Digital Twin API",
        "docs": "/docs",
        "health": "/health",
        "operations_overview": "/api/ops/overview",
    }
