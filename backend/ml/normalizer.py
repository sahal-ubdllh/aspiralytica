# backend/ml/normalizer.py
# ================================================================
# NORMALIZER — Konversi bahasa informal → formal (Bahasa Indonesia)
# ================================================================
# Dipanggil oleh: preprocessor.py
# Fungsi utama  : normalize(text) → str
# ================================================================

import re

# ── Kamus Singkatan & Slang ──────────────────────────────────────
SLANG_DICT = {
    # ── Singkatan umum ──
    "yg":          "yang",
    "dg":          "dengan",
    "dgn":         "dengan",
    "utk":         "untuk",
    "tuk":         "untuk",
    "krn":         "karena",
    "krna":        "karena",
    "krena":       "karena",
    "karna":       "karena",
    "tp":          "tapi",
    "tpi":         "tapi",
    "ttg":         "tentang",
    "spy":         "supaya",
    "biar":        "supaya",
    "blm":         "belum",
    "sdh":         "sudah",
    "udh":         "sudah",
    "udah":        "sudah",
    "dah":         "sudah",
    "jg":          "juga",
    "juga":        "juga",
    "lg":          "lagi",
    "lgi":         "lagi",
    "jd":          "jadi",
    "jdi":         "jadi",
    "gk":          "tidak",
    "ga":          "tidak",
    "gak":         "tidak",
    "ngga":        "tidak",
    "nggak":       "tidak",
    "enggak":      "tidak",
    "tdk":         "tidak",
    "tak":         "tidak",
    "ndak":        "tidak",
    "gbs":         "tidak bisa",
    "gabisa":      "tidak bisa",
    "gausa":       "tidak usah",
    "bs":          "bisa",
    "bisa":        "bisa",
    "hrs":         "harus",
    "hrus":        "harus",
    "msh":         "masih",
    "masi":        "masih",
    "masih":       "masih",
    "sm":          "sama",
    "sma":         "sama",
    "sama":        "sama",
    "bgt":         "sekali",
    "banget":      "sekali",
    "bngt":        "sekali",
    "bener":       "benar",
    "bner":        "benar",
    "emg":         "memang",
    "emang":       "memang",
    "memang":      "memang",
    "gimana":      "bagaimana",
    "gmna":        "bagaimana",
    "gmn":         "bagaimana",
    "knp":         "kenapa",
    "knpa":        "kenapa",
    "kpn":         "kapan",
    "kapan":       "kapan",
    "dmn":         "dimana",
    "dimna":       "dimana",
    "dr":          "dari",
    "dri":         "dari",
    "ke":          "ke",
    "pd":          "pada",
    "ada":         "ada",
    "aja":         "saja",
    "aj":          "saja",
    "doang":       "saja",
    "dong":        "dong",
    "sih":         "sih",
    "nih":         "ini",
    "ni":          "ini",
    "tuh":         "itu",
    "tu":          "itu",
    "lah":         "lah",
    "deh":         "deh",
    "kok":         "kok",
    "woi":         "hei",
    "woy":         "hei",
    "hei":         "hei",

    # ── Kata ganti orang ──
    "gue":         "saya",
    "gw":          "saya",
    "aku":         "saya",
    "w":           "saya",
    "lo":          "anda",
    "lu":          "anda",
    "loe":         "anda",
    "elo":         "anda",
    "mereka":      "mereka",
    "dia":         "dia",
    "dy":          "dia",
    "kita":        "kita",
    "kmi":         "kami",

    # ── Kata sifat / kondisi ──
    "rusak":       "rusak",
    "parah":       "parah",
    "prh":         "parah",
    "buruk":       "buruk",
    "jelek":       "jelek",
    "kotor":       "kotor",
    "bersih":      "bersih",
    "bagus":       "bagus",
    "bgus":        "bagus",
    "baik":        "baik",
    "lama":        "lama",
    "cepat":       "cepat",
    "lambat":      "lambat",
    "lelet":       "lambat",
    "lemot":       "lambat",
    "aman":        "aman",
    "bahaya":      "bahaya",
    "berbahaya":   "berbahaya",
    "darurat":     "darurat",
    "penting":     "penting",
    "urgent":      "darurat",
    "males":       "malas",
    "ribet":       "rumit",
    "njelimet":    "rumit",
    "susah":       "sulit",
    "gampang":     "mudah",
    "sewot":       "kesal",
    "dongkol":     "kesal",
    "mangkel":     "kesal",
    "nyebelin":    "menyebalkan",
    "nyusahin":    "menyusahkan",
    "parah bgt":   "sangat parah",
    "parah banget":"sangat parah",
    "ancur bgt":   "hancur sekali",
    "rusak bgt":   "rusak sekali",

    # ── Ekspresi keluhan informal ──
    "tolong":      "tolong",
    "tlg":         "tolong",
    "tlng":        "tolong",
    "minta":       "minta",
    "mohon":       "mohon",
    "harap":       "harap",
    "segera":      "segera",
    "cepet":       "cepat",
    "cpet":        "cepat",
    "lama bgt":    "sangat lama",
    "lama banget": "sangat lama",
    "kapan":       "kapan",
    "knp":         "kenapa",
    "kok":         "mengapa",
    "masa":        "masa",
    "masa iya":    "masa iya",
    "masa sih":    "masa iya",
    "gimana sih":  "bagaimana",
    "payah":       "payah",
    "percuma":     "percuma",
    "sia-sia":     "sia-sia",
    "keluhan":     "keluhan",
    "lapor":       "lapor",
    "laporan":     "laporan",
    "aduan":       "aduan",
    "pengaduan":   "pengaduan",
    "protes":      "protes",
    "komplain":    "keluhan",
    "complain":    "keluhan",

    # ── Kata kerja informal ──
    "benesin":     "memperbaiki",
    "benerin":     "memperbaiki",
    "beresin":     "membereskan",
    "ngurus":      "mengurus",
    "ngurusin":    "mengurus",
    "ngebenerin":  "memperbaiki",
    "ngeberesin":  "membereskan",
    "ngebersiin":  "membersihkan",
    "bersihin":    "membersihkan",
    "bersiin":     "membersihkan",
    "ngangkut":    "mengangkut",
    "ngangkutin":  "mengangkut",
    "nambahin":    "menambahkan",
    "nambah":      "menambah",
    "ngecat":      "mengecat",
    "ngebangun":   "membangun",
    "ngasih":      "memberikan",
    "ngerespon":   "merespons",
    "ngerti":      "mengerti",
    "nolongin":    "menolong",
    "bantuin":     "membantu",
    "anter":       "antar",
    "anterin":     "mengantarkan",
    "kirimin":     "mengirimkan",
    "pasangin":    "memasang",
    "pasang":      "pasang",
    "diperbaiki":  "diperbaiki",
    "dibersihin":  "dibersihkan",
    "dibenerin":   "diperbaiki",
    "diberesin":   "dibereskan",
    "diurusin":    "diurus",
    "ditanganin":  "ditangani",
    "diselesaiin": "diselesaikan",

    # ── Infrastruktur & tempat ──
    "jln":         "jalan",
    "jl":          "jalan",
    "jalan":       "jalan",
    "jalanan":     "jalan",
    "got":         "got",
    "selokan":     "selokan",
    "drainase":    "drainase",
    "lampu":       "lampu",
    "pju":         "penerangan jalan",
    "tps":         "tempat pembuangan sampah",
    "sampah":      "sampah",
    "trotoar":     "trotoar",
    "trotoarnya":  "trotoar",
    "jembatan":    "jembatan",
    "gorong":      "gorong-gorong",
    "saluran":     "saluran",
    "pipa":        "pipa",
    "air":         "air",
    "listrik":     "listrik",
    "pln":         "pln",
    "pdam":        "pdam",
    "fasilitas":   "fasilitas",
    "fasilitasnya":"fasilitas",

    # ── Kata hubung & lainnya ──
    "ampe":        "sampai",
    "sampe":       "sampai",
    "nyampe":      "sampai",
    "kelar":       "selesai",
    "beres":       "selesai",
    "bikin":       "membuat",
    "bikin susah": "menyusahkan",
    "bikin kesel": "mengecewakan",
    "bikin marah": "mengecewakan",
    "udah":        "sudah",
    "blom":        "belum",
    "belom":       "belum",
    "skrg":        "sekarang",
    "skrang":      "sekarang",
    "sekarang":    "sekarang",
    "minggu":      "minggu",
    "bulan":       "bulan",
    "tahun":       "tahun",
    "hari":        "hari",
    "hri":         "hari",
}

# ── Sarcasm phrases (tidak di-normalize, tapi dikenali di rules.py) ──
SARCASM_MARKERS = [
    "bagus banget padahal",
    "mantap sekali",
    "luar biasa padahal",
    "hebat ya",
    "keren banget padahal",
]


def _build_pattern():
    """
    Buat regex pattern dari SLANG_DICT.
    Urutkan dari panjang ke pendek supaya frasa multi-kata
    di-match duluan (contoh: "parah banget" sebelum "parah").
    """
    sorted_keys = sorted(SLANG_DICT.keys(), key=len, reverse=True)
    escaped     = [re.escape(k) for k in sorted_keys]
    return re.compile(r'\b(' + '|'.join(escaped) + r')\b', re.IGNORECASE)


_PATTERN = _build_pattern()


def normalize(text: str) -> str:
    """
    Normalisasi teks informal Bahasa Indonesia.

    Langkah:
      1. Lowercase
      2. Ganti slang/singkatan sesuai SLANG_DICT
      3. Hapus karakter yang tidak relevan (angka, simbol berulang)
      4. Normalisasi spasi

    Args:
        text: teks mentah dari pengguna

    Returns:
        teks yang sudah dinormalisasi

    Contoh:
        >>> normalize("jln rusak prh bgt gak ada yg benesin tlg!!!")
        'jalan rusak parah sekali tidak ada yang memperbaiki tolong'
    """
    text = text.lower().strip()

    # Ganti kata slang/singkatan
    def _replace(match):
        word = match.group(0).lower()
        return SLANG_DICT.get(word, word)

    text = _PATTERN.sub(_replace, text)

    # Hapus tanda baca berulang (!!!  ??? ...) → satu spasi
    text = re.sub(r'[!?\.]{2,}', ' ', text)

    # Normalisasi spasi
    text = re.sub(r'\s+', ' ', text).strip()

    return text