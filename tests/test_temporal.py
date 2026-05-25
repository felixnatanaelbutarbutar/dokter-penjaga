import pytest
from core.temporal import temporal_boost, detect_temporal_conflict
from config import get_settings

cfg = get_settings()

def test_temporal_boost():
    # Min year should be 0.0
    assert temporal_boost(cfg.year_min) == 0.0
    
    # Max year should be 1.0
    assert temporal_boost(cfg.year_max) == 1.0
    
    # Below min year should be 0.0
    assert temporal_boost(cfg.year_min - 5) == 0.0
    
    # Above max year should be 1.0
    assert temporal_boost(cfg.year_max + 5) == 1.0
    
    # Middle year should be proportionally between 0 and 1
    mid_year = (cfg.year_min + cfg.year_max) // 2
    boost = temporal_boost(mid_year)
    assert 0.0 < boost < 1.0

def test_detect_temporal_conflict():
    docs_no_conflict = [
        {"title": "Doc A", "year": 2023},
        {"title": "Doc B", "year": 2024}
    ]
    
    has_conflict, reason = detect_temporal_conflict(docs_no_conflict)
    assert has_conflict is False
    assert reason == ""

    docs_with_conflict = [
        {"title": "Guideline Old", "year": 2019},
        {"title": "Guideline New", "year": 2024}
    ]
    
    has_conflict, reason = detect_temporal_conflict(docs_with_conflict)
    assert has_conflict is True
    assert "2019" in reason
    assert "2024" in reason
    assert "Guideline Old" in reason

def test_detect_temporal_conflict_not_enough_docs():
    docs = [{"title": "Only One", "year": 2024}]
    has_conflict, reason = detect_temporal_conflict(docs)
    assert has_conflict is False
