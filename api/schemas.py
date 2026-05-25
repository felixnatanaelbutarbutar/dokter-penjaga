from pydantic import BaseModel, Field
from typing import List, Optional

class SourceCitation(BaseModel):
    title: str = Field(..., description="Judul dokumen referensi")
    year: int = Field(..., description="Tahun terbit dokumen")
    url: Optional[str] = Field(None, description="Tautan dokumen jika tersedia")

class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Pertanyaan medis dari pengguna")
    session_id: str = Field(default="default-session", description="ID Sesi untuk tracking dan logging")

class AskResponse(BaseModel):
    answer: str = Field(..., description="Jawaban final dari asisten medis")
    sources: List[SourceCitation] = Field(default_factory=list, description="Daftar sumber yang digunakan")
    redacted_query: str = Field(..., description="Query pengguna setelah disensor PII-nya")
    is_emergency: bool = Field(default=False, description="Flag jika terdeteksi kondisi darurat")

class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    version: str = Field(default="1.0.0")
