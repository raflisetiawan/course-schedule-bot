import discord
import random
from datetime import datetime


# ─────────────────────────────────────────────
# Warna embed
# ─────────────────────────────────────────────
COLOR_FOUND    = 0x2ECC71  # Hijau — ada jadwal
COLOR_EMPTY    = 0xF39C12  # Kuning — tidak ada jadwal
COLOR_ERROR    = 0xE74C3C  # Merah — error / kelas tidak valid
COLOR_INFO     = 0x4285F4  # Biru — greeting, help, info


# ─────────────────────────────────────────────
# Emoji untuk tipe mata kuliah
# ─────────────────────────────────────────────
TIPE_EMOJI = {
    "Lab":   "🔬",
    "Teori": "📖",
}


def _tipe_emoji(tipe: str) -> str:
    return TIPE_EMOJI.get(tipe, "📌")


def _footer_text(count: int) -> str:
    footers = [
        f"Total {count} mata kuliah",
        f"{count} matkul hari ini • Asisten Jadwal Informatika 🎓",
        f"Semangat ya! {count} matkul menanti",
    ]
    return random.choice(footers)


# ─────────────────────────────────────────────
# Embed builders
# ─────────────────────────────────────────────

def build_jadwal_embed(
    kelas: str,
    hari: str,
    semester_label: str,
    jadwal_list: list[dict],
    ai_response: str,
) -> discord.Embed:
    """
    Embed utama saat jadwal ditemukan.
    Menampilkan respons AI di description + detail setiap mata kuliah di fields.
    """
    embed = discord.Embed(
        title=f"📅  {kelas}  —  {hari}",
        description=ai_response,
        color=COLOR_FOUND,
        timestamp=datetime.now(),
    )
    embed.set_author(name="Asisten Jadwal Informatika", icon_url="https://i.imgur.com/WMLF9hU.png")
    embed.add_field(name="🗓️ Semester", value=semester_label, inline=False)

    for mk in jadwal_list:
        emoji = _tipe_emoji(mk.get("tipe", ""))
        nama  = mk.get("nama", "-")
        tipe  = mk.get("tipe", "-")
        waktu = mk.get("waktu", "-")
        ruang = mk.get("ruang", "-")
        dosen = mk.get("dosen", "-")
        gabungan = mk.get("gabungan", None)

        value_lines = [
            f"⏰ `{waktu}`   📍 `{ruang}`   👨‍🏫 `{dosen}`",
        ]
        if gabungan:
            value_lines.append(f"🔗 Kelas gabungan: *{gabungan}*")

        embed.add_field(
            name=f"{emoji} {nama}  [{tipe}]",
            value="\n".join(value_lines),
            inline=False,
        )

    embed.set_footer(text=_footer_text(len(jadwal_list)))
    return embed


def build_empty_embed(kelas: str, hari: str, ai_response: str) -> discord.Embed:
    """Embed saat tidak ada jadwal di hari tersebut."""
    embed = discord.Embed(
        title=f"🎉  {kelas}  —  {hari}",
        description=ai_response,
        color=COLOR_EMPTY,
        timestamp=datetime.now(),
    )
    embed.set_author(name="Asisten Jadwal Informatika", icon_url="https://i.imgur.com/WMLF9hU.png")
    embed.set_footer(text="Asisten Jadwal Informatika")
    return embed


def build_error_embed(ai_response: str) -> discord.Embed:
    """Embed untuk error: kelas tidak valid, input tidak lengkap, dll."""
    embed = discord.Embed(
        description=ai_response,
        color=COLOR_ERROR,
        timestamp=datetime.now(),
    )
    embed.set_author(name="Asisten Jadwal Informatika", icon_url="https://i.imgur.com/WMLF9hU.png")
    embed.set_footer(text="Asisten Jadwal Informatika")
    return embed


def build_info_embed(ai_response: str, title: str = "") -> discord.Embed:
    """Embed untuk greeting, help, atau info umum."""
    embed = discord.Embed(
        title=title or None,
        description=ai_response,
        color=COLOR_INFO,
        timestamp=datetime.now(),
    )
    embed.set_author(name="Asisten Jadwal Informatika", icon_url="https://i.imgur.com/WMLF9hU.png")
    embed.set_footer(text="Asisten Jadwal Informatika ")
    return embed


def build_help_embed() -> discord.Embed:
    """Embed panduan penggunaan — hardcoded, tidak butuh Gemini."""
    embed = discord.Embed(
        title="📚  Panduan Asisten Jadwal Informatika",
        description=(
            "Halo! Aku bisa menjawab pertanyaan jadwal kuliah Informatika UISI "
            "dengan bahasa yang natural. Cukup ketik pertanyaanmu!\n\u200b"
        ),
        color=COLOR_INFO,
        timestamp=datetime.now(),
    )
    embed.set_author(name="Asisten Jadwal Informatika", icon_url="https://i.imgur.com/WMLF9hU.png")

    embed.add_field(
        name="🗣️ Cara Pakai",
        value=(
            "Gunakan slash command `/bot-course-schedule` lalu tulis pertanyaanmu.\n"
            "Tidak perlu format khusus — pakai bahasa sehari-hari!"
        ),
        inline=False,
    )
    embed.add_field(
        name="💬 Contoh Pertanyaan",
        value=(
            "• `IF 2A hari ini ada kelas apa?`\n"
            "• `besok IF-4B kuliah nggak?`\n"
            "• `jadwal IF-6A hari Kamis`\n"
            "• `IF 8A rabu ada apa aja?`\n"
            "• `senin IF-3A kosong nggak?`"
        ),
        inline=False,
    )
    embed.add_field(
        name="🏫 Kelas Semester Genap (GN)",
        value="`IF-2A` `IF-2B` `IF-4A` `IF-4B` `IF-6A` `IF-6B` `IF-8A` `IF-8B`",
        inline=False,
    )
    embed.add_field(
        name="🏫 Kelas Semester Gasal (GS)",
        value="`IF-1A` `IF-1B` `IF-3A` `IF-3B` `IF-5A` `IF-5B` `IF-7A` `IF-7B`",
        inline=False,
    )
    embed.set_footer(text="Asisten Jadwal Informatika ")
    return embed
