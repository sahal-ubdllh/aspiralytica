# backend/models.py
# ================================================================
# PYDANTIC MODELS — Request & Response schema untuk FastAPI
# ================================================================
# Bertugas: validasi input/output API secara otomatis
# Dipakai oleh: main.py
# ================================================================

from pydantic import BaseModel, Field
from typing import Optional


# ── REQUEST MODELS ───────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    """Request body untuk POST /analyze"""
    text: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Teks laporan masyarakat yang akan dianalisis",
        example="Jalan di depan sekolah rusak parah sudah berminggu-minggu tidak diperbaiki",
    )


class UpdateStatusRequest(BaseModel):
    """Request body untuk PATCH /history/{id}/status"""
    status: str = Field(
        ...,
        description="Status baru laporan",
        example="diproses",
    )


class RegisterRequest(BaseModel):
    """Request body untuk POST /auth/register"""
    name: str = Field(..., min_length=2, max_length=100, example="Budi Santoso")
    email: str = Field(..., example="budi@email.com")
    password: str = Field(..., min_length=6, example="password123")


class LoginRequest(BaseModel):
    """Request body untuk POST /auth/login"""
    email: str = Field(..., example="budi@email.com")
    password: str = Field(..., example="password123")


# ── RESPONSE MODELS ──────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    """Response untuk POST /analyze dan GET /history/{id}"""
    id: int
    text: str
    sentiment: str
    intent: str
    priority: str
    is_sarcasm: bool = False
    status: str
    created_at: str


class UserResponse(BaseModel):
    """Data user tanpa password"""
    id: int
    name: str
    email: str


class LoginResponse(BaseModel):
    """Response untuk POST /auth/login"""
    message: str
    user: UserResponse


class RegisterResponse(BaseModel):
    """Response untuk POST /auth/register"""
    message: str
    user: UserResponse


class DeleteResponse(BaseModel):
    """Response untuk DELETE /history/{id}"""
    message: str


class MetricsResponse(BaseModel):
    """Response untuk GET /metrics — hasil evaluasi model"""
    trained_at: str
    sentiment: dict
    intent: dict


class HealthResponse(BaseModel):
    """Response untuk GET / — health check"""
    status: str
    message: str
    model_loaded: bool