from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import hashlib

from database import (
    init_db, insert_report, get_all_reports,
    get_report_by_id, delete_report, update_report_status,
    create_user, get_user_by_email,
)
from ml.classifier import classifier

app = FastAPI(title="Aspiralytica API", version="1.0.0")

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

# =============================================
# MODELS
# =============================================

class AnalyzeRequest(BaseModel):
    text: str

class AnalyzeResponse(BaseModel):
    id: int
    text: str
    sentiment: str
    intent: str
    priority: str
    status: str
    created_at: str

class UpdateStatusRequest(BaseModel):
    status: str  # menunggu | diproses | selesai

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# =============================================
# ENDPOINTS — Analisis
# =============================================

@app.get("/")
def root():
    return {"message": "Aspiralytica API is running 🚀"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Teks laporan tidak boleh kosong")
    if len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Teks minimal 10 karakter")

    result = classifier.analyze(request.text)

    report_id = insert_report(
        text=request.text,
        sentiment=result["sentiment"],
        intent=result["intent"],
        priority=result["priority"],
    )
    return get_report_by_id(report_id)

@app.get("/history", response_model=list[AnalyzeResponse])
def history():
    return get_all_reports()

@app.get("/history/{report_id}", response_model=AnalyzeResponse)
def get_one(report_id: int):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    return report

@app.delete("/history/{report_id}")
def delete_one(report_id: int):
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    delete_report(report_id)
    return {"message": "Laporan berhasil dihapus"}

@app.patch("/history/{report_id}/status")
def update_status(report_id: int, request: UpdateStatusRequest):
    valid = ["menunggu", "diproses", "selesai"]
    if request.status not in valid:
        raise HTTPException(status_code=400, detail=f"Status harus salah satu dari: {valid}")
    report = get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Laporan tidak ditemukan")
    update_report_status(report_id, request.status)
    return get_report_by_id(report_id)

# =============================================
# ENDPOINTS — Auth
# =============================================

@app.post("/auth/register")
def register(request: RegisterRequest):
    if not request.name.strip() or not request.email.strip() or not request.password.strip():
        raise HTTPException(status_code=400, detail="Semua field wajib diisi")
    if len(request.password) < 6:
        raise HTTPException(status_code=400, detail="Password minimal 6 karakter")
    try:
        user = create_user(request.name.strip(), request.email.strip(), request.password)
        return {"message": "Akun berhasil dibuat", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
def login(request: LoginRequest):
    user = get_user_by_email(request.email.strip())
    if not user:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    hashed = hashlib.sha256(request.password.encode()).hexdigest()
    if user["password"] != hashed:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    return {
        "message": "Login berhasil",
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
    }