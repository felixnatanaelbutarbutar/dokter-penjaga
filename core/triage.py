import yaml
import os
import re
from typing import Dict, Any, Tuple

# Resolve path to config file relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRIAGE_YAML_PATH = os.path.join(PROJECT_ROOT, "config", "triage_keywords.yaml")

class TriageClassifier:
    """
    Rule-based deterministic classifier to detect emergency situations.
    Complies with TRIAGE-01, TRIAGE-02, and TRIAGE-03.
    """
    def __init__(self, config_path: str = TRIAGE_YAML_PATH):
        self.config_path = config_path
        self.keywords: Dict[str, list] = {}
        self._load_keywords()

    def _load_keywords(self):
        """Loads triage keywords from YAML file."""
        if not os.path.exists(self.config_path):
            # Fallback default if file is missing
            self.keywords = {
                "cardiology": ["serangan jantung", "henti jantung", "pingsan mendadak"],
                "respiratory": ["henti napas", "sesak napas akut"]
            }
            return
            
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                self.keywords = data

    def classify(self, text: str) -> Tuple[bool, float, str]:
        """
        Classifies whether the text indicates an emergency.
        Returns:
            is_emergency (bool): True if emergency detected.
            confidence (float): 1.0 if deterministic match found, else 0.0.
            reason (str): The category/reason for emergency classification.
        """
        if not text:
            return False, 0.0, ""
            
        text_lower = text.lower()
        
        # Check against all categories and keywords
        for category, keyword_list in self.keywords.items():
            if not keyword_list:
                continue
                
            for keyword in keyword_list:
                # We use word boundary regex to avoid partial matches
                # But since keywords can have spaces, simple " in " check is fast,
                # though regex boundary is safer.
                pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    reason = f"Terdeteksi kondisi darurat pada kategori: {category.upper()} (Keyword: '{keyword}')"
                    return True, 1.0, reason
                    
        return False, 0.0, ""

triage_classifier = TriageClassifier()
