"""
Local regex-based NLP fallback parser.
Digunakan saat Gemini API tidak tersedia (403/429/timeout).
Mengekstrak kelas, hari, dan intent dari pesan bahasa Indonesia.
"""

import re
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# Hari mapping
# ─────────────────────────────────────────────
_HARI_MAP = {
    0: "Senin", 1: "Selasa", 2: "Rabu",
    3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu",
}

_HARI_KEYWORDS = {
    "senin": "Senin", "monday": "Senin", "mon": "Senin",
    "selasa": "Selasa", "tuesday": "Selasa", "tue": "Selasa",
    "rabu": "Rabu", "wednesday": "Rabu", "wed": "Rabu",
    "kamis": "Kamis", "thursday": "Kamis", "thu": "Kamis",
    "jumat": "Jumat", "jum'at": "Jumat", "friday": "Jumat", "fri": "Jumat",
    "sabtu": "Sabtu", "saturday": "Sabtu", "sat": "Sabtu",
    "minggu": "Minggu", "sunday": "Minggu", "sun": "Minggu",
}

_JADWAL_KEYWORDS = [
    "jadwal", "kelas", "kuliah", "matkul", "mata kuliah", "schedule",
    "ada apa", "ada kelas", "ada kuliah", "kosong", "libur",
    "jam berapa", "ruang", "dosen", "belajar",
]

_GREETING_KEYWORDS = [
    "halo", "hai", "hi", "hey", "hello", "pagi", "siang", "sore",
    "malam", "assalamualaikum", "selamat",
]

_HELP_KEYWORDS = [
    "help", "bantuan", "cara pakai", "gimana caranya", "cara",
    "panduan", "tutorial", "petunjuk", "tolong bantu",
]


def _get_today() -> str:
    return _HARI_MAP.get(datetime.now().weekday(), "Senin")


def _get_tomorrow() -> str:
    return _HARI_MAP.get((datetime.now().weekday() + 1) % 7, "Selasa")


def extract_kelas(text: str) -> str | None:
    """Ekstrak kode kelas dari teks. Return format IF-XY atau None."""
    # Match: IF-2A, IF 2A, IF2A, if-2a, dll
    match = re.search(r"(?i)IF[\s\-]?(\d+[A-B])", text)
    if match:
        return f"IF-{match.group(1).upper()}"
    return None


def extract_hari(text: str) -> str | None:
    """Ekstrak nama hari dari teks. Support 'hari ini', 'besok', dan nama hari."""
    lower = text.lower()

    # Dynamic: hari ini / today
    if re.search(r"hari\s*ini|today|sekarang", lower):
        return _get_today()

    # Dynamic: besok / tomorrow
    if re.search(r"besok|tomorrow|besuk", lower):
        return _get_tomorrow()

    # Static: nama hari langsung
    for keyword, hari in _HARI_KEYWORDS.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", lower):
            return hari

    return None


def detect_intent(text: str) -> str:
    """Deteksi intent dari teks user."""
    lower = text.lower().strip()

    # Check greeting first (short messages)
    if any(lower.startswith(k) or lower == k for k in _GREETING_KEYWORDS):
        return "GREETING"

    # Check help
    if any(k in lower for k in _HELP_KEYWORDS):
        return "HELP"

    # Check jadwal query — cukup ada keyword jadwal ATAU ada kode kelas
    has_jadwal_keyword = any(k in lower for k in _JADWAL_KEYWORDS)
    has_kelas = extract_kelas(text) is not None
    has_hari = extract_hari(text) is not None

    if has_jadwal_keyword or has_kelas or (has_hari and len(lower) > 5):
        return "JADWAL_QUERY"

    return "UNKNOWN"


def parse_query(text: str) -> dict:
    """
    Parse pesan user secara lokal tanpa AI.
    Return dict: {intent, kelas, hari, semester}
    """
    return {
        "intent": detect_intent(text),
        "kelas": extract_kelas(text),
        "hari": extract_hari(text),
        "semester": None,  # Bisa diperluas jika ada keyword gasal/genap
    }
