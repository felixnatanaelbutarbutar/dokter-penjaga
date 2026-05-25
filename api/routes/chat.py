from fastapi import APIRouter, HTTPException, Depends
from api.schemas import AskRequest, AskResponse, HealthResponse, SourceCitation
from core.pii import redact_text
from core.audit_logger import audit_logger
from core.guardrails import input_guardrail
from core.triage import triage_classifier
from core.retrieval import retrieval_engine
from core.temporal import detect_temporal_conflict
from core.llm import llm_engine
import time

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint untuk memastikan API dan dependencies berjalan dengan baik."""
    # TODO: Cek koneksi Qdrant dan model embedding di fase berikutnya
    return HealthResponse(status="ok")

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Endpoint utama untuk menerima pertanyaan medis.
    Alur:
    1. PII Redaction
    2. Audit Log (Incoming Request)
    3. Input Guardrail
    4. Triage Classifier
    5. Hybrid Retrieval & Temporal Boost
    6. LLM Generation
    """
    start_time = time.time()
    
    # 1. PII Redaction (WAJIB pertama kali sebelum apapun - PII-01)
    redacted_query = redact_text(request.query)
    
    # 2. Audit Logging
    audit_logger.log_request(
        session_id=request.session_id,
        redacted_query=redacted_query
    )
    
    # 3. Guardrail Check (Input)
    is_blocked, block_reason = input_guardrail.check_input(redacted_query)
    if is_blocked:
        audit_logger.log_guardrail_block(
            session_id=request.session_id,
            redacted_query=redacted_query,
            reason=block_reason
        )
        return AskResponse(
            answer="Permintaan ini tidak dapat diproses.",
            redacted_query=redacted_query,
            sources=[],
            is_emergency=False
        )

    # 4. Triage Classifier
    is_emergency, confidence, triage_reason = triage_classifier.classify(redacted_query)
    audit_logger.log_triage(
        session_id=request.session_id,
        is_emergency=is_emergency,
        reason=triage_reason,
        confidence=confidence
    )
    
    if is_emergency:
        # Langsung stop, jangan panggil LLM
        return AskResponse(
            answer="⚠️ INI KONDISI DARURAT. Segera hubungi 119 atau bawa ke IGD terdekat sekarang.",
            redacted_query=redacted_query,
            sources=[],
            is_emergency=True
        )
    
    # 5. Hybrid Retrieval
    top_docs = retrieval_engine.hybrid_search(redacted_query, top_k=5)
    
    # Log Retrieval
    audit_logger.log_retrieval(
        session_id=request.session_id,
        retrieved_docs_count=len(top_docs),
        sources=[doc.get("title") for doc in top_docs]
    )
    
    # Temporal Conflict Detection
    has_conflict, conflict_reason = detect_temporal_conflict(top_docs)
    
    # Check Confidence
    if top_docs and top_docs[0].get("hybrid_score", 0.0) < 0.5:
        # Jika skor rendah, tambahkan pesan ketidakpastian
        uncertainty_flag = True
    else:
        uncertainty_flag = False

    # 6. LLM Generation
    answer = llm_engine.generate_response(redacted_query, top_docs, has_conflict, conflict_reason)
    
    # 7. Output Guardrail (Task 3.3)
    from core.guardrails import output_guardrail
    is_bad_output, out_reason = output_guardrail.check_output(answer)
    if is_bad_output:
        audit_logger.log_guardrail_block(
            session_id=request.session_id,
            redacted_query=redacted_query,
            reason=f"Output Blocked: {out_reason}"
        )
        answer = "Maaf, respons yang dihasilkan sistem tidak memenuhi standar keamanan dan tidak dapat ditampilkan."
    elif uncertainty_flag:
        answer = "⚠️ Peringatan: Sistem tidak memiliki informasi medis yang cukup meyakinkan untuk menjawab ini. Silakan konsultasikan ke dokter Anda.\n\n" + answer

    # Format Sources for Response Schema
    source_citations = [
        SourceCitation(
            title=doc.get("title", ""),
            year=doc.get("year", 0),
            url=doc.get("url", "")
        )
        for doc in top_docs
    ]
    
    # Audit log response
    processing_time_ms = int((time.time() - start_time) * 1000)
    audit_logger.log_response(
        session_id=request.session_id,
        response_length=len(answer),
        processing_time_ms=processing_time_ms
    )
    
    return AskResponse(
        answer=answer,
        redacted_query=redacted_query,
        sources=source_citations,
        is_emergency=False
    )
