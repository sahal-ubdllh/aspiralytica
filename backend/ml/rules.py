# backend/ml/rules.py
# ================================================================
# RULE-BASED ENGINE — Keyword Matching + Sarcasm Detection
# ================================================================
#
# CHANGELOG v4:
#   - Perluas SENT_NEGATIF_KW: tambah single-word triggers
#     ("rusak", "bocor", "mampet", "padam", "berlubang", dll)
#     → Fix: "jalan masih rusak" sekarang → negatif ✅
#   - Tambah pola "masih rusak", "belum diperbaiki", "sudah mati", dll
#   - Tambah "tidak memperhatikan", "tidak ada tindakan", "berlarut"
#   - Tambah pola temporal: "dari X tahun", "bertahun-tahun", "lama sekali"
#   - Perluas KELUHAN_KEYWORDS dengan pola yang sama
#   - Pertahankan negasi-aware untuk keyword POSITIF (tidak berubah)
# ================================================================

import re

# ================================================================
# NEGATION-AWARE KEYWORD MATCHING
# ================================================================

_NEGATION_WORDS = {
    "tidak", "tak", "bukan", "belum",
    "tanpa", "kurang",
}


def _keyword_in_text(text: str, keyword: str) -> bool:
    return keyword in text


def _positive_keyword_in_text(text: str, keyword: str) -> bool:
    """
    Cek keyword POSITIF dengan memastikan tidak didahului negasi.

    Contoh:
        "memuaskan" di "sangat memuaskan"  → True  ✅
        "memuaskan" di "tidak memuaskan"   → False ✅
        "membaik"   di "belum membaik"     → False ✅
        "membaik"   di "semakin membaik"   → True  ✅
    """
    idx = text.find(keyword)
    if idx == -1:
        return False
    before = text[:idx].strip().split()
    if before and before[-1] in _NEGATION_WORDS:
        return False
    return True


# ================================================================
# KEYWORD RULES — INTENT
# ================================================================

DARURAT_KEYWORDS = [
    "kebakaran", "banjir bandang", "tanah longsor", "gempa",
    "tsunami", "erupsi gunung", "angin puting beliung",
    "tenggelam", "keracunan massal", "korban jiwa", "luka parah",
    "tidak sadarkan diri", "nyawa terancam", "butuh penanganan cepat",
    "evakuasi", "ambruk", "kebocoran gas", "listrik konslet",
    "jembatan putus", "kebanjiran parah",
    "darurat", "gawat darurat", "ambulans", "tim penyelamat",
    "situasi kritis", "insiden serius", "kondisi darurat",
    "membutuhkan bantuan segera", "perlu pertolongan segera",
]

APRESIASI_KEYWORDS = [
    "terima kasih", "terimakasih", "makasih", "alhamdulillah",
    "bagus sekali", "sangat bagus", "luar biasa", "hebat sekali",
    "mantap sekali", "keren sekali", "terpuji", "acungan jempol",
    "patut diapresiasi", "patut dipuji", "patut diacungi",
    "sangat memuaskan", "puas sekali", "sangat puas",
    "senang sekali", "bangga", "salut",
    "semakin membaik", "terus membaik", "terus meningkat",
    "membaik dari waktu", "jauh lebih baik", "jauh meningkat",
    "pelayanan baik", "pelayanan bagus", "pelayanan memuaskan",
    "pelayanan ramah", "pelayanan sangat baik", "sangat baik",
    "sangat membantu", "membantu sekali",
    "dipermudah", "dimudahkan",
]

KELUHAN_KEYWORDS = [
    # Kondisi fisik buruk
    "rusak parah", "rusak berat", "masih rusak", "sudah rusak",
    "masih belum diperbaiki", "belum diperbaiki", "tidak diperbaiki",
    "tidak diangkut", "tidak mengalir", "tidak menyala", "tidak berfungsi",
    "tidak terawat", "tidak ada perbaikan", "tidak ada yang peduli",
    "tidak ada respons", "tidak ada tindakan", "tidak ada solusi",
    "tidak pernah diperbaiki", "tidak kunjung beres",
    "sudah lama rusak", "dibiarkan rusak", "dibiarkan begitu saja",
    "tidak memperhatikan", "tidak pernah memperhatikan",
    # Kondisi parah
    "sangat mengecewakan", "sangat buruk", "sangat lambat",
    "tidak karuan", "tidak masuk akal", "tidak profesional",
    "parah sekali", "buruk sekali", "jorok sekali", "kotor sekali",
    "sangat kotor", "sangat disayangkan", "memprihatinkan",
    "tidak kondusif", "tidak layak", "tidak layak huni",
    # Temporal — sudah lama
    "bertahun-tahun", "dari tahun lalu", "sudah berhari-hari",
    "sudah berminggu-minggu", "berbulan-bulan", "berkali-kali dilaporkan",
    "sudah lama", "lama sekali",
    # Emosi negatif
    "sudah capek", "sudah lelah", "lelah melaporkan", "capek melaporkan",
    "mengganggu", "terganggu",
    # Bau/sanitasi
    "menyengat", "bau busuk", "bau sampah",
    # Tren memburuk
    "semakin parah", "semakin buruk", "makin parah",
    # Negasi + kata positif
    "tidak bagus", "tidak baik", "tidak memuaskan", "tidak puas",
    "tidak beres", "tidak membantu", "tidak ramah", "tidak aman",
    "tidak nyaman", "tidak bersih", "tidak teratur", "tidak jelas",
]

SARAN_KEYWORDS = [
    "sebaiknya", "alangkah baiknya", "alangkah lebih baik",
    "disarankan", "kami sarankan", "saran kami", "saran agar",
    "usul agar", "usulan", "ada baiknya", "kiranya perlu",
    "hendaknya", "seharusnya ada", "seharusnya dibuat",
    "lebih baik jika", "lebih baik bila", "lebih baik kalau",
    "perlu dibenahi", "perlu ditingkatkan", "bisa ditingkatkan",
    "dapat ditingkatkan", "bisa diperbaiki", "dapat diperbaiki",
    "bisa dioptimalkan", "perlu dioptimalkan",
]

PERMINTAAN_KEYWORDS = [
    "mohon", "minta", "harap", "tolong",
    "kami membutuhkan", "kami memerlukan", "kami inginkan",
    "ingin ada", "berharap ada", "perlu ada",
    "diharapkan ada", "sangat diperlukan", "sangat dibutuhkan",
    "perlu ditambah", "perlu dipasang", "perlu dibangun",
    "perlu disediakan", "perlu diperbaiki",
    "segera pasang", "segera bangun", "segera tambah", "segera sediakan",
]


# ================================================================
# KEYWORD RULES — SENTIMEN
# ================================================================

# ── NEGATIF ──────────────────────────────────────────────────────
# Dibagi 3 kelompok agar mudah di-maintain:
#   A) Single-word triggers   — satu kata sudah cukup jadi sinyal negatif
#   B) Phrase triggers        — frasa 2+ kata lebih spesifik
#   C) Negasi + kata positif  — hasil normalisasi slang / negasi eksplisit

SENT_NEGATIF_KW = [

    # ── A) Single-word / short triggers ─────────────────────────
    # Kata-kata ini sendiri sudah kuat menandai sentimen negatif
    # dalam konteks laporan masyarakat
    "rusak",           # "jalan rusak", "fasilitas rusak"
    "bocor",           # "atap bocor", "pipa bocor"
    "mampet",          # "got mampet", "saluran mampet"
    "padam",           # "listrik padam", "lampu padam"
    "retak",           # "jembatan retak", "tembok retak"
    "berlubang",       # "jalan berlubang"
    "menumpuk",        # "sampah menumpuk"
    "terbengkalai",    # "proyek terbengkalai"
    "ambruk",          # "jembatan ambruk"
    "longsor",         # "tanah longsor"
    "banjir",          # "banjir lagi"
    "kumuh",           # "lingkungan kumuh"
    "jorok",           # "kondisi jorok"
    "kotor",           # "sangat kotor"
    "mati",            # "lampu mati", "pompa mati"

    # ── B) Phrase triggers ───────────────────────────────────────
    # Kondisi fisik buruk — eksplisit
    "rusak parah", "rusak berat", "masih rusak", "sudah rusak",
    "rusak total", "rusak sejak lama",
    "masih belum diperbaiki", "belum diperbaiki", "tidak diperbaiki",
    "tidak diangkut", "tidak mengalir", "tidak menyala",
    "tidak berfungsi", "tidak terawat",
    "bau busuk", "bau sampah", "menyengat",
    "jorok sekali", "kotor sekali", "kumuh sekali",
    "berlubang parah", "retak parah",
    "bocor parah", "bocor terus",
    "lampu mati", "sudah mati", "sudah padam",
    "pohon tumbang", "tembok roboh",
    "got mampet", "saluran mampet", "drainase mampet",

    # Tidak ada tindakan / diabaikan
    "tidak ada perbaikan", "tidak ada yang peduli",
    "tidak ada respons", "tidak ada tindakan", "tidak ada solusi",
    "tidak ada yang datang", "tidak ada yang memperbaiki",
    "tidak ada yang mengurus", "tidak ada yang menangani",
    "tidak ada yang membersihkan", "tidak ada yang membereskan",
    "tidak pernah diperbaiki", "tidak kunjung beres",
    "tidak memperhatikan", "tidak pernah memperhatikan",
    "tidak pernah diperhatikan", "tidak pernah ditangani",
    "pemerintah tidak memperhatikan", "diabaikan",
    "dibiarkan rusak", "dibiarkan begitu saja", "dibiarkan berlarut",
    "tidak pernah ada tindakan", "tidak ada upaya",

    # Temporal — sudah lama dibiarkan
    "bertahun-tahun", "dari tahun lalu", "sejak lama",
    "sudah lama", "sudah berhari-hari", "sudah berminggu-minggu",
    "berbulan-bulan", "berkali-kali dilaporkan", "lama sekali",
    "sudah bertahun", "puluhan tahun",

    # Kondisi parah / ekspresi frustrasi
    "sangat buruk", "sangat lambat", "sangat mengecewakan",
    "sangat berbahaya", "sangat disayangkan", "sangat parah",
    "buruk sekali", "parah sekali", "lambat sekali",
    "tidak karuan", "tidak masuk akal", "tidak profesional",
    "memprihatinkan", "mengkhawatirkan",
    "tidak kondusif", "tidak layak", "tidak layak huni",
    "semakin parah", "semakin buruk", "makin parah", "makin rusak",
    "sudah capek", "sudah lelah", "mengganggu", "terganggu",
    "tidak ada respons", "tidak kunjung beres",

    # Bencana / darurat
    "insiden serius", "situasi kritis", "kondisi kritis",
    "butuh penanganan cepat", "gawat darurat", "nyawa terancam",
    "luka parah", "tidak sadarkan diri",
    "kebakaran", "banjir bandang", "tanah longsor", "gempa",
    "korban jiwa", "keracunan massal", "tenggelam",

    # ── C) Negasi + kata positif ─────────────────────────────────
    "tidak bagus", "tidak baik", "tidak memuaskan", "tidak puas",
    "tidak beres", "tidak membantu", "tidak ramah", "tidak aman",
    "tidak nyaman", "tidak bersih", "tidak teratur", "tidak jelas",
    "tidak profesional", "tidak responsif",
    "belum ada perbaikan", "belum ada tindakan",
]

# ── POSITIF ──────────────────────────────────────────────────────
# WAJIB pakai _positive_keyword_in_text (negasi-aware)
SENT_POSITIF_KW = [
    "terima kasih", "terimakasih", "makasih",
    "bagus sekali", "sangat bagus", "luar biasa", "hebat sekali",
    "acungan jempol", "patut diapresiasi", "patut dipuji",
    "sangat memuaskan", "puas sekali", "sangat puas",
    "senang sekali", "bangga", "salut", "mantap",
    "sangat membantu", "membantu sekali",
    "dipermudah", "dimudahkan",
    "pelayanan baik", "pelayanan bagus", "pelayanan memuaskan",
    "pelayanan ramah", "pelayanan sangat baik", "sangat baik",
    "semakin membaik", "terus membaik", "terus meningkat",
    "jauh lebih baik", "jauh meningkat", "membaik dari waktu",
    # Rentan negasi — wajib negasi-aware:
    "memuaskan", "membaik", "bagus", "baik", "puas",
    "membantu", "ramah", "beres", "aman", "nyaman",
    "bersih", "teratur", "profesional", "responsif",
]


# ================================================================
# SARCASM DETECTION
# ================================================================

_SARC_POSITIF_KUAT = [
    "bangga sekali", "senang sekali", "luar biasa sekali", "bagus sekali",
    "hebat sekali", "keren sekali", "mantap sekali", "terima kasih sekali",
    "sungguh membanggakan", "sungguh luar biasa", "wah keren", "wah bagus",
    "wah hebat", "sangat bangga", "sangat kagum", "membanggakan sekali",
    "mengagumkan sekali", "bangga betul", "senang betul", "hebat betul",
    "bagus betul", "mantap betul", "keren betul", "luar biasa betul",
]

_SARC_KONTRADIKSI = [
    "langsung rusak", "langsung mati", "langsung mampet", "langsung berlubang",
    "langsung hancur", "langsung ambruk", "langsung bocor",
    "tidak pernah datang", "tidak pernah hadir", "tidak pernah ada",
    "tidak pernah sampai", "tidak pernah diperbaiki",
    "tidak pernah disentuh", "tidak pernah ditangani",
    "tidak pernah diperhatikan", "tidak pernah diselesaikan",
    "sudah membiarkan", "telah membiarkan",
    "membiarkan sampah", "membiarkan jalan", "membiarkan warga",
    "mudah rapuh", "cepat rusak", "asal jadi", "asal bangun",
    "kerja santai", "kerja lambat", "kerja asal",
    "dibiarkan antre", "dibiarkan begitu saja",
    "tanpa kualitas", "tanpa hasil", "tanpa solusi",
    "tidak ada yang peduli", "tidak ada yang merespons",
    "puluhan tahun tidak",
]

_SARC_KATA_POS = [
    "bangga", "senang", "terima kasih", "luar biasa", "bagus",
    "hebat", "keren", "mantap", "alhamdulillah", "mengagumkan",
]

_SARC_KATA_NEG = [
    "rusak", "berlubang", "mampet", "mati", "bocor", "kotor",
    "menumpuk", "rapuh", "lubang", "tidak pernah", "dibiarkan",
    "antre", "antri", "lambat", "buruk", "parah", "hancur",
    "menggunung", "tanpa kualitas", "tanpa solusi", "tanpa hasil",
    "tidak ada yang peduli", "tidak disentuh", "tidak ditangani",
    "biarkan jalan", "biarkan sampah", "makin parah", "tidak dilayani",
]

_SARC_PENGUAT = [
    "sekali", "betul", "banget", "benar", "sungguh", "amat", "nian",
]

_SARC_POSITIF_TANPA_PENGUAT = [
    "salut", "acungan jempol", "patut dipuji", "patut diacungi",
    "kagum", "membanggakan", "mengagumkan", "menakjubkan", "hebat",
]


def detect_sarcasm(text: str) -> bool:
    """
    Mendeteksi sarkasme dalam teks bahasa Indonesia.

    4 layer deteksi:
      Layer 1a: kata positif kuat + kontradiksi spesifik
      Layer 1b: kata positif kuat + kata negatif apapun
      Layer 2 : kata positif biasa + penguat + konteks negatif
      Layer 3 : pujian eksplisit + konteks negatif
    """
    tl = text.lower()

    has_strong_pos = any(kw in tl for kw in _SARC_POSITIF_KUAT)
    has_contradict = any(kw in tl for kw in _SARC_KONTRADIKSI)
    has_any_neg    = any(kw in tl for kw in _SARC_KATA_NEG)

    if has_strong_pos and has_contradict:   return True   # Layer 1a
    if has_strong_pos and has_any_neg:      return True   # Layer 1b

    has_penguat   = any(p in tl for p in _SARC_PENGUAT)
    has_basic_pos = any(kw in tl for kw in _SARC_KATA_POS)
    if has_penguat and has_basic_pos and has_any_neg:  return True  # Layer 2

    has_explicit_praise = any(kw in tl for kw in _SARC_POSITIF_TANPA_PENGUAT)
    if has_explicit_praise and has_any_neg:  return True  # Layer 3

    return False


# ================================================================
# FUNGSI RULE — dipanggil oleh classifier.py
# ================================================================

def rule_intent(text: str) -> str | None:
    """
    Klasifikasi intent berbasis keyword.
    Prioritas: darurat > apresiasi > keluhan > saran > permintaan

    Returns None jika tidak ada keyword cocok → serahkan ke ML.
    """
    tl = text.lower()
    rules = [
        ("darurat",    DARURAT_KEYWORDS),
        ("apresiasi",  APRESIASI_KEYWORDS),
        ("keluhan",    KELUHAN_KEYWORDS),
        ("saran",      SARAN_KEYWORDS),
        ("permintaan", PERMINTAAN_KEYWORDS),
    ]
    for intent, keywords in rules:
        if any(_keyword_in_text(tl, kw) for kw in keywords):
            return intent
    return None


def rule_sentiment(text: str, intent: str = "") -> str | None:
    """
    Klasifikasi sentimen berbasis keyword dengan negasi-aware matching.

    Urutan:
      1. Negatif  → cek biasa (sudah eksplisit)
      2. Positif  → negasi-aware
      3. Saran/permintaan → netral
      4. Darurat  → negatif
      5. None     → serahkan ke ML

    Returns None jika tidak ada rule cocok → serahkan ke ML.
    """
    tl = text.lower()

    if any(_keyword_in_text(tl, kw) for kw in SENT_NEGATIF_KW):
        return "negatif"

    if any(_positive_keyword_in_text(tl, kw) for kw in SENT_POSITIF_KW):
        return "positif"

    if intent in ("saran", "permintaan"):
        return "netral"

    if intent == "darurat":
        return "negatif"

    return None