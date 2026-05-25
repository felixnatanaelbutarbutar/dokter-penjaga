import yaml
import os
import re
from typing import Dict, Any, Tuple

# Resolve path to config file relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARDRAIL_YAML_PATH = os.path.join(PROJECT_ROOT, "config", "guardrail_patterns.yaml")

class InputGuardrail:
    """
    Checks incoming user requests for prompt injection or dangerous intents.
    Complies with GUARD-01 and GUARD-02.
    """
    def __init__(self, config_path: str = GUARDRAIL_YAML_PATH):
        self.config_path = config_path
        self.injection_patterns: list = []
        self.lethal_requests: list = []
        self._load_patterns()

    def _load_patterns(self):
        """Loads guardrail patterns from YAML file."""
        if not os.path.exists(self.config_path):
            self.injection_patterns = ["ignore previous instructions"]
            self.lethal_requests = ["dosis mematikan"]
            return
            
        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                self.injection_patterns = data.get("injection_patterns", [])
                self.lethal_requests = data.get("lethal_requests", [])

    def check_input(self, text: str) -> Tuple[bool, str]:
        """
        Checks if the input violates guardrails.
        Returns:
            is_blocked (bool): True if blocked.
            reason (str): Reason for blocking.
        """
        if not text:
            return False, ""
            
        text_lower = text.lower()
        
        # 1. Check Injection Patterns
        for pattern in self.injection_patterns:
            if pattern.lower() in text_lower:
                return True, f"Prompt Injection terdeteksi: Terdapat pola terlarang '{pattern}'"
                
        # 2. Check Lethal Requests
        for pattern in self.lethal_requests:
            if pattern.lower() in text_lower:
                return True, f"Lethal Request terdeteksi: Terdapat pola terlarang '{pattern}'"
                
        return False, ""

# Singleton instance
input_guardrail = InputGuardrail()

class OutputGuardrail:
    """
    Checks outgoing LLM responses for hallucinations or dangerous advice.
    Complies with GUARD-03.
    """
    def check_output(self, text: str) -> Tuple[bool, str]:
        if not text:
            return False, ""
            
        text_lower = text.lower()
        
        # Check for absolute dosage without disclaimer or dangerous advice
        # For simplicity in this demo, we just block very specific bad phrases
        bad_phrases = [
            "minum 500mg", 
            "dosis mematikan adalah", 
            "bunuh diri",
            "saya jamin obat ini aman 100%"
        ]
        
        for phrase in bad_phrases:
            if phrase in text_lower:
                return True, f"Output berbahaya terdeteksi: '{phrase}'"
                
        return False, ""

output_guardrail = OutputGuardrail()
