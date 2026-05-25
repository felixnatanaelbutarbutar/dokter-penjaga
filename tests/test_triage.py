import pytest
from core.triage import triage_classifier

def test_triage_detects_emergency():
    # Test valid emergency phrases
    emergencies = [
        "Bapak saya tiba-tiba serangan jantung, tolong!",
        "Dia jatuh tidak sadar sejak 5 menit yang lalu.",
        "Anak saya tersedak parah dan membiru."
    ]
    
    for text in emergencies:
        is_emergency, confidence, reason = triage_classifier.classify(text)
        assert is_emergency is True, f"Failed to detect emergency in: {text}"
        assert confidence == 1.0
        assert len(reason) > 0

def test_triage_ignores_normal_query():
    # Test non-emergency phrases
    normal_queries = [
        "Bagaimana cara mencegah penyakit diabetes?",
        "Berapa dosis paracetamol untuk anak 5 tahun?",
        "Saya pusing dan batuk berdahak."
    ]
    
    for text in normal_queries:
        is_emergency, confidence, reason = triage_classifier.classify(text)
        assert is_emergency is False, f"Falsely detected emergency in: {text}"
        assert confidence == 0.0
