import json
import os
import re
from functools import lru_cache

from utils.dosen_map import get_panggilan

# ─────────────────────────────────────────────
# Path ke database
# ─────────────────────────────────────────────
_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database_jadwal.json")


@lru_cache(maxsize=1)
def load_database() -> dict:
    """Load database_jadwal.json sekali, di-cache selamanya."""
    with open(_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────────
# Helpers waktu
# ─────────────────────────────────────────────

def get_slot_waktu(slot_number: int) -> str:
    """Ambil string waktu dari nomor slot, e.g. 1 → '07:30 - 08:20'."""
    db = load_database()
    return db["keterangan"]["slot_waktu"].get(str(slot_number), "?")


def get_time_range(slot_mulai: int, slot_selesai: int) -> str:
    """
    Gabungkan waktu mulai slot pertama dengan waktu selesai slot terakhir.
    e.g. slot_mulai=1, slot_selesai=3 → '07:30 - 10:00'
    """
    db = load_database()
    slots = db["keterangan"]["slot_waktu"]

    start_raw = slots.get(str(slot_mulai), "")
    end_raw = slots.get(str(slot_selesai), "")

    # Format setiap slot: "HH:MM - HH:MM" → ambil HH:MM pertama / terakhir
    start_time = start_raw.split(" - ")[0] if start_raw else "?"
    end_time = end_raw.split(" - ")[1] if end_raw else "?"

    return f"{start_time} - {end_time}"


# ─────────────────────────────────────────────
# Helpers kelas
# ─────────────────────────────────────────────

def normalize_kelas(input_text: str) -> str:
    """
    Normalisasi input kelas ke format IF-XY.
    Contoh: 'IF 2A', 'IF2A', 'if-2a' → 'IF-2A'
    """
    text = input_text.upper().strip()
    # Match pola IF diikuti angka dan huruf, dengan atau tanpa separator
    match = re.search(r"IF[\s\-]?(\d+[A-Z])", text)
    if match:
        return f"IF-{match.group(1)}"
    return text


def get_available_kelas(semester: str) -> list[str]:
    """Daftar semua kelas yang tersedia di semester tertentu."""
    db = load_database()
    try:
        return list(db["jadwal"][semester]["kelas"].keys())
    except KeyError:
        return []


def get_semester_label(semester: str) -> str:
    """Ambil label lengkap semester, e.g. 'Semester Genap TA 2025/2026'."""
    db = load_database()
    try:
        return db["jadwal"][semester]["label"]
    except KeyError:
        return semester


def get_semester_generated(semester: str) -> str:
    """Ambil tanggal generate jadwal."""
    db = load_database()
    try:
        return db["jadwal"][semester].get("generated", "-")
    except KeyError:
        return "-"


# ─────────────────────────────────────────────
# Query jadwal
# ─────────────────────────────────────────────

def get_jadwal(semester: str, kelas: str, hari: str) -> list[dict]:
    """
    Ambil daftar mata kuliah untuk semester, kelas, dan hari tertentu.
    Return list of dict yang sudah di-enrich dengan field 'waktu'.
    Return [] jika tidak ada jadwal.
    """
    db = load_database()

    try:
        mata_kuliah_all = db["jadwal"][semester]["kelas"][kelas]["mata_kuliah"]
    except KeyError:
        return []

    result = []
    for mk in mata_kuliah_all:
        if mk.get("hari", "").lower() == hari.lower():
            # Enrich dengan time range string dan nama panggilan dosen
            enriched = dict(mk)
            enriched["waktu"] = get_time_range(mk["slot_mulai"], mk["slot_selesai"])
            enriched["dosen_kode"] = mk.get("dosen", "-")
            enriched["dosen"] = get_panggilan(mk.get("dosen", "-"))
            result.append(enriched)

    # Sort berdasarkan slot_mulai
    result.sort(key=lambda x: x.get("slot_mulai", 0))
    return result


def is_kelas_valid(semester: str, kelas: str) -> bool:
    """Cek apakah kelas ada di database."""
    return kelas in get_available_kelas(semester)
