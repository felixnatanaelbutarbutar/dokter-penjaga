import re
from typing import List, Dict
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

class PIIRedactor:
    """
    Handles detection and redaction of PII (Personally Identifiable Information).
    Complies with PII-01 and PII-02 rules.
    Uses Microsoft Presidio with multilingual spaCy model and custom Indonesian recognizers.
    """
    def __init__(self):
        # Configure NLP engine to use the multilingual model downloaded (xx_ent_wiki_sm)
        # We map "id" (Indonesian) to this model.
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "id", "model_name": "xx_ent_wiki_sm"}],
        }
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        # Initialize Presidio Analyzer with our NLP engine
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine, 
            supported_languages=["id"]
        )
        self.anonymizer = AnonymizerEngine()
        
        # Add custom recognizers for Indonesian context
        self._add_custom_recognizers()

    def _add_custom_recognizers(self):
        # 1. Custom NIK Recognizer (16 digits)
        nik_pattern = Pattern(name="nik_pattern", regex=r"\b\d{16}\b", score=0.85)
        nik_recognizer = PatternRecognizer(
            supported_entity="ID_NUMBER",
            supported_language="id",
            patterns=[nik_pattern],
            context=["nik", "ktp", "identitas"]
        )
        self.analyzer.registry.add_recognizer(nik_recognizer)

        # 2. Custom Phone Number Recognizer (Indonesian format)
        # Matches: +628..., 08..., 628...
        phone_pattern = Pattern(
            name="id_phone_pattern", 
            regex=r"\b(?:\+62|62|0)8[1-9][0-9]{6,11}\b", 
            score=0.85
        )
        phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            supported_language="id",
            patterns=[phone_pattern],
            context=["hp", "telepon", "telp", "whatsapp", "wa"]
        )
        self.analyzer.registry.add_recognizer(phone_recognizer)

    def redact_pii(self, text: str) -> str:
        """
        Redacts PII from text.
        Entities targeted: PERSON, LOCATION, EMAIL_ADDRESS, ID_NUMBER, PHONE_NUMBER.
        """
        if not text:
            return text

        # Analyze the text
        results = self.analyzer.analyze(
            text=text,
            entities=["PERSON", "LOCATION", "EMAIL_ADDRESS", "ID_NUMBER", "PHONE_NUMBER"],
            language="id",
            score_threshold=0.5
        )
        
        # Filter out common false positives in Indonesian
        false_positives = ["saya", "aku", "dia", "kamu", "mereka", "kita", "kami", "nik", "ktp"]
        filtered_results = [
            res for res in results 
            if text[res.start:res.end].lower() not in false_positives
        ]

        # Anonymize (Redact)
        anonymized_result = self.anonymizer.anonymize(
            text=text,
            analyzer_results=filtered_results
        )

        return anonymized_result.text

# Global singleton instance for easy import
pii_redactor = PIIRedactor()

def redact_text(text: str) -> str:
    """Convenience function to redact text using the global instance."""
    return pii_redactor.redact_pii(text)
