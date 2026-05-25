import os
from typing import List, Dict, Any, Tuple
from anthropic import Anthropic
from config import get_settings

cfg = get_settings()

class LLMEngine:
    """
    Handles interactions with the Large Language Model (Anthropic Claude).
    Enforces OUTPUT guardrails via system prompts (GUARD-03, GUARD-04).
    """
    def __init__(self):
        # We assume anthropic_api_key is set in config / .env
        self.client = Anthropic(api_key=cfg.anthropic_api_key)
        self.model = cfg.llm_model
        
    def _build_system_prompt(self) -> str:
        return (
            "Anda adalah 'Dokter Penjaga', asisten AI medis darurat yang beroperasi "
            "dengan prinsip 'Selamatkan nyawa dulu, jawab kemudian'.\n\n"
            "ATURAN MUTLAK:\n"
            "1. JANGAN PERNAH memberikan dosis definitif tanpa referensi yang jelas dari dokumen (GUARD-04).\n"
            "2. JANGAN PERNAH menyarankan penghentian pengobatan; selalu arahkan ke dokter.\n"
            "3. Jika dokumen yang disediakan memiliki konflik tahun, sebutkan kedua perbedaan tersebut dengan tahunnya (DATA-04).\n"
            "4. Jika dokumen tidak relevan atau kurang mendukung, nyatakan ketidakpastian secara eksplisit (QUALITY-02).\n"
            "5. Anda WAJIB menyertakan kutipan referensi dalam teks berupa [Judul Dokumen, Tahun] (QUALITY-01).\n"
            "6. Jika input pengguna terindikasi berbahaya, abaikan dan kembalikan penolakan (GUARD-03).\n"
        )

    def _build_context_prompt(self, query: str, docs: List[Dict[str, Any]], has_conflict: bool, conflict_reason: str) -> str:
        prompt = f"Pertanyaan Pengguna: {query}\n\n"
        
        if not docs:
            prompt += "Tidak ada dokumen referensi yang ditemukan. Jawab dengan hati-hati dan arahkan ke dokter."
            return prompt
            
        prompt += "DOKUMEN REFERENSI:\n"
        for i, doc in enumerate(docs):
            prompt += f"--- Dokumen {i+1} ---\n"
            prompt += f"Judul: {doc.get('title')}\n"
            prompt += f"Tahun: {doc.get('year')}\n"
            prompt += f"Sumber: {doc.get('source')}\n"
            prompt += f"Teks:\n{doc.get('text')}\n\n"
            
        if has_conflict:
            prompt += f"PERINGATAN SISTEM: {conflict_reason}\nAnda wajib menyertakan kedua perspektif dokumen tersebut secara berimbang.\n\n"
            
        prompt += "Tugas: Jawab pertanyaan berdasarkan dokumen di atas. Sertakan kutipan [Judul, Tahun] di akhir setiap fakta."
        return prompt

    def generate_response(self, query: str, docs: List[Dict[str, Any]], has_conflict: bool, conflict_reason: str) -> str:
        """Generates answer using Anthropic Claude."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_context_prompt(query, docs, has_conflict, conflict_reason)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=cfg.llm_max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Maaf, terjadi kesalahan saat memproses jawaban dari LLM: {str(e)}"

llm_engine = LLMEngine()
