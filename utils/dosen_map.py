"""
Mapping kode dosen ke nama lengkap dan panggilan.
Kode yang belum diketahui namanya tetap ditampilkan sebagai kode.
"""

# Format setiap entry:
# "KODE": {"nama": "Nama Lengkap", "panggilan": "pak/bu X"}
DOSEN_MAP: dict[str, dict] = {
    # ── Yang diketahui ──────────────────────────────────────────────
    "MNI": {
        "nama": "Moch. Nurul Indra Al Fauzan, S.Kom., M.Eng",
        "panggilan": "Pak Fauzan",
    },
    "NGT": {
        "nama": "Ngatini, S.Si., M.Si., MCE, MOS",
        "panggilan": "Bu Tini",
    },
    "PAY": {
        "nama": "Puji Andayani, S.Si., M.Si., M.Sc., MCE",
        "panggilan": "Bu Puji",
    },
    "TQB": {
        "nama": "Taufiqotul Bariyah, S.Kom., M.IM., MC",
        "panggilan": "Bu Fiqo",
    },
    "LHY": {
        "nama": "Lailatul Hidayah, S.Kom., M.S., MCE",
        "panggilan": "Bu Laili",
    },
    "MZF": {
        "nama": "Muhammad Zain Fawwaz Nuruddin Siswantoro, S.Kom., M.Kom., MCE",
        "panggilan": "Pak Zain",
    },
    "YIR": {
        "nama": "Yohanes Indra Riskajaya, S.Kom., M.Kom., MTA, MCE",
        "panggilan": "Pak Yo",
    },

    # ── Yang belum diketahui — tampilkan kode saja ──────────────────
    "ADF": {"nama": "ADF", "panggilan": "ADF"},
    "ARI": {"nama": "ARI", "panggilan": "ARI"},
    "MAF": {"nama": "MAF", "panggilan": "MAF"},
    "MNF": {"nama": "MNF", "panggilan": "MNF"},
    "MNR": {"nama": "MNR", "panggilan": "MNR"},
    "WKS": {"nama": "WKS", "panggilan": "WKS"},
}


def get_panggilan(kode: str) -> str:
    """
    Konversi kode dosen ke nama panggilan.
    Support multiple dosen dipisah ' / ', e.g. 'NGT / PAY' → 'Bu Tini / Bu Puji'.
    Kode yang tidak dikenal dikembalikan apa adanya.
    """
    parts = [k.strip() for k in kode.split("/")]
    result = []
    for part in parts:
        info = DOSEN_MAP.get(part)
        result.append(info["panggilan"] if info else part)
    return " / ".join(result)


def get_nama_lengkap(kode: str) -> str:
    """
    Konversi kode dosen ke nama lengkap.
    Support multiple dosen dipisah ' / '.
    """
    parts = [k.strip() for k in kode.split("/")]
    result = []
    for part in parts:
        info = DOSEN_MAP.get(part)
        result.append(info["nama"] if info else part)
    return " / ".join(result)
