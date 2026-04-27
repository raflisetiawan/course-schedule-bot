import json
import logging
import re
from datetime import datetime, timedelta

from google import genai
from google.genai import types

import config
from utils.data_loader import get_available_kelas, get_semester_label
from utils.local_parser import parse_query as _local_parse_query

logger = logging.getLogger("jadwal_bot.gemini")

# ─────────────────────────────────────────────
# Init Gemini client (sekali, di module level)
# ─────────────────────────────────────────────
_client = genai.Client(api_key=config.GEMINI_API_KEY)


# ─────────────────────────────────────────────
# Fallback templates (dipakai jika Gemini error)
# ─────────────────────────────────────────────
_FALLBACK = {
    "FOUND": (
        "Jadwal **{kelas}** hari **{hari}**:\n"
        "{jadwal_text}\n\nSemangat kuliahnya! 💪"
    ),
    "EMPTY": (
        "Tidak ada jadwal kuliah untuk **{kelas}** di hari **{hari}**. "
        "Bisa santai dulu! 😄"
    ),
    "CLASS_NOT_FOUND": (
        "Hmm, kelas **{kelas}** tidak ditemukan di database. "
        "Cek lagi kode kelasnya ya! Kelas yang tersedia: {available}"
    ),
    "MISSING_CLASS": (
        "Eh, kelasnya belum disebutkan nih! "
        "Coba tulis seperti ini: `IF 2A hari Senin ada kelas apa?` 😊"
    ),
    "GREETING": (
        "Halo! 👋 Aku Asisten Jadwal Informatika UISI. "
        "Mau cek jadwal? Ketik saja seperti: `IF 2A hari ini ada kelas apa?`"
    ),
    "ERROR": "Maaf, terjadi kesalahan. Coba lagi dalam beberapa saat ya! 🙏",
}


def _format_fallback_jadwal(jadwal_list: list[dict]) -> str:
    lines = []
    for mk in jadwal_list:
        lines.append(
            f"• **{mk['nama']}** [{mk.get('tipe', '-')}] — "
            f"{mk.get('waktu', '-')} di {mk.get('ruang', '-')} (Dosen: {mk.get('dosen', '-')})"
        )
    return "\n".join(lines) if lines else "-"


# ─────────────────────────────────────────────
# Helper: hari ini & besok
# ─────────────────────────────────────────────
_HARI_MAP = {
    0: "Senin", 1: "Selasa", 2: "Rabu",
    3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu",
}


def _get_today() -> str:
    return _HARI_MAP.get(datetime.now().weekday(), "Senin")


def _get_tomorrow() -> str:
    return _HARI_MAP.get((datetime.now().weekday() + 1) % 7, "Selasa")



def _local_parse(user_message: str) -> dict:
    """Wrapper for local regex parser fallback."""
    result = _local_parse_query(user_message)
    logger.info(f"Local parser result: {result}")
    return result


# ─────────────────────────────────────────────
# Step 1: Extract intent dari pesan user
# ─────────────────────────────────────────────

async def extract_intent(user_message: str, semester: str) -> dict:
    """
    Kirim pesan user ke Gemini untuk mengekstrak:
    - intent: JADWAL_QUERY | GREETING | HELP | UNKNOWN
    - kelas: str | null
    - hari: str | null
    - semester: str | null

    Return dict. Fallback ke {'intent': 'UNKNOWN'} jika error.
    """
    today = _get_today()
    tomorrow = _get_tomorrow()
    available = ", ".join(get_available_kelas(semester))
    today_date = datetime.now().strftime("%d %B %Y")

    system_prompt = f"""Kamu adalah parser jadwal kuliah Informatika UISI.
Dari pesan mahasiswa, ekstrak informasi berikut dalam format JSON murni (tanpa markdown, tanpa penjelasan):

{{
  "intent": "JADWAL_QUERY" | "GREETING" | "HELP" | "UNKNOWN",
  "kelas": "<kode kelas format IF-XY, contoh IF-2A>" | null,
  "hari": "Senin" | "Selasa" | "Rabu" | "Kamis" | "Jumat" | "Sabtu" | "Minggu" | null,
  "semester": "GS" | "GN" | null
}}

Aturan:
- Jika user menyebut "hari ini" atau "today", isi hari dengan "{today}".
- Jika user menyebut "besok" atau "tomorrow", isi hari dengan "{tomorrow}".
- Kelas yang valid saat ini: {available}
- Format kelas: IF-XY (contoh: IF-2A, IF-4B). Normalisasi "IF 2A" atau "IF2A" menjadi "IF-2A".
- Semester: "GS"=gasal/ganjil, "GN"=genap. Jika tidak disebut, isi null.
- Hari ini: {today}, {today_date}.

Respond HANYA dengan JSON, tidak ada teks lain."""

    try:
        response = await _client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=user_message[:config.MAX_MESSAGE_LENGTH],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                max_output_tokens=200,
                temperature=0.1,  # Rendah agar output konsisten/deterministik
            ),
        )
        raw = response.text.strip()
        logger.debug(f"extract_intent raw: {raw}")
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"extract_intent JSON parse error: {e} | raw: {response.text}")
        logger.info("Falling back to local parser...")
        return _local_parse(user_message)
    except Exception as e:
        logger.error(f"extract_intent API error: {e}")
        logger.info("Falling back to local parser...")
        return _local_parse(user_message)


# ─────────────────────────────────────────────
# Step 2: Generate natural language response
# ─────────────────────────────────────────────

async def generate_response(context: dict) -> str:
    """
    Terima context dict, kirim ke Gemini, return respons bahasa manusia.
    Context keys: user_message, status, kelas, hari, semester_label, jadwal, available_classes
    """
    system_prompt = """Kamu adalah "Asisten Jadwal Informatika", bot Discord yang ramah dan ceria untuk mahasiswa Informatika UISI.

Tugasmu: ubah data jadwal yang diberikan menjadi respons bahasa manusia yang natural.

Aturan wajib:
- Gaya bahasa: santai, hangat, seperti teman — bukan robot.
- Variasikan setiap jawaban agar tidak monoton.
- Gunakan emoji secukupnya (jangan berlebihan).
- Sebutkan semua mata kuliah, waktu, ruang, dan dosen yang ada di data.
- Jangan mengarang data yang tidak ada di context.
- Respons dalam Bahasa Indonesia.
- JANGAN gunakan heading markdown (## atau #).
- Respons singkat dan padat, maksimal 4-5 kalimat."""

    context_message = json.dumps(context, ensure_ascii=False, indent=2)
    status = context.get("status", "ERROR")

    try:
        response = await _client.aio.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=context_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=400,
                temperature=0.8,  # Tinggi agar respons bervariasi
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"generate_response API error: {e}")
        return _get_fallback_response(context)


def _get_fallback_response(context: dict) -> str:
    """Fallback response saat Gemini tidak tersedia."""
    status = context.get("status", "ERROR")
    kelas = context.get("kelas", "")
    hari = context.get("hari", "")

    if status == "FOUND":
        jadwal_text = _format_fallback_jadwal(context.get("jadwal", []))
        return _FALLBACK["FOUND"].format(kelas=kelas, hari=hari, jadwal_text=jadwal_text)
    elif status == "EMPTY":
        return _FALLBACK["EMPTY"].format(kelas=kelas, hari=hari)
    elif status == "CLASS_NOT_FOUND":
        available = ", ".join(context.get("available_classes", []))
        return _FALLBACK["CLASS_NOT_FOUND"].format(kelas=kelas, available=available)
    elif status == "MISSING_CLASS":
        return _FALLBACK["MISSING_CLASS"]
    elif status == "GREETING":
        return _FALLBACK["GREETING"]
    else:
        return _FALLBACK["ERROR"]


# ─────────────────────────────────────────────
# Public helper: build context dict
# ─────────────────────────────────────────────

def build_context(
    user_message: str,
    parsed: dict,
    semester: str,
    jadwal_list: list[dict] | None = None,
    available_classes: list[str] | None = None,
) -> dict:
    """
    Build context dict yang akan dikirim ke generate_response().
    """
    kelas = parsed.get("kelas")
    hari = parsed.get("hari")
    intent = parsed.get("intent", "UNKNOWN")

    # Tentukan status
    if intent == "GREETING":
        status = "GREETING"
    elif intent == "HELP":
        status = "HELP"
    elif intent != "JADWAL_QUERY":
        status = "UNKNOWN"
    elif not kelas:
        status = "MISSING_CLASS"
    elif jadwal_list is None:
        status = "CLASS_NOT_FOUND"
    elif len(jadwal_list) == 0:
        status = "EMPTY"
    else:
        status = "FOUND"

    ctx = {
        "user_message": user_message,
        "status": status,
        "kelas": kelas,
        "hari": hari,
        "semester_label": get_semester_label(semester),
    }

    if jadwal_list is not None:
        ctx["jadwal"] = jadwal_list
    if available_classes is not None:
        ctx["available_classes"] = available_classes

    return ctx
