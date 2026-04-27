# 🎓 Asisten Jadwal Informatika

Bot Discord untuk mahasiswa Informatika **UISI** yang memungkinkan pengecekan jadwal kuliah menggunakan **bahasa sehari-hari**. Ditenagai oleh **Gemini AI** untuk memahami pertanyaan natural, dengan fallback regex parser agar tetap berfungsi meski API tidak tersedia.

---

## ✨ Fitur

- 💬 **Natural Language** — Tanya jadwal seperti ngobrol biasa, tidak perlu format khusus
- 🤖 **Gemini AI** — Parsing intent & generasi respons yang bervariasi dan tidak monoton
- 🔄 **Fallback Mode** — Tetap berfungsi menggunakan regex parser lokal saat Gemini tidak tersedia
- 📅 **Multi-Semester** — Support Semester Gasal (GS) dan Genap (GN)
- 👨‍🏫 **Nama Dosen** — Kode dosen otomatis dikonversi ke nama panggilan (Bu Tini, Pak Fauzan, dll.)
- 🎨 **Discord Embed** — Tampilan jadwal yang rapi dan berwarna

## 📸 Contoh Penggunaan

```
/jadwal pesan: IF 2A hari ini ada kelas apa?
/jadwal pesan: besok IF-4B kuliah nggak?
/jadwal pesan: jadwal IF-6A hari Kamis
/help-schedule
```

**Contoh respons (Fallback Mode):**
```
📅 IF-2A — Senin

Jadwal IF-2A hari Senin:
• Pemrograman 2 [Lab] — 07:30 - 10:00 di Lab CM 206 (Dosen: Pak Fauzan)
• Aljabar Linear [Teori] — 12:30 - 15:00 di CM 303 (Dosen: Bu Puji)

Semangat kuliahnya! 💪
```

---

## 🏗️ Struktur Proyek

```
course-schedule/
├── bot.py                    # Entry point utama
├── config.py                 # Konfigurasi (token, model, semester)
├── database_jadwal.json      # Database jadwal kuliah
├── requirements.txt
├── .env                      # Token & API key (jangan di-commit!)
├── .env.example              # Template env
├── .gitignore
│
├── cogs/
│   └── jadwal.py             # Slash command handler
│
├── services/
│   └── gemini_service.py     # Integrasi Gemini AI (2-step: parse + generate)
│
└── utils/
    ├── data_loader.py        # Load & query database_jadwal.json
    ├── embed_builder.py      # Discord Embed builder
    ├── local_parser.py       # Regex NLP fallback parser
    └── dosen_map.py          # Mapping kode dosen → nama panggilan
```

---

## ⚙️ Setup & Instalasi

### 1. Clone / Download Proyek

```bash
git clone <repo-url>
cd course-schedule
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

Copy file `.env.example` menjadi `.env`, lalu isi:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

- **Discord Bot Token** → [Discord Developer Portal](https://discord.com/developers/applications)
- **Gemini API Key** → [Google AI Studio](https://aistudio.google.com/)

### 4. Jalankan Bot

```bash
python bot.py
```

---

## 🤖 Alur Kerja AI

Bot menggunakan **2-step Gemini AI flow**:

```
User Message
    │
    ▼
[Step 1] extract_intent()  ──── Gemini mengekstrak: kelas, hari, semester (JSON)
    │                           Fallback: local regex parser
    ▼
[Data Layer] get_jadwal()  ──── Query database_jadwal.json
    │
    ▼
[Step 2] generate_response() ── Gemini generate respons natural bahasa Indonesia
    │                           Fallback: template hardcoded
    ▼
Discord Embed
```

### Mode Operasi

| Mode | Kondisi | Kualitas Respons |
|------|---------|-----------------|
| **AI Mode** | Gemini API tersedia | Respons natural, bervariasi, seperti teman |
| **Fallback Mode** | Gemini error/limit | Respons template, tetap informatif |

---

## 📚 Slash Commands

| Command | Deskripsi |
|---------|-----------|
| `/jadwal pesan:<teks>` | Tanya jadwal kuliah dengan bahasa bebas |
| `/help-schedule` | Panduan penggunaan bot |

---

## 🏫 Data Jadwal

### Kelas yang Tersedia

| Semester | Kelas |
|----------|-------|
| **Gasal (GS)** | IF-1A, IF-1B, IF-3A, IF-3B, IF-5A, IF-5B, IF-7A, IF-7B |
| **Genap (GN)** | IF-2A, IF-2B, IF-4A, IF-4B, IF-6A, IF-6B, IF-8A, IF-8B |

### Dosen

| Kode | Nama | Panggilan |
|------|------|-----------|
| MNI | Moch. Nurul Indra Al Fauzan | Pak Fauzan |
| NGT | Ngatini, S.Si., M.Si., MCE, MOS | Bu Tini |
| PAY | Puji Andayani, S.Si., M.Si., M.Sc., MCE | Bu Puji |
| TQB | Taufiqotul Bariyah, S.Kom., M.IM., MC | Bu Fiqo |
| LHY | Lailatul Hidayah, S.Kom., M.S., MCE | Bu Laili |
| MZF | Muhammad Zain Fawwaz Nuruddin | Pak Zain |
| YIR | Yohanes Indra Riskajaya, S.Kom., M.Kom. | Pak Yo |

> Kode yang belum diketahui (ADF, ARI, MAF, MNF, MNR, WKS) ditampilkan apa adanya.
> Update di `utils/dosen_map.py` untuk menambahkan nama baru.

---

## ⚙️ Konfigurasi Lanjutan

Edit `config.py` untuk mengubah:

```python
ACTIVE_SEMESTER = "GN"      # Semester aktif default: "GS" atau "GN"
GEMINI_MODEL = "gemini-2.5-flash-lite"  # Model Gemini yang digunakan
MAX_MESSAGE_LENGTH = 500    # Batas panjang pesan ke Gemini
RATE_LIMIT_RATE = 10        # Max request per user
RATE_LIMIT_PER = 60.0       # Per berapa detik
```

---

## 🗓️ Update Data Jadwal

Data jadwal tersimpan di `database_jadwal.json`. Struktur setiap mata kuliah:

```json
{
  "nama": "Pemrograman 2",
  "tipe": "Lab",
  "ruang": "Lab CM 206",
  "dosen": "MNI",
  "hari": "Senin",
  "slot_mulai": 1,
  "slot_selesai": 3
}
```

### Referensi Slot Waktu

| Slot | Waktu |
|------|-------|
| 1 | 07:30 - 08:20 |
| 2 | 08:20 - 09:10 |
| 3 | 09:10 - 10:00 |
| 4 | 10:00 - 10:50 |
| 5 | 10:50 - 11:40 |
| *(istirahat)* | 11:40 - 12:30 |
| 6 | 12:30 - 13:20 |
| 7 | 13:20 - 14:10 |
| 8 | 14:10 - 15:00 |
| *(istirahat)* | 15:00 - 15:30 |
| 9 | 15:30 - 16:20 |
| 10 | 16:20 - 17:10 |
| 11 | 17:10 - 18:00 |

---

## 🛠️ Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Language | Python 3.10+ |
| Discord Framework | discord.py 2.3+ |
| AI / NLP | Google Gemini API (`google-genai`) |
| AI Model | `gemini-2.5-flash-lite` |
| Data | JSON file-based |
| Config | python-dotenv |

---

## 📝 Lisensi

Proyek ini dibuat untuk keperluan internal mahasiswa Informatika UISI.
