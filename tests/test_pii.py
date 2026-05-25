import pytest
from core.pii import redact_text

class TestPIIRedaction:
    def test_redact_nik(self):
        # 16-digit number
        text = "Halo, NIK saya adalah 3275011234567890 dan saya butuh bantuan."
        redacted = redact_text(text)
        assert "3275011234567890" not in redacted
        assert "<ID_NUMBER>" in redacted or "<REDACTED>" in redacted or redacted != text

    def test_redact_indonesian_phone(self):
        phones = ["081234567890", "+6281234567890", "6281234567890"]
        for p in phones:
            text = f"Tolong hubungi saya di {p} secepatnya."
            redacted = redact_text(text)
            assert p not in redacted
            assert "<PHONE_NUMBER>" in redacted or redacted != text

    def test_redact_person_name(self):
        text = "Nama saya Budi Santoso, saya sakit kepala."
        redacted = redact_text(text)
        assert "Budi" not in redacted
        assert "Santoso" not in redacted

    def test_redact_location(self):
        text = "Saya tinggal di Jakarta Selatan."
        redacted = redact_text(text)
        assert "Jakarta" not in redacted

    def test_no_pii_remains_unchanged(self):
        text = "Saya merasa mual dan pusing sejak kemarin malam."
        redacted = redact_text(text)
        assert redacted == text

    def test_empty_string(self):
        assert redact_text("") == ""
