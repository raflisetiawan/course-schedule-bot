import logging
import discord
from discord import app_commands
from discord.ext import commands

import config
from services.gemini_service import (
    extract_intent,
    generate_response,
    build_context,
)
from utils.data_loader import (
    get_jadwal,
    get_available_kelas,
    is_kelas_valid,
    normalize_kelas,
    get_semester_label,
)
from utils.embed_builder import (
    build_jadwal_embed,
    build_empty_embed,
    build_error_embed,
    build_info_embed,
    build_help_embed,
)

logger = logging.getLogger("jadwal_bot.cog")


class JadwalCog(commands.Cog):
    """Cog utama untuk semua perintah jadwal kuliah."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # Slash command: /bot-course-schedule
    # ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="bot-course-schedule",
        description="Tanya jadwal kuliah Informatika UISI pakai bahasa sehari-hari! 📅",
    )
    @app_commands.describe(
        pesan="Tulis pertanyaanmu, contoh: 'IF 2A hari ini ada kelas apa?'"
    )
    @app_commands.checks.cooldown(rate=config.RATE_LIMIT_RATE, per=config.RATE_LIMIT_PER)
    async def schedule_command(
        self, interaction: discord.Interaction, pesan: str
    ):
        # Defer dulu — Gemini API butuh waktu > 3 detik
        await interaction.response.defer(thinking=True)

        user_tag = f"{interaction.user} ({interaction.user.id})"
        logger.info(f"Query dari {user_tag}: {pesan!r}")

        try:
            await self._handle_query(interaction, pesan)
        except Exception as e:
            logger.exception(f"Unhandled error pada query '{pesan}': {e}")
            embed = build_error_embed(
                "Aduh, terjadi error yang nggak terduga nih 😅 "
                "Coba lagi dalam beberapa saat ya!"
            )
            await interaction.followup.send(embed=embed)

    # ──────────────────────────────────────────────────────────
    # Slash command: /help-schedule
    # ──────────────────────────────────────────────────────────

    @app_commands.command(
        name="help-schedule",
        description="Panduan cara menggunakan Asisten Jadwal Informatika 📚",
    )
    async def help_schedule(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=build_help_embed())

    # ──────────────────────────────────────────────────────────
    # Error handler: cooldown
    # ──────────────────────────────────────────────────────────

    @schedule_command.error
    async def on_cooldown_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ Sabar ya, kamu lagi cooldown! "
                f"Coba lagi dalam **{error.retry_after:.1f} detik**.",
                ephemeral=True,
            )
        else:
            logger.error(f"Command error: {error}")
            error_msg = "Terjadi kesalahan. Coba lagi nanti! 🙏"
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(error_msg, ephemeral=True)
                else:
                    await interaction.response.send_message(error_msg, ephemeral=True)
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    # ──────────────────────────────────────────────────────────
    # Internal handler logic
    # ──────────────────────────────────────────────────────────

    async def _handle_query(self, interaction: discord.Interaction, pesan: str):
        """Core logic: parse → query → generate → send."""

        # Tentukan semester aktif
        semester = config.ACTIVE_SEMESTER

        # ── Step 1: Extract intent via Gemini ──
        parsed = await extract_intent(pesan, semester)
        logger.info(f"Parsed intent: {parsed}")

        intent = parsed.get("intent", "UNKNOWN")
        raw_kelas = parsed.get("kelas")
        hari = parsed.get("hari")
        parsed_semester = parsed.get("semester")

        # Gunakan semester dari user jika disebutkan
        if parsed_semester:
            semester = parsed_semester

        # ── Step 2: Routing berdasarkan intent ──

        # GREETING
        if intent == "GREETING":
            ctx = build_context(pesan, parsed, semester)
            ai_response = await generate_response(ctx)
            embed = build_info_embed(ai_response, title="👋 Halo!")
            await interaction.followup.send(embed=embed)
            return

        # HELP
        if intent == "HELP":
            await interaction.followup.send(embed=build_help_embed())
            return

        # UNKNOWN atau bukan JADWAL_QUERY
        if intent != "JADWAL_QUERY":
            ctx = build_context(pesan, parsed, semester)
            ai_response = await generate_response(ctx)
            embed = build_info_embed(ai_response)
            await interaction.followup.send(embed=embed)
            return

        # ── Step 3: JADWAL_QUERY — validasi kelas ──

        if not raw_kelas:
            # Kelas tidak disebutkan
            ctx = build_context(pesan, parsed, semester)
            ai_response = await generate_response(ctx)
            embed = build_error_embed(ai_response)
            await interaction.followup.send(embed=embed)
            return

        kelas = normalize_kelas(raw_kelas)

        if not is_kelas_valid(semester, kelas):
            # Kelas tidak ada di database
            available = get_available_kelas(semester)
            ctx = build_context(
                pesan, {**parsed, "kelas": kelas}, semester,
                jadwal_list=None, available_classes=available
            )
            ai_response = await generate_response(ctx)
            embed = build_error_embed(ai_response)
            await interaction.followup.send(embed=embed)
            return

        # ── Step 4: Hari default ke hari ini jika tidak disebutkan ──
        if not hari:
            from datetime import datetime
            _HARI_MAP = {0: "Senin", 1: "Selasa", 2: "Rabu",
                         3: "Kamis", 4: "Jumat", 5: "Sabtu", 6: "Minggu"}
            hari = _HARI_MAP[datetime.now().weekday()]
            logger.info(f"Hari tidak disebutkan, default ke: {hari}")

        # ── Step 5: Ambil jadwal dari JSON ──
        jadwal_list = get_jadwal(semester, kelas, hari)
        semester_label = get_semester_label(semester)

        # ── Step 6: Build context & generate response ──
        ctx = build_context(
            pesan, {**parsed, "kelas": kelas, "hari": hari},
            semester, jadwal_list=jadwal_list
        )
        ai_response = await generate_response(ctx)

        # ── Step 7: Build & send embed ──
        if jadwal_list:
            embed = build_jadwal_embed(
                kelas=kelas,
                hari=hari,
                semester_label=semester_label,
                jadwal_list=jadwal_list,
                ai_response=ai_response,
            )
        else:
            embed = build_empty_embed(kelas=kelas, hari=hari, ai_response=ai_response)

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(JadwalCog(bot))
