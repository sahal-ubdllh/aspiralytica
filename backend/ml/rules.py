# backend/ml/rules.py
# ================================================================
# RULE-BASED ENGINE — Keyword Matching + Sarcasm Detection
# ================================================================
#
# CHANGELOG v5 (revisi untuk dataset realistis):
#   - Perluas _NEGATION_WORDS: tambah "ga", "gak", "ngga",
#     "kagak", "enggak", "ndak", "gbs", "blm"
#   - Perluas KELUHAN_KEYWORDS: tambah ekspresi frustrasi informal
#   - Perluas DARURAT_KEYWORDS: tambah frasa informal darurat
#   - Perluas APRESIASI_KEYWORDS: tambah slang apresiasi modern
#   - Perluas SARAN_KEYWORDS: tambah frasa informal saran
#   - Perluas SENT_NEGATIF_KW: tambah kata-kata informal negatif
#   - Perluas SENT_POSITIF_KW: tambah slang positif modern
#   - Perluas sarcasm detection: 4 layer + layer 5 (emoji sarcasm)
#   - Tambah _SARC_KONTRADIKSI_INFORMAL: kontradiksi versi slang
#   - Tambah _SARC_MODERN_PHRASES: frasa sarkasme modern Indonesia
# ================================================================

import re

# ================================================================
# NEGATION-AWARE KEYWORD MATCHING
# ================================================================

_NEGATION_WORDS = {
    # Formal
    "tidak", "tak", "bukan", "belum",
    "tanpa", "kurang",
    # Informal / slang — TAMBAHAN v5
    "ga", "gak", "ngga", "nggak",
    "kagak", "enggak", "ndak",
    "gbs",   # "gak bisa" disingkat
    "blm",   # "belum" singkatan
    "gapernah", "gabisa",
}


def _keyword_in_text(text: str, keyword: str) -> bool:
    return keyword in text


def _positive_keyword_in_text(text: str, keyword: str) -> bool:
    """
    Cek keyword POSITIF dengan memastikan tidak didahului negasi.

    Contoh:
        "memuaskan" di "sangat memuaskan"  → True  ✅
        "memuaskan" di "tidak memuaskan"   → False ✅
        "memuaskan" di "ga memuaskan"      → False ✅  (v5)
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
    # ── TAMBAHAN v5: frasa informal darurat ──────────────────────
    "minta tolong cepet", "tolong buruan",
    "udah kritis", "udah parah banget",
    "orang pingsan", "ada yang pingsan",
    "ada korban", "butuh ambulan",
    "api gede", "api makin gede", "asap tebal",
    "banjir masuk rumah", "air udah masuk",
    "pohon roboh ke", "tiang roboh",
    "ga bisa nafas", "sesak napas",
    "kesetrum", "tersengat listrik",
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
    # ── TAMBAHAN v5: slang apresiasi modern ──────────────────────
    "makasih bgt", "thx bgt", "tengkyu",
    "keren abis", "mantul",        # mantap betul
    "top deh", "top markotop",
    "gass", "gaskeun",             # semangat / bagus
    "jos", "josss",
    "cepet bgt responnya", "respon cepet",
    "akhirnya diperbaiki", "akhirnya beres",
    "alhamdulillah udah", "syukurlah udah",
    "pelayanannya oke", "lumayan oke",
    "petugasnya baik bgt", "orangnya ramah bgt",
    "nggak nyangka secepet ini", "dilayani dengan baik",
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
    # ── TAMBAHAN v5: ekspresi frustrasi informal ─────────────────
    "ga ada yang benerin", "ga ada yang beresin",
    "ga ada yang nanganin", "ga ada yang dateng",
    "ga pernah diperbaiki", "ga pernah diurus",
    "ga kunjung beres", "blm juga diperbaiki",
    "udah berapa kali lapor", "udah sering dilaporin",
    "capek lapor", "males lapor lagi",
    "ngga ada respons", "ngga ada kabar",
    "kagak pernah diperbaiki", "kagak ada tindakan",
    "ampun deh", "aduh parah",
    "masih aja rusak", "masih aja kotor", "masih aja mampet",
    "dari dulu", "dari kemarin", "dari minggu lalu", "dari bulan lalu",
    "numpuk terus", "mampet terus", "banjir terus", "rusak terus",
    "tiap hujan banjir", "tiap musim hujan",
    "warga resah", "warga was-was", "warga khawatir",
    "udah muak", "udah bosen", "bosen nunggu",
    "ga ada harapan", "pesimis",
    "janji mulu ga ditepatin", "janji terus tapi",
    "ngobrol doang", "cuma janji",
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
    # ── TAMBAHAN v5: frasa saran informal ────────────────────────
    "harusnya", "mestinya", "mending",
    "kayaknya perlu", "kayaknya harus",
    "usul biar", "usul aja", "saran aja",
    "coba dong", "coba deh",
    "mending diganti", "mending diperbaiki",
    "gimana kalau", "gimana kalo",
    "bagusnya", "enaknya",
]

PERMINTAAN_KEYWORDS = [
    "mohon", "minta", "harap", "tolong",
    "kami membutuhkan", "kami memerlukan", "kami inginkan",
    "ingin ada", "berharap ada", "perlu ada",
    "diharapkan ada", "sangat diperlukan", "sangat dibutuhkan",
    "perlu ditambah", "perlu dipasang", "perlu dibangun",
    "perlu disediakan", "perlu diperbaiki",
    "segera pasang", "segera bangun", "segera tambah", "segera sediakan",
    # ── TAMBAHAN v5: frasa permintaan informal ───────────────────
    "tlg dong", "tolong dong", "tolong segera",
    "minta dong", "minta tolong",
    "pliss", "please", "plis",
    "dong segera", "buruan dong",
    "kami butuh", "kita butuh", "warga butuh",
    "kapan diperbaiki", "kapan dipasang", "kapan dibenerin",
    "kapan diangkut", "kapan ditangani",
]


# ================================================================
# KEYWORD RULES — SENTIMEN
# ================================================================

# ── NEGATIF ──────────────────────────────────────────────────────
SENT_NEGATIF_KW = [

    # ── A) Single-word / short triggers ─────────────────────────
    "rusak",        "bocor",        "mampet",
    "padam",        "retak",        "berlubang",
    "menumpuk",     "terbengkalai", "ambruk",
    "longsor",      "banjir",       "kumuh",
    "jorok",        "kotor",        "mati",

    # ── B) Phrase triggers ───────────────────────────────────────
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
    "tidak ada perbaikan", "tidak ada yang peduli",
    "tidak ada respons", "tidak ada tindakan", "tidak ada solusi",
    "tidak ada yang datang", "tidak ada yang memperbaiki",
    "tidak ada yang mengurus", "tidak ada yang menangani",
    "tidak ada yang membersihkan", "tidak ada yang membereskan",
    "tidak pernah diperbaiki", "tidak kunjung beres",
    "tidak memperhatikan", "tidak pernah memperhatikan",
    "tidak pernah diperhatikan", "tidak pernah ditangani",
    "tidak pernah ada tindakan", "tidak ada upaya",
    "bertahun-tahun", "dari tahun lalu", "sejak lama",
    "sudah lama", "sudah berhari-hari", "sudah berminggu-minggu",
    "berbulan-bulan", "berkali-kali dilaporkan", "lama sekali",
    "sudah bertahun", "puluhan tahun",
    "sangat buruk", "sangat lambat", "sangat mengecewakan",
    "sangat berbahaya", "sangat disayangkan", "sangat parah",
    "buruk sekali", "parah sekali", "lambat sekali",
    "tidak karuan", "tidak masuk akal", "tidak profesional",
    "memprihatinkan", "mengkhawatirkan",
    "tidak kondusif", "tidak layak", "tidak layak huni",
    "semakin parah", "semakin buruk", "makin parah", "makin rusak",
    "sudah capek", "sudah lelah", "mengganggu", "terganggu",
    "tidak ada respons", "tidak kunjung beres",
    "insiden serius", "situasi kritis", "kondisi kritis",
    "butuh penanganan cepat", "gawat darurat", "nyawa terancam",
    "luka parah", "tidak sadarkan diri",
    "kebakaran", "banjir bandang", "tanah longsor", "gempa",
    "korban jiwa", "keracunan massal", "tenggelam",
    "tidak bagus", "tidak baik", "tidak memuaskan", "tidak puas",
    "tidak beres", "tidak membantu", "tidak ramah", "tidak aman",
    "tidak nyaman", "tidak bersih", "tidak teratur", "tidak jelas",
    "tidak profesional", "tidak responsif",
    "belum ada perbaikan", "belum ada tindakan",

    # ── C) TAMBAHAN v5: ekspresi negatif informal ────────────────
    "parah bgt", "rusak bgt", "kotor bgt", "jorok bgt",
    "lama bgt", "lambat bgt", "buruk bgt",
    "ga ada yg benerin", "ga ada yg beresin",
    "ga ada yg nanganin", "ga pernah diurus",
    "ga kunjung beres", "blm juga beres",
    "masih aja rusak", "masih aja kotor",
    "dari dulu ga", "dari kemarin ga",
    "tiap hujan banjir", "banjir mulu",
    "mampet mulu", "rusak mulu", "kotor mulu",
    "numpuk terus", "ga diangkut2",
    "udah muak", "udah bosen", "capek lapor",
    "ngga ada respons", "ngga ada kabar sama sekali",
    "kagak pernah", "kagak ada",
    "ga ada harapan",
    "ampun deh parah", "aduh parah bgt",
    "kesel bgt", "sebel bgt", "dongkol",
    "nyebelin", "nyusahin", "bikin kesel",
    "percuma lapor", "sia-sia lapor",
    "janji mulu", "omong doang",
    # Angka + waktu — sudah lama
    "3 hari ga", "1 minggu ga", "2 minggu ga",
    "sudah 3 hari", "sudah 1 minggu", "sudah 2 minggu",
    "sudah 3 bulan", "sudah setahun",
    "ngantri berjam", "antre berjam",
    "5 jam", "6 jam", "7 jam", "8 jam",     # waktu antre ekstrem
    # Token emoji yang dihasilkan preprocessor
    "marah", "kesal", "kecewa",             # dari emoji 😡😤🤦
]

# ── POSITIF ──────────────────────────────────────────────────────
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
    # ── TAMBAHAN v5: slang positif modern ────────────────────────
    "makasih bgt", "thx bgt",
    "keren abis", "mantul", "josss", "top deh",
    "oke bgt", "lumayan oke", "respon cepet",
    "akhirnya beres", "akhirnya diperbaiki",
    "alhamdulillah udah", "syukurlah",
    "nggak nyangka secepet ini",
    # Token emoji dari preprocessor
    "jempol",                              # dari 👍
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
    # ── TAMBAHAN v5: frasa positif kuat informal ─────────────────
    "keren banget", "bagus banget", "mantap banget", "hebat banget",
    "top banget", "josss banget", "kece banget",
    "luar biasa min", "salut min", "good job min",
    "amazing", "perfect", "wow keren",
    "smart city", "kota pintar",          # sering di-sarkas
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

# ── TAMBAHAN v5: kontradiksi versi informal ──────────────────────
_SARC_KONTRADIKSI_INFORMAL = [
    "langsung error", "langsung crash", "langsung mati",
    "login aja error", "loading terus", "server mati",
    "server down terus", "aplikasi error", "error mulu",
    "ga pernah dateng", "ga pernah dibenerin", "ga pernah diurus",
    "kagak pernah", "ga ada tindakan",
    "nunggu berjam", "ngantri berjam", "antre sampai",
    "tapi ga dilayani", "tapi ga diperbaiki", "tapi ga ada respons",
    "padahal udah bayar", "padahal udah lapor",
    "padahal udah 3", "padahal baru",          # padahal baru dipasang
    "asal-asalan", "kerja asal", "asal kelar",
    "cuma janji", "janji mulu", "ngobrol doang",
    "tapi mati terus", "tapi rusak terus", "tapi banjir terus",
]

# ── TAMBAHAN v5: frasa sarkasme modern khas media sosial ────────
_SARC_MODERN_PHRASES = [
    # Format: pujian + masalah dalam satu frasa
    "smart city tapi server", "smart city tapi aplikasi",
    "kota pintar tapi lampu",
    "inovasi tapi ga bisa",
    "teknologi canggih tapi error",
    "pelayanan prima tapi",
    "program unggulan tapi",
    "mantap pelayanannya, ngantri",
    "mantap min, udah berapa",
    "bagus banget min padahal",
    "keren banget padahal",
    "hebat ya, sampe",
    "wah keren, antre",
    "alhamdulillah, akhirnya rusak",
    "terima kasih sudah membiarkan",
    "sukses terus ya, warganya",
    "good job, sampahnya",
]

_SARC_KATA_POS = [
    "bangga", "senang", "terima kasih", "luar biasa", "bagus",
    "hebat", "keren", "mantap", "alhamdulillah", "mengagumkan",
    # TAMBAHAN v5
    "josss", "mantul", "top", "kece", "amazing", "smart",
]

_SARC_KATA_NEG = [
    "rusak", "berlubang", "mampet", "mati", "bocor", "kotor",
    "menumpuk", "rapuh", "lubang", "tidak pernah", "dibiarkan",
    "antre", "antri", "lambat", "buruk", "parah", "hancur",
    "menggunung", "tanpa kualitas", "tanpa solusi", "tanpa hasil",
    "tidak ada yang peduli", "tidak disentuh", "tidak ditangani",
    "biarkan jalan", "biarkan sampah", "makin parah", "tidak dilayani",
    # TAMBAHAN v5: kata negatif informal
    "error", "crash", "down", "mati terus",
    "ga bisa", "gabisa", "ga jalan",
    "nunggu lama", "ngantri lama", "antre berjam",
    "ga ada respons", "ga ada kabar",
    "masih rusak", "masih mampet", "masih kotor",
    "ga dibenerin", "ga diurus", "ga ditangani",
    "payah", "percuma", "sia-sia",
]

_SARC_PENGUAT = [
    "sekali", "betul", "banget", "bgt", "benar", "sungguh",
    "amat", "nian",
    # TAMBAHAN v5
    "abis", "poll", "bener-bener", "beneran", "emang",
    "ya ampun", "astaga", "astaghfirullah",
]

_SARC_POSITIF_TANPA_PENGUAT = [
    "salut", "acungan jempol", "patut dipuji", "patut diacungi",
    "kagum", "membanggakan", "mengagumkan", "menakjubkan", "hebat",
    # TAMBAHAN v5
    "nice", "good job", "well done", "bravo",
    "mantap jiwa", "top markotop",
    "keren abis", "mantul",
]

# ── TAMBAHAN v5: pola emoji sarkasme ─────────────────────────────
# Preprocessor mengubah 👍 → "jempol", dll.
# Layer 5 mendeteksi token emoji + konteks negatif.
_SARC_EMOJI_POS_TOKENS = ["jempol", "oke", "mohon"]
_SARC_EMOJI_AFTER_NEG  = True   # flag: aktifkan pengecekan emoji layer 5


def detect_sarcasm(text: str) -> bool:
    """
    Mendeteksi sarkasme dalam teks bahasa Indonesia.

    5 layer deteksi:
      Layer 1a: kata positif kuat + kontradiksi spesifik
      Layer 1b: kata positif kuat + kata negatif apapun
      Layer 2 : kata positif biasa + penguat + konteks negatif
      Layer 3 : pujian eksplisit + konteks negatif
      Layer 4 : frasa sarkasme modern langsung (v5)
      Layer 5 : token emoji positif + kata negatif (v5)
    """
    tl = text.lower()

    has_strong_pos  = any(kw in tl for kw in _SARC_POSITIF_KUAT)
    has_contradict  = any(kw in tl for kw in _SARC_KONTRADIKSI)
    has_contradict |= any(kw in tl for kw in _SARC_KONTRADIKSI_INFORMAL)
    has_any_neg     = any(kw in tl for kw in _SARC_KATA_NEG)

    if has_strong_pos and has_contradict:   return True   # Layer 1a
    if has_strong_pos and has_any_neg:      return True   # Layer 1b

    has_penguat   = any(p in tl for p in _SARC_PENGUAT)
    has_basic_pos = any(kw in tl for kw in _SARC_KATA_POS)
    if has_penguat and has_basic_pos and has_any_neg:  return True  # Layer 2

    has_explicit_praise = any(kw in tl for kw in _SARC_POSITIF_TANPA_PENGUAT)
    if has_explicit_praise and has_any_neg:  return True  # Layer 3

    # Layer 4: frasa sarkasme modern langsung
    if any(phrase in tl for phrase in _SARC_MODERN_PHRASES):
        return True

    # Layer 5: token emoji positif (hasil konversi preprocessor) + negatif
    has_emoji_pos = any(tok in tl for tok in _SARC_EMOJI_POS_TOKENS)
    if has_emoji_pos and has_any_neg:
        return True

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