# backend/main.py
# ================================================================
# FASTAPI APPLICATION — Entry point backend Aspiralytica
# ================================================================

import json
import os
import hashlib
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import (
    init_db,
    insert_report, get_all_reports,
    get_report_by_id, delete_report, update_report_status,
    create_user, get_user_by_email,
)
from models import (
    AnalyzeRequest, AnalyzeResponse,
    UpdateStatusRequest,
    RegisterRequest, LoginRequest,
    LoginResponse, RegisterResponse,
    DeleteResponse, MetricsResponse, HealthResponse,
)
from ml.classifier import classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aspiralytica API",
    description="AI-Powered Public Report Analysis System",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    if classifier is None:
        logger.warning(
            "⚠️  Model belum ditraining! Jalankan: python -m ml.train"
        )
    else:
        logger.info("✅ Aspiralytica API siap. Model berhasil dimuat.")


# ================================================================
# HEALTH CHECK
# ================================================================

@app.get("/", response_model=HealthResponse)
def root():
    return {
        "status": "ok",
        "message": "Aspiralytica API is running 🚀",
        "model_loaded": classifier is not None,
    }


# ================================================================
# ANALISIS LAPORAN
# ================================================================

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if classifier is None:
        raise HTTPException(
            status_code=503,
            detail="Model belum tersedia. Jalankan: python -m ml.train"
        )

    result = classifier.analyze(request.text)

    report_id = insert_report(
        text=request.text,
        sentiment=result["sentiment"],
        intent=result["intent"],
        priority=result["priority"],
        is_sarcasm=result["is_sarcasm"],
    )
    return get_report_by_id(report_id)


# ================================================================
# RIWAYAT LAPORAN
# ================================================================

@app.get("/history", response_model=list[AnalyzeResponse])
def history():
    return get_all_reports()


@app.get("/history/{report_id}", response_model=AnalyzeResponse)
def get_one(report_id: int):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    return report


@app.delete("/history/{report_id}", response_model=DeleteResponse)
def delete_one(report_id: int):
    if not get_report_by_id(report_id):
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    delete_report(report_id)
    return {"message": "Laporan berhasil dihapus"}


@app.patch("/history/{report_id}/status", response_model=AnalyzeResponse)
def update_status(report_id: int, request: UpdateStatusRequest):
    valid = ["menunggu", "diproses", "selesai"]
    if request.status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Status harus salah satu dari: {valid}"
        )
    if not get_report_by_id(report_id):
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    update_report_status(report_id, request.status)
    return get_report_by_id(report_id)


# ================================================================
# MODEL METRICS (berguna untuk paper/skripsi)
# ================================================================

@app.get("/metrics", response_model=MetricsResponse)
def get_metrics():
    """
    Mengembalikan hasil evaluasi model dari training terakhir.
    Data diambil dari ml/models/metrics.json
    """
    metrics_path = os.path.join("ml", "models", "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=404,
            detail="Metrics belum tersedia. Jalankan: python -m ml.train"
        )
    with open(metrics_path, "r") as f:
        return json.load(f)


# ================================================================
# AUTH
# ================================================================

@app.post("/auth/register", response_model=RegisterResponse)
def register(request: RegisterRequest):
    try:
        user = create_user(
            request.name.strip(),
            request.email.strip().lower(),
            request.password,
        )
        return {"message": "Akun berhasil dibuat", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    user = get_user_by_email(request.email.strip().lower())
    if not user:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    hashed = hashlib.sha256(request.password.encode()).hexdigest()
    if user["password"] != hashed:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    return {
        "message": "Login berhasil",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    }