from config import get_settings
from typing import List, Dict, Any, Tuple

cfg = get_settings()

def temporal_boost(year: int) -> float:
    """
    Menghitung skor temporal berdasarkan tahun terbit.
    Dokumen lebih baru mendapat skor lebih tinggi.
    Fungsi: f(year) = (year - YEAR_MIN) / (YEAR_MAX - YEAR_MIN)
    Mengembalikan nilai antara 0.0 hingga 1.0.
    """
    if year < cfg.year_min:
        return 0.0
    if year > cfg.year_max:
        return 1.0
        
    return (year - cfg.year_min) / (cfg.year_max - cfg.year_min)

def detect_temporal_conflict(docs: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Mendeteksi apakah terdapat konflik temporal (perbedaan tahun terbit)
    di antara dokumen-dokumen yang relevan (top K).
    Asumsi docs berbentuk dictionary yang memiliki kunci 'year' dan 'title'.
    """
    if not docs or len(docs) < 2:
        return False, ""
        
    years = [doc.get("year", 0) for doc in docs if doc.get("year", 0) > 0]
    
    if not years:
        return False, ""
        
    min_year = min(years)
    max_year = max(years)
    
    if (max_year - min_year) >= cfg.conflict_year_gap:
        # Temukan judul dokumen untuk pesan konflik
        doc_old = next((d for d in docs if d.get("year") == min_year), None)
        doc_new = next((d for d in docs if d.get("year") == max_year), None)
        
        reason = (
            f"Terdeteksi perbedaan panduan berdasarkan tahun: "
            f"Terdapat dokumen tahun {min_year} ('{doc_old.get('title') if doc_old else 'Unknown'}') "
            f"dan tahun {max_year} ('{doc_new.get('title') if doc_new else 'Unknown'}'). "
            f"Sistem akan menampilkan kedua perspektif."
        )
        return True, reason
        
    return False, ""
