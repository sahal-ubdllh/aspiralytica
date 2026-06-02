# backend/ml/data.py
# ================================================================
# ASPIRALYTICA NLP DATASET — v3 (Generator Edition)
# ================================================================
#
# Statistik dataset:
#   INTENT  : keluhan=350, permintaan=350, saran=350,
#             apresiasi=350, darurat=350  → TOTAL = 1750
#   SENTIMEN: negatif=300, positif=300, netral=300 → TOTAL = 900
#
# Arsitektur:
#   - Static seed data   : kalimat dikurasi manual (formal + informal)
#   - GENERATED_*        : generator berbasis phrase bank (stochastic)
#   - _HARD_CASES_*      : kasus ambigu / edge case antar kelas
#   - GENERATED_SARCASM  : sarkasme otomatis → masuk kelas keluhan
#
# Cara generate ulang dengan ukuran berbeda:
#   Ubah angka n= di blok GENERATED DATASETS, lalu update label count.
#
# Cara menggunakan:
#   from ml.data import INTENT_DATA, SENTIMENT_DATA
#   texts = INTENT_DATA["texts"]
#   labels = INTENT_DATA["labels"]
# ================================================================

import random

# ================================================================
# GENERATOR DATASET REALISTIS
# ================================================================
# Pendekatan: frase-based generation dengan weighted selection.
# Setiap kalimat dibangun dari slot: [subjek] + [predikat] + [objek]
# + [penguat/konteks] + opsional [emoticon/ekspresi akhir].
# Hasilnya lebih natural dan bervariasi dibanding template fixed.

random.seed(42)  # reproducible untuk paper


def _pick(lst, k=1, weights=None):
    """Ambil k item dari lst, bisa dengan bobot."""
    if k == 1:
        return random.choices(lst, weights=weights, k=1)[0]
    return random.choices(lst, weights=weights, k=k)


# ──────────────────────────────────────────────────────────────────
# KOMPONEN FRASE
# ──────────────────────────────────────────────────────────────────

# Subjek keluhan (siapa yang ngelaporin / kondisi apa)
_SUBJ_KELUHAN = [
    "jalan di depan rumah gue", "jalan di rt sini", "jalan di gang",
    "jalan ke sekolah", "jalan desa", "jalan kampung",
    "got di belakang rumah", "got di ujung jalan", "saluran air",
    "drainase di sini", "selokan depan gang",
    "lampu jalan", "lampu di gang ini", "penerangan jalan",
    "sampah di depan", "tps di sini", "tempat sampah",
    "trotoar", "trotoar depan rumah", "trotoar di jalan utama",
    "fasilitas umum", "fasilitas di taman", "taman kota",
    "pelayanan kantor", "pelayanan kelurahan", "pelayanan puskesmas",
    "petugasnya", "petugas kebersihan", "petugas di sini",
    "pompa air", "air pdam", "pipa air",
    "jembatan di sini", "jembatan kampung",
    "pos ronda", "balai warga", "lapangan olahraga",
    "bak sampah", "tps di ujung", "gerobak sampah",
]

# Predikat kondisi (apa yang terjadi)
_PRED_KELUHAN = [
    ("rusak parah", 3), ("rusak bgt", 3), ("masih rusak", 2),
    ("rusak dan ga diperbaiki", 2), ("makin rusak", 2),
    ("mampet", 2), ("mampet terus", 2), ("mampet mulu", 2),
    ("mati", 2), ("ga nyala", 2), ("padam terus", 1),
    ("kotor banget", 3), ("jorok bgt", 2), ("ga pernah dibersihkan", 2),
    ("numpuk", 2), ("numpuk terus", 2), ("penuh banget", 1),
    ("bocor", 2), ("bocor parah", 2), ("jebol", 1),
    ("ga berfungsi", 2), ("ga diperbaiki", 2), ("terbengkalai", 1),
    ("ancur", 2), ("hancur", 1), ("retak-retak", 1),
    ("berbahaya bgt", 2), ("rawan banget", 1),
    ("lambat banget", 2), ("ga profesional", 1), ("ga ramah", 1),
]

# Konteks temporal (sudah berapa lama)
_KONTEKS_WAKTU = [
    "udah berhari-hari", "udah berminggu-minggu", "udah berbulan-bulan",
    "dari minggu lalu", "dari bulan lalu", "dari tahun lalu",
    "udah lama bgt", "lama banget", "dari dulu",
    "udah 3 hari", "udah seminggu", "udah 2 minggu", "udah sebulan",
    "bertahun-tahun", "udah setahun lebih", "dari tahun kemarin",
    "tiap hari", "tiap hujan", "tiap musim hujan", "tiap kali hujan",
    "terus-terusan", "ga pernah beres", "terus aja kayak gini",
]

# Ekspresi respons tidak ada tindakan
_RESPONS_GA_ADA = [
    "ga ada yang benerin", "ga ada yang nanganin",
    "ga ada yang dateng", "ga ada yang ngurusin",
    "ga pernah diperbaiki", "ga pernah diurus",
    "ga ada tindakan sama sekali", "ga ada respons",
    "ga ada kabar apapun", "dinas tutup mata",
    "dibiarkan aja", "pemerintah cuek aja",
    "laporan ga ditindaklanjuti", "ga kunjung beres",
    "udah dilaporin berkali-kali tapi", "ga ada harapan",
]

# Ekspresi frustrasi penutup
_FRUSTRASI = [
    "😡", "parah sih", "kesel bgt", "nyebelin",
    "udah muak", "capek bgt", "bosen nunggu",
    "ga ada harapan nih", "masa iya kayak gini terus",
    "tolong dong", "kok ga diurus sih",
    "gimana sih pemerintah ini", "percuma lapor",
    "sia-sia aja lapor", "males lapor lagi",
    "warga resah nih", "kami was-was",
    "bahaya bgt loh", "ini serius", "minta tolong deh",
    "", "", "",   # beberapa tanpa ekspresi akhir (lebih natural)
]

# Ekspresi permintaan informal
_PERMINTAAN = [
    "tolong dong segera", "minta tolong", "mohon dong",
    "tlg segera", "harap segera", "pliss dong",
    "kami minta", "warga minta", "kita butuh",
    "kapan diperbaiki dong", "kapan dibenerin",
    "kapan ditangani", "kapan diangkut",
    "buruan dong", "cepetan dong",
    "tolong ya", "minta ya", "mohon ya",
]

# Objek permintaan
_OBJ_PERMINTAAN = [
    "lampu jalan di sini", "penerangan gang ini",
    "sampah yang udah numpuk", "got yang mampet ini",
    "jalan yang berlubang ini", "jalan yang rusak parah",
    "trotoar yang hancur ini", "drainase yang tersumbat",
    "fasilitas taman yang rusak", "tempat sampah baru",
    "petugas yang lebih responsif", "pelayanan yang lebih cepat",
    "zebra cross di depan sekolah", "rambu di persimpangan",
    "armada sampah tambahan", "jadwal angkut sampah yang jelas",
    "pos kesehatan", "posyandu baru di sini",
    "jembatan yang udah lapuk", "pipa air yang bocor",
]

# Ekspresi apresiasi informal
_APRESIASI_EXPR = [
    "makasih bgt ya", "terima kasih banyak",
    "alhamdulillah akhirnya", "syukurlah",
    "seneng bgt deh", "happy banget",
    "salut deh", "keren bgt",
    "mantap bgt kerjanya", "bagus bgt hasilnya",
    "pelayanannya oke bgt", "petugasnya ramah bgt",
    "ga nyangka secepet ini", "nggak nyangka",
    "akhirnya beres juga", "akhirnya ditangani",
    "puas bgt", "sangat puas deh",
    "responsif banget", "cepet banget responnya",
    "kerja bagus min", "good job",
]

# Objek apresiasi
_OBJ_APRESIASI = [
    "jalan udah diperbaiki", "jalan udah diaspal",
    "lampu udah dipasang", "penerangan udah ada",
    "sampah udah diangkut", "got udah dibenerin",
    "drainase udah dibersihkan", "banjir udah berkurang",
    "pelayanannya meningkat bgt", "prosesnya dipercepat",
    "petugas langsung dateng", "langsung ditangani",
    "taman udah dibersihkan", "fasilitas udah diperbaiki",
    "jembatan udah aman", "trotoar udah bagus",
    "program ini sangat membantu", "bansos tepat sasaran",
    "aplikasi pelayanan mudah dipake", "sistem antrian lebih rapi",
]

# Kalimat sarkasme modern
_SARCASM_TEMPLATES = [
    # Format: pujian ironis + kondisi buruk
    "mantap bgt pelayanannya, ngantri {jam} jam baru dilayani 👍",
    "keren bgt min, {masalah} tapi ga diperbaiki juga",
    "bagus banget pengelolaan sampahnya, numpuk terus tiap hari 👍",
    "smart city tapi {masalah_tech}, gimana ya",
    "hebat ya petugas kita, dateng terlambat dan kerja asal-asalan",
    "salut deh sama pemda, {masalah} dibiarkan bertahun-tahun",
    "wah keren bgt, {masalah} tapi warga disuruh sabar terus",
    "luar biasa min aplikasinya, {masalah_tech} mulu",
    "mantap sekali, udah lapor {kali} kali tapi ga ada respons",
    "bagus banget programnya, warganya tetep kesulitan aja",
    "terima kasih udah membiarkan {masalah} selama ini ya 😊",
    "program unggulan katanya, tapi {masalah} ga pernah beres",
    "good job min, {masalah} makin parah dari hari ke hari",
    "top markotop, janji diperbaiki {waktu} lalu tapi sampe sekarang",
    "alhamdulillah ya, sampah di sini udah jadi gunung sendiri",
    "inovasi pelayanan katanya, {masalah_tech} mulu dari kemarin",
    "pelayanan prima katanya, realitanya {keluhan_pelayanan}",
    "kota pintar katanya tapi lampu jalannya aja pada mati",
    "hebat min, petugas kita emang paling jago ngumpet",
    "wah bagus ya, drainasenya juga ikutan rusak biar kompak",
]

_SARC_JAM   = ["3", "4", "5", "6", "7"]
_SARC_KALI  = ["3", "5", "berkali-kali", "puluhan"]
_SARC_WAKTU = ["bulan lalu", "tahun lalu", "3 bulan lalu", "2 tahun lalu"]

_SARC_MASALAH = [
    "jalan berlubang parah", "got mampet terus",
    "lampu jalan mati", "sampah numpuk",
    "banjir tiap hujan", "trotoar hancur",
    "fasilitas rusak semua", "drainase ga berfungsi",
    "pipa bocor", "pompa air mati",
]

_SARC_MASALAH_TECH = [
    "server mati", "aplikasinya error", "login aja error",
    "loading terus ga bisa masuk", "down terus",
    "fitur laporan ga bisa dipake", "crash mulu",
    "notifikasi ga muncul", "data warga ga tersimpan",
]

_SARC_KELUHAN_PELAYANAN = [
    "antrinya 5 jam ga dilayani",
    "petugas ga ada di tempat",
    "disuruh balik lagi besok",
    "dokumennya minta ini itu terus",
    "sistemnya ga bisa diakses dari tadi",
    "data kita katanya ga ketemu",
]

# Darurat informal
_DARURAT_TEMPLATES = [
    "ada {kejadian} di {lokasi}, minta tolong cepet!",
    "darurat! {kejadian} di {lokasi}, butuh bantuan segera",
    "tolong! {kejadian} {lokasi}, ada korban",
    "kebakaran {lokasi}, api udah gede banget tlg bantuan",
    "banjir udah masuk rumah di {lokasi}, tolong evakuasi",
    "ada orang pingsan di {lokasi}, butuh ambulan sekarang",
    "tiang listrik roboh di {lokasi}, berbahaya bgt",
    "longsor di {lokasi}, warga minta tolong segera",
    "ada {kejadian} darurat di {lokasi} tolong respon cepet",
    "gas bocor di {lokasi}!! tolong tim penanggulangan",
]

_DAR_KEJADIAN = [
    "kebakaran", "banjir bandang", "tanah longsor",
    "kecelakaan parah", "pohon tumbang",
    "dinding ambruk", "pipa gas bocor",
    "korban luka parah", "orang keracunan",
]

_DAR_LOKASI = [
    "rt 05 rw 03", "jalan di depan pasar",
    "gang sempit ujung", "permukiman padat",
    "dekat sungai", "bantaran kali",
    "belakang sekolah", "depan masjid",
    "perumahan blok c", "kampung seberang",
]

# Hard cases: ambigu antar kelas
_HARD_CASES_INTENT = [
    # Keluhan + unsur saran (ambigu keluhan/saran)
    "jalan di sini rusak parah, harusnya ada jadwal perbaikan rutin",
    "sampah numpuk terus, kayaknya perlu petugas tambahan deh",
    "got mampet mulu, mestinya dikeruk sebulan sekali kan",
    "lampu mati lagi, mending diganti yang LED biar ga sering rusak",
    "drainase buruk bikin banjir, perlu diperbaiki sistemnya",
    "pelayanan lambat banget, sebaiknya tambah loket dong",
    # Keluhan + unsur permintaan (ambigu keluhan/permintaan)
    "trotoar ancur, minta dong segera diperbaiki",
    "penerangan gelap bgt, tolong pasang lampu baru ya",
    "petugas ga pernah dateng, mohon ditegur atasan ya",
    # Permintaan lemah (ambigu permintaan/saran)
    "kayaknya perlu ada taman di sini biar warga bisa olahraga",
    "warga ingin ada angkutan umum ke daerah kami",
    "alangkah baiknya kalau ada posyandu dekat sini",
    # Apresiasi + sedikit saran (ambigu apresiasi/saran)
    "pelayanannya udah lumayan, tapi masih bisa ditingkatkan lagi",
    "jalan udah diperbaiki, semoga bisa lebih cepat ke depannya",
    "terima kasih taman udah dibersihkan, kalau ada kursi lebih oke",
    # Ekspresi netral yang bisa salah dikira keluhan
    "kondisi jalan memang perlu perhatian lebih dari dinas",
    "fasilitas di sini masih bisa dibenahi lebih baik lagi",
    "pelayanan berjalan normal sesuai jam operasional",
]

_HARD_CASES_SENTIMENT = [
    # Negatif tapi formulasi sopan
    "mohon diperhatikan kondisi jalan yang sudah cukup lama tidak diperbaiki",
    "kami berharap drainase yang mampet segera mendapat perhatian",
    "warga merasa pelayanan masih perlu banyak peningkatan",
    "kondisi ini tentu tidak ideal untuk kenyamanan warga",
    "kami mengharapkan respons yang lebih cepat dari dinas terkait",
    # Positif tapi diawali konteks negatif (ambigu)
    "meski sempat rusak lama, jalan akhirnya diperbaiki juga",
    "tadinya khawatir ga ditangani, ternyata petugas datang cepet",
    "walaupun antri lama, pelayanannya tetap memuaskan kok",
    # Netral yang bisa dikira positif/negatif
    "jalan di sini belum diperbaiki sudah beberapa bulan",
    "petugas tidak datang sesuai jadwal yang ditentukan",
    "lampu jalan di gang ini tidak menyala sejak minggu lalu",
    "air pdam tidak mengalir sejak kemarin siang",
    "sampah belum diangkut padahal jadwalnya tadi pagi",
    # Sarkasme halus (tanpa kata kuat, susah dideteksi)
    "keren ya aplikasinya, mau laporan aja butuh 10 langkah",
    "bagus juga sih sistemnya, tiap mau login pasti gagal",
    "ya memang sudah takdir got di sini mampet terus kali",
    "biasalah, udah hapal jadwal 'segera diperbaiki' artinya apa",
    "emang dari sono-nya lampu ini emang ga suka nyala",
]


def _generate_keluhan(n: int) -> list[str]:
    """Generate n kalimat keluhan natural dengan variasi tinggi."""
    results = []
    pred_list  = [p[0] for p in _PRED_KELUHAN]
    pred_w     = [p[1] for p in _PRED_KELUHAN]

    for _ in range(n):
        subj    = _pick(_SUBJ_KELUHAN)
        pred    = _pick(pred_list, weights=pred_w)
        waktu   = _pick(_KONTEKS_WAKTU)
        respons = _pick(_RESPONS_GA_ADA)
        frustr  = _pick(_FRUSTRASI)

        # Variasi struktur kalimat
        pola = random.randint(1, 5)
        if pola == 1:
            s = f"{subj} {pred} {waktu}, {respons}"
        elif pola == 2:
            s = f"{waktu} {subj} {pred}, {respons}"
        elif pola == 3:
            s = f"{subj} udah {pred} {waktu} tapi {respons}"
        elif pola == 4:
            s = f"{subj} {pred}, {waktu}, {respons}. {frustr}"
        else:
            s = f"kok {subj} {pred} mulu sih, {waktu} {respons}"

        if frustr and pola not in (4,):
            s = s.rstrip() + f". {frustr}"

        results.append(s.strip())
    return results


def _generate_permintaan(n: int) -> list[str]:
    """Generate n kalimat permintaan informal."""
    results = []
    for _ in range(n):
        eksp = _pick(_PERMINTAAN)
        obj  = _pick(_OBJ_PERMINTAAN)
        pola = random.randint(1, 3)
        if pola == 1:
            s = f"{eksp} {obj} ya"
        elif pola == 2:
            s = f"{eksp} {obj} dong, warga udah nunggu lama"
        else:
            s = f"kami {eksp} {obj} secepatnya"
        results.append(s.strip())
    return results


def _generate_apresiasi(n: int) -> list[str]:
    """Generate n kalimat apresiasi natural."""
    results = []
    for _ in range(n):
        expr = _pick(_APRESIASI_EXPR)
        obj  = _pick(_OBJ_APRESIASI)
        pola = random.randint(1, 3)
        if pola == 1:
            s = f"{expr}, {obj}"
        elif pola == 2:
            s = f"{obj}, {expr} deh"
        else:
            s = f"{expr} karena {obj}, semoga terus begini"
        results.append(s.strip())
    return results


def _generate_sarcasm(n: int) -> list[str]:
    """Generate n kalimat sarkasme realistis."""
    results = []
    for _ in range(n):
        tmpl = _pick(_SARCASM_TEMPLATES)
        s = tmpl.format(
            jam               = _pick(_SARC_JAM),
            masalah           = _pick(_SARC_MASALAH),
            masalah_tech      = _pick(_SARC_MASALAH_TECH),
            kali              = _pick(_SARC_KALI),
            waktu             = _pick(_SARC_WAKTU),
            keluhan_pelayanan = _pick(_SARC_KELUHAN_PELAYANAN),
        )
        results.append(s.strip())
    return results


def _generate_darurat(n: int) -> list[str]:
    """Generate n kalimat darurat informal."""
    results = []
    for _ in range(n):
        tmpl    = _pick(_DARURAT_TEMPLATES)
        kejadian = _pick(_DAR_KEJADIAN)
        lokasi   = _pick(_DAR_LOKASI)
        s = tmpl.format(kejadian=kejadian, lokasi=lokasi)
        results.append(s.strip())
    return results


# ──────────────────────────────────────────────────────────────────
# PHRASE BANK TAMBAHAN — untuk saran, sentimen negatif/positif/netral
# ──────────────────────────────────────────────────────────────────

# Komponen saran
_SARAN_INTRO = [
    "sebaiknya", "alangkah baiknya", "disarankan agar", "saran kami",
    "lebih baik kalau", "perlu dipertimbangkan", "ada baiknya",
    "kiranya perlu", "usul kami", "mungkin perlu",
    "kayaknya perlu", "bisa dipertimbangkan", "saran aja sih",
    "menurut saya sebaiknya", "kalau boleh saran",
]
_SARAN_SUBJ = [
    "pemerintah", "dinas terkait", "pemda", "pihak kelurahan",
    "pengelola", "petugas", "aparat", "dinas kebersihan",
    "dinas PU", "PDAM",
]
_SARAN_AKSI = [
    "membuat jadwal rutin pemeliharaan", "menambah armada",
    "memasang {obj} baru", "memperbaiki sistem {obj}",
    "membuka layanan online untuk", "menambah petugas",
    "melakukan evaluasi berkala terhadap", "mengadakan sosialisasi",
    "meningkatkan kualitas {obj}", "merenovasi fasilitas",
    "menerapkan sistem digital untuk", "menambah jam operasional",
    "melibatkan warga dalam perencanaan", "rutin mengevaluasi",
    "membentuk tim khusus untuk menangani",
]
_SARAN_OBJ = [
    "jalan", "drainase", "sampah", "lampu jalan",
    "pelayanan publik", "taman kota", "trotoar",
    "sistem antrian", "aplikasi pengaduan", "fasilitas umum",
    "angkutan umum", "pos kesehatan", "bank sampah",
    "penerangan gang", "toilet umum",
]
_SARAN_ALASAN = [
    "agar warga tidak kesulitan", "supaya lebih efisien",
    "biar tidak terjadi lagi masalah ini", "demi kenyamanan warga",
    "biar lebih responsif terhadap keluhan", "agar lebih terjangkau",
    "supaya lingkungan lebih bersih", "biar warga tidak perlu antri",
    "agar lebih tepat sasaran", "supaya tidak berulang terus",
    "biar transparan dan akuntabel", "demi keselamatan warga",
]

# Komponen sentimen negatif (untuk generator)
_NEG_SUBJ = [
    "jalan di sini", "lampu jalan", "sampah", "got",
    "drainase", "pelayanan", "fasilitas", "air pdam",
    "trotoar", "puskesmas", "petugas", "kondisi lingkungan",
]
_NEG_PRED = [
    "rusak parah ga diperbaiki", "mati terus ga ada yang benerin",
    "numpuk ga diangkut-angkut", "mampet banjir tiap hujan",
    "buruk bgt mengecewakan warga", "tidak layak sangat memprihatinkan",
    "bocor sudah lama diabaikan", "makin parah dari hari ke hari",
    "tidak berfungsi sudah berbulan-bulan", "jorok tidak terawat sama sekali",
]
_NEG_WAKTU = [
    "udah berminggu-minggu", "dari bulan lalu", "bertahun-tahun",
    "udah 3 hari", "udah sebulan lebih", "dari dulu",
    "ga pernah beres", "terus-terusan",
]
_NEG_PENUTUP = [
    "sangat mengecewakan", "warga kecewa besar", "ga ada tindakan apapun",
    "laporan tidak direspons", "pemerintah tidak peduli",
    "kami udah capek nunggu", "percuma lapor", "sia-sia aja",
    "minta tolong ditangani", "ini sudah darurat", "",
]

# Komponen sentimen positif (untuk generator)
_POS_EKSP = [
    "alhamdulillah", "syukurlah", "seneng banget",
    "puas bgt sama", "makasih banyak ya",
    "salut deh sama", "top bgt", "keren bgt",
    "bangga sama", "mantap bgt",
]
_POS_OBJ = [
    "jalan udah diperbaiki", "drainase udah dibersihkan",
    "lampu udah dipasang dan nyala", "sampah rutin diangkut",
    "pelayanannya cepat dan ramah", "petugas responsif bgt",
    "program ini tepat sasaran", "fasilitas udah layak",
    "got udah dikeruk ga banjir lagi", "taman udah bersih indah",
    "puskesmas pelayanannya meningkat", "aplikasi pelayanan mudah dipake",
    "bansos tepat sasaran dan cepat cair", "pembangunan selesai tepat waktu",
]
_POS_HARAP = [
    "semoga terus begini", "pertahankan terus ya",
    "lanjutkan programnya", "semoga makin baik",
    "ditingkatkan lagi", "ini yang kami harapkan selama ini",
    "", "", "",  # beberapa tanpa kalimat harapan
]

# Komponen sentimen netral (untuk generator)
_NETRAL_INFO = [
    "prosedur {hal} di kantor {tempat}",
    "jadwal {hal} di wilayah ini",
    "syarat {hal} untuk warga",
    "cara mengurus {hal}",
    "biaya dan proses {hal}",
    "mekanisme {hal} yang berlaku",
    "informasi tentang {hal}",
    "ketentuan {hal} bagi warga",
]
_NETRAL_HAL = [
    "pembuatan KTP", "perpanjangan SIM", "kartu keluarga",
    "akta kelahiran", "surat domisili", "izin usaha",
    "bantuan sosial", "program beasiswa", "vaksinasi",
    "angkutan sampah", "pelayanan publik", "pengaduan online",
    "program bantuan rumah", "kartu kesehatan", "surat pindah",
]
_NETRAL_TEMPAT = [
    "kelurahan", "kecamatan", "dinas terkait",
    "kantor pelayanan", "puskesmas", "SAMSAT",
]
_NETRAL_KONDISI = [
    "kondisi {obj} masih perlu perhatian lebih dari dinas terkait",
    "fasilitas {obj} berjalan normal sesuai jam operasional",
    "{obj} perlu diperbaiki agar lebih layak digunakan warga",
    "program {obj} sudah berjalan dan warga mulai merasakan manfaatnya",
    "petugas {obj} sudah berupaya memberikan pelayanan yang lebih baik",
    "proses {obj} membutuhkan waktu sesuai prosedur yang berlaku",
]
_NETRAL_OBJ2 = [
    "jalan", "drainase", "pelayanan", "sampah",
    "fasilitas umum", "lampu jalan", "air bersih",
    "angkutan umum", "program bantuan", "layanan kesehatan",
]


def _generate_saran(n: int) -> list[str]:
    """Generate n kalimat saran yang natural dan bervariasi."""
    results = []
    for _ in range(n):
        intro = _pick(_SARAN_INTRO)
        subj  = _pick(_SARAN_SUBJ)
        aksi  = _pick(_SARAN_AKSI).replace("{obj}", _pick(_SARAN_OBJ))
        obj   = _pick(_SARAN_OBJ)
        alasan = _pick(_SARAN_ALASAN)

        pola = random.randint(1, 5)
        if pola == 1:
            s = f"{intro} {subj} {aksi} {obj}"
        elif pola == 2:
            s = f"{intro} ada {obj} yang lebih {_pick(['baik','layak','teratur','memadai'])}, {alasan}"
        elif pola == 3:
            s = f"{intro} {aksi} {obj}, {alasan}"
        elif pola == 4:
            s = f"saran: {aksi} {obj} {alasan}"
        else:
            s = f"{intro} {subj} lebih {_pick(['aktif','responsif','konsisten','transparan'])} dalam menangani {obj}"

        results.append(s.strip())
    return results


def _generate_negatif(n: int) -> list[str]:
    """Generate n kalimat sentimen negatif yang natural."""
    results = []
    for _ in range(n):
        subj    = _pick(_NEG_SUBJ)
        pred    = _pick(_NEG_PRED)
        waktu   = _pick(_NEG_WAKTU)
        penutup = _pick(_NEG_PENUTUP)

        pola = random.randint(1, 5)
        if pola == 1:
            s = f"{subj} {pred} {waktu}"
        elif pola == 2:
            s = f"{waktu} {subj} {pred}, {penutup}"
        elif pola == 3:
            s = f"{subj} udah {pred} {waktu}, {penutup}"
        elif pola == 4:
            s = f"udah lapor soal {subj} tapi {pred} terus, {penutup}"
        else:
            s = f"kok {subj} {pred} terus sih {waktu}? {penutup}"

        results.append(s.strip())
    return results


def _generate_positif(n: int) -> list[str]:
    """Generate n kalimat sentimen positif yang natural."""
    results = []
    for _ in range(n):
        eksp  = _pick(_POS_EKSP)
        obj   = _pick(_POS_OBJ)
        harap = _pick(_POS_HARAP)

        pola = random.randint(1, 4)
        if pola == 1:
            s = f"{eksp} {obj}"
        elif pola == 2:
            s = f"{obj}, {eksp} deh"
        elif pola == 3:
            s = f"{eksp} karena {obj}. {harap}".strip()
        else:
            s = f"{obj}! {eksp}. {harap}".strip()

        results.append(s.strip().rstrip("!").strip())
    return results


def _generate_netral(n: int) -> list[str]:
    """Generate n kalimat sentimen netral (info/prosedur/kondisi)."""
    results = []
    for _ in range(n):
        pola = random.randint(1, 3)
        if pola == 1:
            # Format tanya-info
            tmpl = _pick(_NETRAL_INFO)
            hal  = _pick(_NETRAL_HAL)
            tmp  = _pick(_NETRAL_TEMPAT)
            s = tmpl.format(hal=hal, tempat=tmp)
        elif pola == 2:
            # Format kondisi netral
            tmpl = _pick(_NETRAL_KONDISI)
            obj2 = _pick(_NETRAL_OBJ2)
            s = tmpl.format(obj=obj2)
        else:
            # Format informatif singkat
            hal  = _pick(_NETRAL_HAL)
            tmp  = _pick(_NETRAL_TEMPAT)
            s = f"info tentang {hal} di {tmp} gimana ya prosedurnya"

        results.append(s.strip())
    return results


# ──────────────────────────────────────────────────────────────────
# GENERATED DATASETS — target 350 per kelas intent, 300 sentimen
# ──────────────────────────────────────────────────────────────────
# Rumus: target = static_count + generated_count
#   keluhan   : 199 static + 18 hard + 30 sarc + 103 gen = 350
#   permintaan: 79  static + 271 gen                     = 350
#   saran     : 56  static + 294 gen                     = 350
#   apresiasi : 53  static + 297 gen                     = 350
#   darurat   : 30  static + 320 gen                     = 350
#
#   negatif   : 58 static + 20 sarc_sent + 15 hard + 207 gen = 300
#   positif   : 104 static + 196 gen                         = 300
#   netral    : 119 static + 181 gen                         = 300

GENERATED_KELUHAN    = _generate_keluhan(103)
GENERATED_PERMINTAAN = _generate_permintaan(271)
GENERATED_SARAN      = _generate_saran(294)
GENERATED_APRESIASI  = _generate_apresiasi(297)
GENERATED_SARCASM    = _generate_sarcasm(30)    # masuk kelas keluhan
GENERATED_DARURAT    = _generate_darurat(320)

# Generator sentimen
GENERATED_NEGATIF = _generate_negatif(207)
GENERATED_POSITIF = _generate_positif(196)
GENERATED_NETRAL  = _generate_netral(181)

# Sarkasme otomatis untuk sentimen NEGATIF
GENERATED_SARC_NEGATIF_SENT = _generate_sarcasm(20)


# ================================================================
# INTENT DATA
# ================================================================

INTENT_DATA = {
    "texts": [

        # ==========================================================
        # KELUHAN (199 static + 18 hard + 30 sarcasm + 103 generated)
        # Total = 350
        # Total ≈ 378
        # ==========================================================
        "Jalan rusak parah sudah lama tidak diperbaiki oleh dinas",
        "Sampah tidak diangkut berhari-hari baunya menyengat sekali",
        "Lampu jalan mati sudah seminggu gelap dan berbahaya",
        "Air PDAM keruh tidak layak diminum warga sudah mengeluh",
        "Drainase mampet banjir setiap kali hujan turun deras",
        "Fasilitas umum rusak dibiarkan tidak ada perbaikan sama sekali",
        "Trotoar hancur berlubang bahaya buat pejalan kaki",
        "Taman kota jorok sampah berserakan tidak ada yang membersihkan",
        "Jembatan retak berbahaya tidak segera diperbaiki pemerintah",
        "Halte bus rusak atap bocor tidak ada perbaikan sama sekali",
        "Genangan air selalu ada di jalan ini setiap kali hujan",
        "Tempat sampah meluber mengotori seluruh lingkungan sekitar",
        "Saluran got tersumbat menimbulkan bau tidak sedap dimana-mana",
        "Kabel listrik menjuntai rendah sangat berbahaya bagi warga",
        "Fasilitas taman bermain rusak berbahaya untuk anak-anak",
        "Penerangan jalan di gang kampung mati total sudah lama sekali",
        "Papan nama jalan sudah hilang tidak ada penggantinya",
        "Pelayanan kantor sangat lambat antre berjam-jam tidak ada kejelasan",
        "Pelayanan buruk petugas tidak mau membantu warga sama sekali",
        "Pelayanan sangat lambat dan mengecewakan sekali tidak karuan",
        "Pelayanan kantor buruk sekali lama antrenya tidak masuk akal",
        "Petugas tidak ramah pelayanan sangat mengecewakan warga",
        "Pelayanan publik di sini sangat buruk harus segera diperbaiki",
        "Petugas tidak profesional dan tidak responsif terhadap keluhan",
        "Pasar kumuh kotor sekali tidak ada pengelolaan kebersihan",
        "Kondisi jalan di sini memang memprihatinkan sekali bagi warga",
        "Warga sudah lelah dengan masalah ini yang tidak kunjung beres",
        "Sudah capek melaporkan berkali-kali tapi tidak ada respons",
        "Situasi di sini sudah tidak kondusif lagi bagi semua warga",
        "Kondisi pasar sangat memprihatinkan dan kotor tidak layak",
        "Sampah semakin parah setiap hari tidak ada yang menangani",
        "Jalan semakin buruk makin parah tidak ada perbaikan apapun",
        "Tidak ada tindakan nyata dari pemerintah terhadap keluhan kami",
        "Sudah berkali-kali dilaporkan tapi tidak pernah diperbaiki",
        "Lingkungan semakin kotor dan tidak terawat sangat disayangkan",
        "Fasilitas sangat tidak layak dan membahayakan keselamatan warga",
        "Air bersih tidak mengalir sudah tiga hari warga sangat kesulitan",
        "Lampu tidak menyala sudah berminggu-minggu wilayah sangat gelap",
        "Pelayanan tidak ada harapan petugas abai terhadap warga",
        "Kantor pelayanan selalu tutup tidak sesuai jam operasional",
        "Jalan berlubang sudah menahun tidak pernah ada perbaikan berarti",
        "Sampah menumpuk di pinggir jalan sudah sangat mengganggu warga",
        "Got mampet banjir terus tiap hujan warga sudah muak",
        "Lampu penerangan jalan rusak sudah berbulan-bulan tidak diganti",
        "Pelayanan di puskesmas sangat lambat antrean mengular panjang",
        "Petugas kebersihan tidak pernah datang ke wilayah kami",
        "Jalan setapak rusak parah tidak bisa dilalui motor sama sekali",
        "Fasilitas MCK umum kotor dan tidak pernah dibersihkan petugas",
        "Pengelolaan parkir semrawut dan merugikan warga sekitar",
        "Drainase jebol sehingga halaman rumah warga selalu banjir",
        "Atap balai warga bocor parah tidak kunjung diperbaiki dinas",
        "Pompa air rusak warga tidak mendapat air bersih berhari-hari",
        "Pos ronda rubuh berbahaya tidak ada yang mau memperbaiki",
        "Jembatan kayu sudah lapuk sangat berbahaya untuk dilalui",
        "Pipa air bocor sudah dilaporkan berulang kali tidak ditangani",
        "Taman bermain kotor dan rusak anak-anak tidak bisa bermain",
        "Warung pinggir jalan memblokir trotoar pejalan kaki tidak bisa lewat",
        "Kendaraan berat sering lewat dan merusak jalan pemukiman",
        "Lampu merah rusak menyebabkan kemacetan dan kecelakaan",
        "Petugas sampah tidak datang sudah seminggu sampah menumpuk",
        "Gorong-gorong tersumbat sampah banjir menggenang tiap hujan",
        "Pelayanan adminduk sangat berbelit-belit menyita waktu warga",
        "Bak sampah di taman overload tidak pernah dikosongkan",
        "Tanggul sungai bocor berbahaya bagi warga yang tinggal di bantaran",
        "Jalur pejalan kaki diokupasi PKL sehingga pejalan kaki di jalan",
        "CCTV di area perumahan banyak yang rusak tidak bisa merekam",
        "Pohon tua rawan tumbang tidak pernah dipangkas oleh dinas",
        "Lapangan olahraga rusak tidak terawat tidak bisa digunakan",
        "Saluran irigasi tersumbat sawah petani gagal mendapat air",
        "Penerangan di gang sempit tidak ada sangat gelap dan rawan",
        "Petugas yang bertugas sering tidak ada di tempat saat dibutuhkan",
        "Lift gedung pemerintah sering rusak tidak nyaman bagi lansia",
        "Pengelolaan pasar sangat buruk bau dan tidak higienis",
        "Papan petunjuk jalan rusak dan menyesatkan pengguna jalan",
        "Tempat pembuangan sampah terbuka menimbulkan bau busuk parah",
        "Rambu lalu lintas hilang tidak ada penggantinya berbahaya",
        "Jalan raya bergelombang tidak rata berbahaya bagi pengendara",
        "Air sungai tercemar limbah warga tidak bisa menggunakannya",
        "Pelayanan STNK di Samsat sangat lama tidak efisien",
        "Petugas pajak tidak ramah dan prosesnya sangat berbelit",
        "Sistem drainase di kawasan ini sangat buruk perlu total dirombak",
        "Tiang listrik miring hampir roboh berbahaya bagi warga",
        "Bangunan liar di pinggir sungai tidak pernah ditertibkan",
        "Pelayanan di RSUD sangat buruk pasien tidak dilayani dengan baik",
        "Fasilitas toilet umum di pasar sangat kotor dan tidak layak",
        "Jalan rusak semakin parah di musim hujan tidak ada tindakan",
        "Warga sudah muak dengan masalah ini yang tidak pernah selesai",
        "Tidak ada kejelasan kapan masalah ini akan ditangani pemerintah",
        "Sudah banyak korban kecelakaan di sini tapi tidak ada perbaikan",
        "Lingkungan kumuh tidak pernah mendapat perhatian dari pemerintah",
        "Petugas tidak pernah melakukan ronda malam wilayah tidak aman",
        "Pengangkutan sampah tidak teratur jadwalnya tidak jelas",
        "Fasilitas kesehatan di desa kami sangat minim dan tidak memadai",
        "Pelayanan birokrasi sangat lambat dan tidak transparan",
        "Genangan air di jalan sudah berbulan tidak ada penanganan",
        "Kerusakan jalan sudah parah tapi tidak masuk skala prioritas",
        "Gedung sekolah rusak sudah lama tidak diperbaiki oleh dinas",
        "Rel pengaman jembatan rusak berbahaya bagi pejalan kaki",
        "Warga sudah tidak percaya laporan mereka akan ditindaklanjuti",
        "jln rusak parah bgt gak ada yg benesin tlg dong",
        "sampah numpuk udah berhari2 bau banget gak diangkut2",
        "lampu jalan mati udh berminggu2 gelap bgt berbahaya",
        "air pdam keruh bgt gak layak diminum warga udh ngeluh",
        "got mampet banjir mulu tiap ujan gak ada yg beresin",
        "fasilitasnya rusak dibiarkan aja gak ada perbaikan sama sekali",
        "trotoar ancur berlubang bahaya bgt buat pejalan kaki",
        "taman kota jorok banget sampah berserakan gak ada yg bersihin",
        "pelayanan lambat banget antre berjam2 gak ada kejelasan",
        "petugasnya gak mau bantu warga sama sekali payah bgt",
        "pelayanan buruk bgt gak profesional ngga memuaskan",
        "pasar kumuh bgt gak ada pengelolaan kebersihan sama sekali",
        "udah capek lapor berkali2 tapi ngga ada respons sama sekali",
        "situasi sini udah ga kondusif banget sangat memprihatinkan",
        "sampah makin parah tiap hari gak ada yg nanganin sama sekali",
        "air bersih ga ngalir udah 3 hari warga susah banget",
        "lampu ga nyala udah berminggu2 gelap bgt dan rawan",
        "kantor pelayanan selalu tutup ga sesuai jam operasional",
        "jalan berlubang udah menahun ga pernah ada perbaikan",
        "got mampet lagi banjir terus tiap hujan warga udah muak",
        "fasilitasnya jorok banget gak pernah dibersihkan petugas",
        "drainase jebol halaman rumah warga jadi banjir terus",
        "pipa air bocor udah dilaporin berkali2 ga ditangani juga",
        "petugas kebersihan ga pernah datang ke wilayah kami sih",
        "kendaraan berat sering lewat bikin jalan pemukiman rusak",
        "pelayanan adminduk ribet banget menyita waktu warga",
        "tanggul sungai bocor berbahaya bgt warga resah",
        "petugas yg bertugas sering ga ada di tempat saat dibutuhin",
        "air sungai tercemar limbah warga ga bisa pakai lagi",
        "jalan raya bergelombang gak rata berbahaya bgt buat pengendara",
        "sistem drainase kawasan ini buruk bgt perlu dirombak total",
        "tiang listrik miring hampir roboh berbahaya bgt buat warga",
        "bangunan liar di pinggir sungai ga pernah ditertibkan dinas",
        "toilet umum di pasar jorok banget ga layak sama sekali",
        "jalan rusak makin parah di musim hujan ga ada tindakan",
        "warga udah muak masalah ini ga pernah selesai2",
        "ga ada kejelasan kapan masalah ini ditangani pemerintah",
        "lingkungan kumuh ga pernah dapat perhatian dari pemerintah",
        "petugas ga pernah ronda malam wilayah jadi ga aman",
        "pengangkutan sampah ga teratur jadwalnya ga jelas kapan",
        "fasilitas kesehatan di desa kami minim banget ga memadai",
        "pelayanan birokrasi lambat banget dan ga transparan",
        "genangan air di jalan udah berbulan ga ada penanganan",
        "kerusakan jalan udah parah tapi ga masuk skala prioritas",
        "gedung sekolah rusak udah lama ga diperbaiki dinas",
        "warga udah ga percaya laporan mereka bakal ditindaklanjuti",
        "lampu merah rusak bikin macet dan rawan kecelakaan bgt",
        "pelayanan di puskesmas lambat banget antrean panjang bgt",
        "jembatan kayu udah lapuk sangat berbahaya buat dilewati",
        "pos ronda rubuh berbahaya ga ada yg mau benerin",
        "atap balai warga bocor parah ga kunjung diperbaiki dinas",
        "pompa air rusak warga ga dapet air bersih berhari2",
        "lapangan olahraga rusak ga terawat ga bisa digunain",
        "bak sampah di taman overload ga pernah dikosongkan petugas",
        "cctv di perumahan banyak yg rusak ga bisa merekam",
        "pohon tua rawan tumbang ga pernah dipangkas dinas",
        "saluran irigasi mampet sawah petani gagal dapet air",
        "penerangan di gang sempit ga ada gelap dan rawan banget",
        "lift gedung pemerintah sering rusak ga nyaman buat lansia",
        "pengelolaan pasar buruk bgt bau dan ga higienis sama sekali",
        "papan petunjuk jalan rusak menyesatkan pengguna jalan",
        "tps terbuka menimbulkan bau busuk parah bikin warga ga nyaman",
        "rambu lalu lintas ilang ga ada penggantinya berbahaya bgt",
        "warung pinggir jalan blokir trotoar pejalan kaki terpaksa di jalan",
        "jalur pejalan kaki diokupasi pkl pejalan kaki terpaksa di jalan",
        "pengelolaan parkir semrawut banget merugikan warga sekitar",
        "fasilitas mck umum kotor ga pernah dibersihkan petugas",
        "jalan setapak rusak parah ga bisa dilalui motor sama sekali",
        "petugas kebersihan ga pernah datang warga harus bersihin sendiri",
        "got mampet lagi ga ada yg mau bersihin padahal udah dilaporin",
        "sampah menumpuk di pinggir jalan mengganggu warga sekitar",
        "rel pengaman jembatan rusak berbahaya buat pejalan kaki",
        "sudah banyak korban kecelakaan di sini tapi ga ada perbaikan",
        "petugas pajak ga ramah dan prosesnya ribet banget",
        "pelayanan stnk di samsat lama banget ga efisien sama sekali",
        "sistem drainase sangat buruk perlu total dirombak segera",
        "pelayanan di rsud buruk banget pasien ga dilayani dgn baik",
        "fasilitas toilet umum di pasar kotor ga layak buat dipakai",
        "kerusakan infrastruktur makin parah ga ada anggaran perbaikan",
        "jalan rusak bikin kendaraan warga cepat rusak dan rugi",
        "lampu penerangan jalan rusak wilayah jadi rawan kejahatan",
        "air bersih sering mati mendadak tanpa pemberitahuan dulu",
        "petugas tidak disiplin sering tidak ada di pos pelayanan",
        "kondisi drainase memprihatinkan selalu banjir saat hujan deras",
        "jembatan gantung sudah tidak aman perlu segera diperbaiki",
        "pelayanan di kantor kelurahan sangat tidak memuaskan",
        "masalah ini sudah bertahun-tahun tapi tidak pernah ditangani",
        "kondisi selokan sangat kotor dan tersumbat perlu dibersihkan",
        "pelayanan tidak ramah petugas jutek tidak mau melayani",
        "taman kota tidak terawat menjadi tempat pembuangan sampah liar",
        "kondisi sanitasi di wilayah ini sangat memprihatinkan",
        "jalan berdebu sangat mengganggu kesehatan warga sekitar",
        "lampu lalu lintas mati menyebabkan kemacetan dan kekacauan",
        "pelayanan perizinan sangat lambat merugikan pengusaha kecil",
        "pengelolaan parkir di pusat kota kacau dan tidak teratur",
        "jalan berlubang parah banget udah banyak yang kecelakaan",
        "kabel listrik menjuntai rendah hampir mengenai kepala warga",
        "banjir makin parah hampir masuk ke dalam rumah warga",
        "pohon mau tumbang angin kencang warga khawatir banget",
        "ada retakan di dinding rumah susun yang makin melebar",
        # ── Generated keluhan realistis ──────────────────────────
        *GENERATED_KELUHAN,
        # ── Generated sarkasme (intent = keluhan) ────────────────
        *GENERATED_SARCASM,
        # ── Hard cases keluhan/ambigu ─────────────────────────────
        *_HARD_CASES_INTENT,

        # ==========================================================
        # PERMINTAAN (79 static + 271 generated)
        # Total = 350
        # Total ≈ 204
        # ==========================================================
        "Mohon dipasang lampu jalan baru di kawasan gelap ini",
        "Minta dibuatkan zebra cross di depan sekolah dasar",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Tolong sediakan tempat sampah yang cukup di taman kota",
        "Mohon bangun posyandu baru di kelurahan kami segera",
        "Minta perbaikan jalan yang berlubang parah di RT kami",
        "Harap pasang rambu lalu lintas di persimpangan berbahaya",
        "Tolong tambahkan toilet umum yang bersih di area pasar",
        "Mohon sediakan bangku taman yang lebih banyak untuk warga",
        "Minta dibangun taman bermain yang layak untuk anak-anak",
        "Harap segera pasang CCTV di area parkir yang rawan maling",
        "Tolong buatkan jalur sepeda yang aman di jalan utama",
        "Mohon tambahkan petugas keamanan di area ini malam hari",
        "Minta diadakan angkutan umum ke daerah terpencil kami",
        "Harap sediakan fasilitas difabel di kantor kelurahan kami",
        "Mohon tambahkan loket pelayanan agar warga tidak antre lama",
        "Tolong tambah jam operasional pelayanan hingga sore hari",
        "Minta disediakan pelayanan online untuk urus administrasi",
        "Kami membutuhkan poliklinik tambahan di wilayah padat ini",
        "Warga berharap ada program vaksinasi di kelurahan kami",
        "Perlu ada penambahan fasilitas kesehatan yang layak di sini",
        "Kami ingin ada bank sampah di setiap RT wilayah kami",
        "Berharap ada lapangan olahraga untuk warga di sini",
        "Tolong pasang portal jalan cegah kendaraan berat masuk",
        "Mohon tambahkan lampu sorot di area yang sering jadi TKP",
        "Minta dilakukan pengerukan saluran drainase yang sudah penuh",
        "Harap ada program penanaman pohon di sepanjang jalan ini",
        "Kami sangat membutuhkan ruang terbuka hijau di wilayah kami",
        "Tolong lakukan fogging nyamuk di wilayah kami yang rawan DBD",
        "Diharapkan ada program bersih-bersih lingkungan setiap minggu",
        "Mohon segera perbaiki jembatan yang hampir roboh itu",
        "Harap ditambahkan fasilitas olahraga di taman kota kami",
        "Minta dibuatkan jalur pedestrian yang nyaman di jalan utama",
        "Tolong segera perbaiki pipa PDAM yang bocor di jalan ini",
        "Mohon sediakan layanan jemput bola untuk warga lansia",
        "Harap ada pengamanan lebih ketat di kawasan sekolah",
        "Minta dibuatkan shelter untuk pejalan kaki di jalan protokol",
        "Tolong tambahkan armada sampah untuk wilayah kami",
        "Mohon perbaiki drainase yang jebol menyebabkan banjir",
        "Harap sediakan ruang laktasi di kantor pemerintahan",
        "Minta dibangun jembatan penghubung dua desa yang terputus",
        "Tolong rehab sekolah dasar yang atapnya sudah bocor",
        "Mohon adakan pelatihan kewirausahaan untuk warga kurang mampu",
        "Harap tambahkan tempat cuci tangan di area publik",
        "Minta pengaspalan jalan kampung yang masih tanah berbatu",
        "Tolong sediakan layanan ambulans desa untuk kedaruratan",
        "Mohon bangun TPU baru karena yang ada sudah penuh",
        "Harap ada sistem peringatan dini banjir di wilayah kami",
        "Minta pemasangan palang kereta api di perlintasan berbahaya",
        "Tolong sediakan bak sampah besar di setiap RT kelurahan",
        "Mohon tambah unit pemadam kebakaran di wilayah padat ini",
        "Harap dibuatkan jalan tembus antar kampung untuk kemudahan",
        "Minta normalisasi sungai yang sudah sangat dangkal ini",
        "Tolong sediakan sumur bor untuk warga yang kekurangan air",
        "Mohon pasang pagar pengaman di tepi jalan yang berbahaya",
        "Harap ada petugas kebersihan yang rutin di kawasan wisata",
        "Minta pembangunan pos keamanan di pintu masuk perumahan",
        "Tolong sediakan fasilitas parkir yang memadai di pasar",
        "Mohon rehab balai desa yang sudah tidak layak digunakan",
        "Harap tambahkan rute angkutan umum ke daerah pinggiran",
        "Minta dibuatkan pedestrian bridge di jalan yang ramai ini",
        "Tolong sediakan dokter jaga 24 jam di puskesmas kami",
        "Mohon bangun drainase baru yang lebih besar di kawasan ini",
        "Harap ada program bedah rumah untuk warga tidak mampu",
        "Minta pemasangan lampu tenaga surya di jalan desa",
        "mohon dong segera pasang lampu jalan di kawasan gelap ini",
        "minta tolong buatin zebra cross di depan sekolah kami",
        "tlg tambahin armada bus rute ke perumahan kami dong",
        "harap sediain tempat sampah lebih banyak di taman ini",
        "harap pasang rambu lalu lintas di persimpangan ini dong",
        "minta dibuatin zebra cross di depan sekolah dasar",
        "mohon dipasang lampu jalan baru di kawasan ini dong",
        "tlg tambahin toilet umum di area pasar tradisional",
        "harap sediain fasilitas difabel di kantor kelurahan",
        "kami butuh posyandu baru di kelurahan kami dong",
        "tlg bangun taman bermain buat anak di kelurahan ini",
        "mohon tambahin petugas keamanan di area ini malam hari",
        "kami pengen ada perbaikan fasilitas di wilayah ini",
        "warga berharap ada tindakan nyata dari pemda dong",
        *GENERATED_PERMINTAAN,

        # ==========================================================
        # SARAN (56 static + 294 generated)
        # Total = 350
        # Total ≈ 149
        # ==========================================================
        "Sebaiknya ada jadwal rutin pemeliharaan jalan setiap bulan",
        "Alangkah baiknya ada sistem pengaduan online yang mudah diakses",
        "Disarankan agar petugas kebersihan menambah frekuensi kunjungan",
        "Saran agar jam pelayanan kantor diperpanjang sampai sore",
        "Ada baiknya dibuat jalur khusus sepeda di jalan protokol kota",
        "Sebaiknya pemerintah menambah armada pengangkut sampah baru",
        "Perlu dibenahi sistem antrian di kantor pelayanan publik",
        "Lebih baik bila ada aplikasi untuk melapor kerusakan fasilitas",
        "Usul agar lampu jalan diganti dengan yang hemat energi LED",
        "Kiranya perlu diadakan bank sampah di setiap kelurahan",
        "Seharusnya ada pos kesehatan di setiap RT yang padat penduduk",
        "Saran untuk meningkatkan kualitas air PDAM yang sering keruh",
        "Lebih baik kalau ada program peremajaan trotoar kota secara berkala",
        "Perlu ditingkatkan kualitas pelayanan di puskesmas kecamatan",
        "Bisa dioptimalkan penggunaan lahan kosong untuk RTH baru",
        "Sebaiknya ada sistem monitoring kondisi jalan secara real time",
        "Alangkah baiknya petugas kelurahan melakukan kunjungan rutin",
        "Disarankan agar dibuat sistem informasi pengaduan terpadu",
        "Usul agar pasar tradisional direvitalisasi secara menyeluruh",
        "Ada baiknya diadakan program edukasi pemilahan sampah",
        "Sebaiknya pemerintah lebih aktif mensosialisasikan program",
        "Ada baiknya ada pemutihan pajak kendaraan untuk warga",
        "Saran agar kantor pelayanan terpadu segera dibuka di daerah",
        "Lebih baik bila ada aplikasi pelacak jadwal angkutan umum",
        "Perlu ada kajian ulang tata ruang kota yang lebih komprehensif",
        "Disarankan agar masyarakat dilibatkan dalam perencanaan anggaran",
        "Sebaiknya ada program edukasi tentang pengolahan sampah",
        "Ada baiknya dibuat sistem informasi ketersediaan layanan publik",
        "Saran untuk meningkatkan kualitas pendidikan di sekolah negeri",
        "Lebih baik bila pelayanan kesehatan gratis diperluas cakupannya",
        "Perlu ada evaluasi program pemberdayaan masyarakat secara rutin",
        "Disarankan agar dibuat peta potensi bencana yang mudah diakses",
        "sebaiknya ada jadwal rutin pemeliharaan jalan tiap bulan",
        "alangkah baiknya ada sistem pengaduan online yg mudah",
        "disaranin biar petugas kebersihan makin sering ke sini",
        "saran biar jam pelayanan kantor diperpanjangin sampe sore",
        "ada baiknya dibikin jalur khusus sepeda di jalan utama",
        "sebaiknya pemerintah tambahin armada pengangkut sampah",
        "perlu dibenahi sistem antrian di kantor pelayanan publik",
        "lebih baik kalau ada aplikasi buat lapor kerusakan fasilitas",
        "usul biar lampu jalan diganti yang hemat energi led",
        "kayaknya perlu ada bank sampah di tiap kelurahan deh",
        "seharusnya ada pos kesehatan di tiap rt yang padat penduduk",
        "saran buat ningkatin kualitas air pdam yang sering keruh",
        "lebih baik ada program peremajaan trotoar kota secara berkala",
        "perlu ditingkatkan kualitas pelayanan di puskesmas kecamatan",
        "bisa dioptimalkan penggunaan lahan kosong buat rth baru",
        "sampah numpuk terus, mestinya ada jadwal pengangkutan yang jelas",
        "pelayanannya lambat, mungkin perlu tambah pegawai biar cepet",
        "got mampet mulu, kayaknya perlu dikeruk rutin setiap bulan",
        "lampu jalan mati, sebaiknya diganti yang LED biar tahan lama",
        "drainase buruk bikin banjir terus, perlu diperbaiki sistemnya",
        "toilet umum jorok, harusnya ada petugas jaga dan bersihin",
        "angkot jarang lewat, mestinya ditambah armadanya dong",
        "kondisi puskesmas memprihatinkan, perlu renovasi segera",
        "trotoar rusak dan sempit, sebaiknya diperlebar buat pejalan kaki",
        *GENERATED_SARAN,

        # ==========================================================
        # APRESIASI (53 asli + 297 generated)
        # Total = 350
        # ==========================================================
        # Total ≈ 181
        # ==========================================================
        "Terima kasih jalan sudah diperbaiki dengan cepat dan baik",
        "Pelayanan sangat baik cepat dan memuaskan sekali bagi warga",
        "Petugas ramah dan sangat membantu warga dengan sepenuh hati",
        "Terima kasih taman kota sudah bersih dan terawat sangat indah",
        "Senang lampu jalan sudah dipasang wilayah jadi terang sekali",
        "Pelayanan administrasi sangat memuaskan dan sangat efisien",
        "Bagus sekali kinerja petugas kebersihan taman kota kita",
        "Apresiasi kepada petugas yang responsif dan sangat profesional",
        "Luar biasa program pemerintah sangat membantu warga yang butuh",
        "Puskesmas pelayanannya meningkat pesat terima kasih banyak",
        "Petugas pemadam sangat cepat dan profesional hebat sekali",
        "Bangga dengan tim yang bekerja keras melayani masyarakat",
        "Salut respons pemerintah yang cepat menangani keluhan warga",
        "Senang taman bermain sudah diperbaiki anak-anak bisa bermain",
        "Pelayanan di desa sangat dipermudah warga sangat puas sekali",
        "Pelayanan petugas bagus ramah warga merasa senang dan puas",
        "Sangat puas dengan pelayanan kantor yang cepat dan baik",
        "Pelayanan sangat baik didesa warga merasa sangat terbantu",
        "Warga merasa puas dengan pelayanan yang diberikan selama ini",
        "Pelayanan pemerintah daerah semakin membaik dari waktu ke waktu",
        "Kinerja para petugas patut mendapat acungan jempol dari warga",
        "Responsivitas pemerintah dalam menangani masalah sangat bagus",
        "Kondisi lingkungan semakin membaik berkat kerja keras petugas",
        "Sangat memuaskan hasil perbaikan yang dilakukan pemerintah",
        "Program kerja bakti sangat membantu warga membersihkan lingkungan",
        "Petugas sigap dan profesional dalam menjalankan tugas harian",
        "Semua petugas ramah dan sangat membantu warga dengan baik",
        "Kebijakan pemerintah kali ini tepat sasaran dan bermanfaat",
        "Fasilitas sudah diperbaiki warga sangat senang berterima kasih",
        "Lingkungan bersih indah berkat kerja keras petugas kebersihan",
        "Alhamdulillah jalan sudah diperbaiki tidak berlubang lagi",
        "Senang sekali pelayanan cepat tidak perlu menunggu lama",
        "Terima kasih petugas datang tepat waktu dan bekerja dengan baik",
        "Pemerintah sangat responsif kali ini masalah langsung ditangani",
        "Pelayanan jauh meningkat dari sebelumnya warga sangat senang",
        "Terima kasih drainase sudah dibersihkan banjir berkurang",
        "Petugas bekerja dengan sangat profesional dan penuh semangat",
        "makasih bgt jalan udah diperbaiki cepet dan bagus bgt",
        "pelayanan bagus bgt cepet dan memuaskan bagi warga",
        "petugasnya ramah bgt dan sangat bantu warga dgn baik",
        "makasih taman kota udah bersih dan terawat sangat indah",
        "seneng bgt lampu jalan udah dipasang wilayah jadi terang",
        "pelayanan administrasi sangat memuaskan dan efisien bgt",
        "bagus bgt kinerja petugas kebersihan taman kota kita",
        "apresiasi buat petugas yang responsif dan sangat profesional",
        "puskesmas pelayanannya meningkat pesat makasih banyak ya",
        "petugas pemadam cepet bgt dan profesional hebat bgt deh",
        "bangga sama tim yang kerja keras buat warga",
        "salut respons pemerintah yang cepet nanganin keluhan warga",
        "seneng taman bermain udah diperbaiki anak2 bisa main",
        "pelayanan di desa sangat dipermudah warga puas bgt",
        "sangat puas sama pelayanan kantor yang cepet dan bagus",
        "warga ngerasa puas sama pelayanan yg dikasih",
        *GENERATED_APRESIASI,

        # ==========================================================
        # DARURAT (30 static + 320 generated)
        # Total = 350
        # Total ≈ 155
        # ==========================================================
        "Kebakaran besar terjadi di pemukiman padat butuh bantuan segera",
        "Banjir bandang menghantam desa kami evakuasi segera diperlukan",
        "Tanah longsor menutup jalan warga terjebak butuh pertolongan",
        "Gempa kuat mengguncang wilayah banyak bangunan ambruk parah",
        "Warga keracunan makanan massal kondisi darurat tolong segera",
        "Terjadi kebocoran gas besar di kawasan industri situasi kritis",
        "Listrik konslet menyebabkan kebakaran di rumah warga padat",
        "Jembatan putus diterjang banjir warga tidak bisa menyeberang",
        "Tsunami peringatan dini berbunyi warga perlu dievakuasi segera",
        "Korban jiwa dalam kecelakaan parah butuh ambulans darurat",
        "Ada korban luka parah di kecelakaan lalu lintas ini",
        "Warga tidak sadarkan diri butuh pertolongan medis segera",
        "Nyawa warga terancam banjir naik cepat situasi gawat darurat",
        "Erupsi gunung mulai terjadi abu tebal warga perlu dievakuasi",
        "Angin puting beliung merusak rumah warga perlu bantuan segera",
        "Situasi kritis kebakaran hutan mendekati permukiman warga",
        "Kondisi darurat banjir mengepung rumah susun warga terjebak",
        "Pohon besar tumbang menimpa rumah warga butuh tim penyelamat",
        "Dinding sekolah ambruk saat jam pelajaran ada korban parah",
        "Tangki BBM bocor di jalan raya situasi sangat berbahaya",
        "Kebakaran pasar besar api sudah membesar butuh bantuan cepat",
        "Banjir bandang dari hulu menerjang kampung warga terjebak",
        "Ada korban tenggelam di sungai butuh tim penyelamat segera",
        "Insiden serius terjadi di pabrik bahan kimia berbahaya",
        "Kondisi darurat gempa susulan terus terjadi warga panik",
        "ada kebakaran di ruko sebelah api udah gede tolong cepet",
        "darurat banjir udah masuk rumah tolong evakuasi segera ya",
        "ada orang keracunan massal di hajatan butuh ambulans sekarang",
        "tiang listrik roboh kena kabel hidup sangat berbahaya tolong",
        "ada longsor di bukit belakang kampung butuh tim penyelamat",
        *GENERATED_DARURAT,

    ],
    "labels": (
        ["keluhan"]    * 350 +
        ["permintaan"] * 350 +
        ["saran"]      * 350 +
        ["apresiasi"]  * 350 +
        ["darurat"]    * 350
    ),
}


# ================================================================
# SENTIMENT DATA
# ================================================================

SENTIMENT_DATA = {
    "texts": [

        # ==========================================================
        # NEGATIF (115 asli + 20 sarcasm generated + 15 hard)
        # Total ≈ 150
        # ==========================================================
        "Jalan rusak parah di depan sekolah sudah lama tidak diperbaiki",
        "Lampu jalan mati sudah seminggu sangat berbahaya sekali",
        "Sampah menumpuk tidak diangkut berhari-hari baunya menyengat",
        "Air PDAM keruh tidak layak diminum sangat mengecewakan warga",
        "Pelayanan kantor sangat lambat dan tidak memuaskan sama sekali",
        "Taman kota kotor jorok dan tidak terawat sama sekali",
        "Drainase tersumbat banjir setiap kali hujan turun sangat parah",
        "Fasilitas kesehatan rusak dibiarkan tidak diperbaiki pemerintah",
        "Trotoar berlubang parah membahayakan pejalan kaki setiap hari",
        "Pelayanan buruk petugas tidak ramah sangat mengecewakan sekali",
        "Saluran air mampet menimbulkan bau busuk tidak tertahankan",
        "Jembatan retak berbahaya dibiarkan tanpa perbaikan apapun",
        "Halte bus rusak bocor tidak ada perbaikan sama sekali",
        "Kabel listrik menjuntai rendah sangat membahayakan warga",
        "Kebakaran besar terjadi dan tidak ada bantuan yang datang",
        "Banjir parah merusak rumah warga sangat memprihatinkan sekali",
        "Tanah longsor membahayakan warga situasi sangat mengkhawatirkan",
        "Warga sudah capek melaporkan tapi tidak ada respons sama sekali",
        "Sudah lelah berkali-kali lapor tapi masalah tidak kunjung beres",
        "Kondisi ini sangat memprihatinkan dan tidak ada yang peduli",
        "Sangat disayangkan pemerintah tidak tanggap terhadap keluhan",
        "Kondisi jalan semakin parah makin buruk setiap harinya",
        "Pelayanan semakin buruk tidak ada perbaikan sama sekali",
        "Lingkungan semakin kotor tidak terawat tidak layak huni",
        "Tidak ada tindakan apapun dari pemerintah sangat mengecewakan",
        "Fasilitas tidak layak dan sangat membahayakan keselamatan warga",
        "Air tidak mengalir sudah tiga hari warga sangat kesulitan",
        "Pelayanan tidak profesional dan sangat tidak memuaskan sekali",
        "Lampu tidak menyala gelap berbahaya sudah berminggu-minggu",
        "jln rusak parah bgt udah lama ga diperbaiki oleh dinas",
        "lampu jalan mati udh berminggu2 gelap bgt berbahaya",
        "sampah numpuk ga diangkut berhari2 baunya menyengat bgt",
        "air pdam keruh bgt ga layak diminum warga sangat kecewa",
        "pelayanan kantor lambat bgt ga memuaskan sama sekali",
        "taman kota jorok bgt ga terawat sama sekali",
        "got tersumbat banjir tiap ujan sangat parah bgt",
        "fasilitas kesehatan rusak dibiarkan ga diperbaiki pemerintah",
        "pelayanan buruk bgt petugas ga ramah sangat mengecewakan",
        "air mampet bau busuk bgt ga tertahankan",
        "jembatan retak berbahaya dibiarkan tanpa perbaikan apapun",
        "kebakaran besar terjadi ga ada bantuan yg datang sama sekali",
        "banjir parah bgt ngerusak rumah warga sangat memprihatinkan",
        "warga udah capek lapor tapi ga ada respons sama sekali",
        "udah lelah berkali2 lapor masalah ga kunjung beres juga",
        "kondisi ini sangat memprihatinkan ga ada yg peduli sama sekali",
        "sangat disayangkan pemerintah ga tanggap terhadap keluhan warga",
        "kondisi jalan makin parah buruk bgt setiap harinya",
        "pelayanan makin buruk bgt ga ada perbaikan sama sekali",
        "lingkungan makin kotor bgt ga terawat ga layak huni",
        "kondisi pasar sangat memprihatinkan kotor bgt ga layak",
        "ga ada tindakan apapun dari pemerintah sangat mengecewakan",
        "air ga ngalir udah 3 hari warga sangat kesulitan bgt",
        "lampu ga nyala gelap bgt berbahaya udah berminggu2",
        "masalah ini makin parah bgt ga ada yg bertanggung jawab",
        "infrastruktur buruk bgt warga udah frustrasi sejak lama",
        "pelayanan sangat ga memuaskan warga kecewa besar bgt",
        "udah dilaporin berkali2 ga ada tindakan apapun bgt",
        "masalah ini terus berulang ga ada solusi permanen sama sekali",
        "lingkungan kotor bgt ga sehat membahayakan warga",
        "kondisi jalan membahayakan bgt banyak yg udah kecelakaan",
        # Sarkasme sebagai sentimen negatif
        "bagus sekali pelayanannya sampai antre 3 jam baru dilayani",
        "keren banget jalannya udah berlubang parah tapi ga diperbaiki juga",
        "luar biasa petugas kita, datang terlambat dan kerjanya asal",
        "mantap banget sistem drainasenya, banjir tiap kali hujan",
        "hebat memang pengelolaan sampahnya, numpuk terus tiap hari",
        # Generated sarcasm sebagai negatif
        *GENERATED_SARC_NEGATIF_SENT,
        # Hard cases sentimen
        *_HARD_CASES_SENTIMENT,
        # Generator negatif
        *GENERATED_NEGATIF,

        # ==========================================================
        # POSITIF (104 asli + 196 generated)
        # Total = 300
        # ==========================================================
        "Terima kasih jalan sudah diperbaiki dengan cepat dan baik",
        "Pelayanan sangat baik cepat dan memuaskan sekali bagi warga",
        "Petugas ramah dan sangat membantu warga dengan sepenuh hati",
        "Terima kasih taman kota sudah bersih dan terawat sangat indah",
        "Senang lampu jalan sudah dipasang wilayah jadi terang sekali",
        "Pelayanan administrasi sangat memuaskan dan sangat efisien",
        "Bagus sekali kinerja petugas kebersihan taman kota kita",
        "Apresiasi kepada petugas yang responsif dan sangat profesional",
        "Luar biasa program pemerintah sangat membantu warga yang butuh",
        "Puskesmas pelayanannya meningkat pesat terima kasih banyak",
        "Petugas pemadam sangat cepat dan profesional hebat sekali",
        "Bangga dengan tim yang bekerja keras melayani masyarakat",
        "Salut respons pemerintah yang cepat menangani keluhan warga",
        "Senang taman bermain sudah diperbaiki anak-anak bisa bermain",
        "Pelayanan di desa sangat dipermudah warga sangat puas sekali",
        "Pelayanan petugas bagus ramah warga merasa senang dan puas",
        "Sangat puas dengan pelayanan kantor yang cepat dan baik",
        "Warga merasa puas dengan pelayanan yang diberikan selama ini",
        "Pelayanan pemerintah daerah semakin membaik dari waktu ke waktu",
        "Kinerja para petugas patut mendapat acungan jempol dari warga",
        "Responsivitas pemerintah dalam menangani masalah sangat bagus",
        "Kondisi lingkungan semakin membaik berkat kerja keras petugas",
        "Sangat memuaskan hasil perbaikan yang dilakukan pemerintah",
        "Program kerja bakti sangat membantu warga membersihkan lingkungan",
        "Alhamdulillah jalan sudah diperbaiki tidak berlubang lagi",
        "Senang sekali pelayanan cepat tidak perlu menunggu lama",
        "Terima kasih petugas datang tepat waktu dan bekerja dengan baik",
        "Pemerintah sangat responsif kali ini masalah langsung ditangani",
        "Pelayanan jauh meningkat dari sebelumnya warga sangat senang",
        "Terima kasih drainase sudah dibersihkan banjir berkurang",
        "Petugas bekerja dengan sangat profesional dan penuh semangat",
        "Senang melihat kondisi lingkungan yang semakin baik dan bersih",
        "Alhamdulillah masalah air bersih sudah teratasi dengan baik",
        "Terima kasih program beasiswa sangat membantu warga kurang mampu",
        "Pelayanan semakin baik petugas tidak lagi mempersulit warga",
        "Terima kasih pemerintah sudah peduli dengan kondisi lingkungan",
        "Sangat puas dengan kinerja petugas yang bekerja keras untuk kita",
        "Kondisi jalan sudah sangat baik nyaman dilalui pengendara",
        "Alhamdulillah program bantuan sosial tepat sasaran bermanfaat",
        "Terima kasih petugas kesehatan aktif melayani warga di lapangan",
        "Senang melihat pembangunan infrastruktur yang berjalan dengan baik",
        "Pelayanan di kantor sangat memuaskan tidak ada yang dipersulit",
        "Bangga melihat kota semakin bersih dan tertata dengan rapi",
        "Terima kasih semua petugas yang bekerja keras untuk masyarakat",
        "Kondisi fasilitas publik sangat baik terawat dan nyaman digunakan",
        "Alhamdulillah semua masalah warga sudah ditangani dengan baik",
        "Terima kasih pemerintah yang tanggap dan peduli kepada warga",
        "Pelayanan sangat cepat dan ramah warga tidak kecewa sama sekali",
        "Senang melihat lingkungan yang semakin bersih dan sehat",
        "Terima kasih program vaksinasi berjalan lancar dan teratur",
        "Petugas sangat membantu dan profesional dalam bertugas",
        "Kondisi jalan sudah diperbaiki warga bisa berkendara dengan aman",
        "Alhamdulillah banjir sudah teratasi berkat normalisasi drainase",
        "makasih bgt jalan udah diperbaiki cepet dan bagus bgt",
        "pelayanan bagus bgt cepet dan memuaskan bagi warga",
        "petugasnya ramah bgt dan sangat bantu warga dgn baik",
        "makasih taman kota udah bersih dan terawat sangat indah",
        "seneng bgt lampu jalan udah dipasang wilayah jadi terang",
        "pelayanan administrasi sangat memuaskan dan efisien bgt",
        "bagus bgt kinerja petugas kebersihan taman kota kita",
        "apresiasi buat petugas yg responsif dan sangat profesional",
        "puskesmas pelayanannya meningkat pesat makasih banyak ya",
        "petugas pemadam cepet bgt dan profesional hebat bgt deh",
        "bangga sama tim yang kerja keras buat warga",
        "salut respons pemerintah yang cepet nanganin keluhan warga",
        "seneng taman bermain udah diperbaiki anak2 bisa main",
        "pelayanan di desa sangat dipermudah warga puas bgt",
        "sangat puas sama pelayanan kantor yang cepet dan bagus",
        "alhamdulillah jalan udah diperbaiki ga berlubang lagi",
        "makasih petugas dateng tepat waktu dan kerja bagus bgt",
        "pemerintah responsif bgt kali ini masalah langsung ditangani",
        "pelayanan jauh meningkat dari sebelumnya warga senang bgt",
        "makasih drainase udah dibersihkan banjir berkurang bgt",
        "petugas kerja sangat profesional dan penuh semangat bgt",
        "seneng lihat kondisi lingkungan makin baik dan bersih",
        "alhamdulillah masalah air bersih udah teratasi dgn baik",
        "makasih program beasiswa sangat bantu warga kurang mampu",
        "pelayanan makin baik petugas ga lagi menyulitin warga",
        "makasih pemerintah udah peduli sama kondisi lingkungan",
        "puas bgt sama kinerja petugas yg kerja keras buat kita",
        "kondisi jalan udah bagus bgt nyaman dilalui pengendara",
        "alhamdulillah program bansos tepat sasaran dan bermanfaat",
        "makasih petugas kesehatan aktif layani warga di lapangan",
        "seneng lihat pembangunan infrastruktur berjalan dengan baik",
        "pelayanan di kantor puas bgt ga ada yg disulitin",
        "bangga lihat kota makin bersih dan tertata dengan rapi",
        "alhamdulillah semua masalah warga udah ditangani dgn baik",
        "makasih pemerintah yg tanggap dan peduli kepada warga",
        "pelayanan cepet bgt dan ramah warga ga kecewa sama sekali",
        "seneng lihat lingkungan makin bersih dan sehat bgt",
        "makasih program vaksinasi berjalan lancar dan teratur",
        "petugas sangat bantu dan profesional dalam bertugas",
        "kondisi jalan udah diperbaiki warga bisa berkendara aman",
        "alhamdulillah banjir udah teratasi berkat normalisasi drainase",
        "mantul respon petugasnya, langsung dateng pas dilaporin 👍",
        "keren bgt aplikasinya, laporan langsung ditindaklanjuti",
        "josss pelayanannya, ga pake lama langsung beres",
        "akhirnya diperbaiki juga, makasih banyak min",
        "nggak nyangka secepet ini ditanganinya, salut deh",
        "top markotop petugasnya, responsive banget sama warga",
        "alhamdulillah akhirnya beres, sempet khawatir ga ditangani",
        "pelayanannya oke bgt, ramah dan cepet, puas deh",
        "makasih bgt udah mau dengerin keluhan warga, responsif",
        "syukurlah drainase udah dibenerin, ga banjir lagi",
        *GENERATED_POSITIF,

        # ==========================================================
        # NETRAL (119 asli + 181 generated)
        # Total = 300
        # ==========================================================
        "Informasi tentang jadwal pengangkutan sampah di wilayah ini",
        "Prosedur pengajuan surat keterangan domisili yang diperlukan",
        "Jadwal operasional pelayanan kantor kelurahan ini seperti apa",
        "Cara mendaftar program bantuan sosial untuk warga kurang mampu",
        "Syarat pembuatan KTP elektronik di kantor kecamatan",
        "Jadwal posyandu bulan ini dan lokasi pelaksanaannya",
        "Prosedur pelaporan kehilangan dokumen penting warga",
        "Persyaratan izin usaha mikro kecil menengah di daerah",
        "Cara mengakses layanan kesehatan gratis untuk warga",
        "Prosedur perpanjangan SIM di Samsat terdekat",
        "Biaya pembuatan akta kelahiran dan persyaratannya",
        "Jadwal pemadaman listrik bergilir di wilayah ini",
        "Informasi program bantuan perbaikan rumah tidak layak huni",
        "Syarat pendaftaran program beasiswa dari pemerintah daerah",
        "Cara mengurus kartu keluarga setelah pindah domisili",
        "Prosedur pemasangan sambungan listrik baru di rumah",
        "Lokasi pengambilan bantuan sembako dari pemerintah",
        "Mekanisme pengaduan masalah lingkungan hidup ke dinas",
        "Jadwal dan lokasi vaksinasi booster di wilayah kami",
        "Cara mendaftarkan anak ke sekolah negeri",
        "Informasi jadwal operasional kantor pelayanan publik",
        "Berapa lama proses pembuatan paspor sekarang",
        "Apakah ada layanan antar dokumen untuk warga lansia",
        "Prosedur pengajuan izin keramaian untuk acara",
        "Di mana bisa mendapat informasi tentang subsidi listrik",
        "Bagaimana cara mengakses layanan perpustakaan online",
        "Prosedur mendapatkan kartu disabilitas",
        "Info tentang program penanggulangan kemiskinan di daerah",
        "kapan sih jadwal angkut sampah di daerah sini",
        "info jam pelayanan kantor kelurahan gimana caranya",
        "prosedur ngurus ktp di kantor kecamatan gimana ya",
        "jadwal posyandu bulan ini kapan dan di mana lokasinya",
        "cara daftar bansos gimana prosedurnya ya",
        "syarat bikin surat keterangan domisili apa aja yg perlu",
        "jadwal pemadaman listrik bergilir di wilayah ini kapan",
        "cara lapor kehilangan dokumen harus ke kantor mana ya",
        "prosedur perpanjangan sim di samsat terdekat gimana",
        "berapa biaya bikin akta kelahiran dan prosedurnya",
        "saya ingin tau berapa lama proses pembuatan paspor sekarang",
        "apakah ada layanan antar dokumen ke rumah untuk lansia",
        "gimana prosedur pengajuan izin keramaian untuk acara",
        "saya perlu info tentang peraturan tata bangunan di daerah",
        "di mana bisa mendapatkan informasi tentang subsidi listrik",
        "gimana cara daftarin anak ke sekolah negeri favorit",
        "prosedur lapor pencemaran lingkungan kepada dinas terkait",
        "info persyaratan buka usaha kuliner di area publik gimana",
        "apakah ada bantuan untuk renovasi rumah tidak layak huni",
        "kapan ada sosialisasi peraturan baru tata kota ya",
        "gimana cara akses layanan perpustakaan daerah secara online",
        "saya ingin tau prosedur dapet kartu disabilitas gimana",
        "info tentang program penanggulangan kemiskinan di daerah",
        "Sebaiknya ada jadwal rutin pemeliharaan jalan setiap bulan",
        "Alangkah baiknya ada sistem pengaduan online yang mudah diakses",
        "Disarankan agar petugas kebersihan menambah frekuensi kunjungan",
        "Saran agar jam pelayanan kantor diperpanjang sampai sore",
        "Ada baiknya dibuat jalur khusus sepeda di jalan protokol kota",
        "Perlu dibenahi sistem antrian di kantor pelayanan publik",
        "Lebih baik bila ada aplikasi untuk melapor kerusakan fasilitas",
        "Usul agar lampu jalan diganti dengan yang hemat energi LED",
        "Sebaiknya ada pos kesehatan di setiap RT yang padat penduduk",
        "Lebih baik kalau ada program peremajaan trotoar kota",
        "Mohon dipasang lampu jalan baru di kawasan gelap ini",
        "Minta dibuatkan zebra cross di depan sekolah dasar",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Tolong sediakan tempat sampah yang cukup di taman kota",
        "Mohon bangun posyandu baru di kelurahan kami segera",
        "Minta perbaikan jalan yang berlubang parah di RT kami",
        "Harap pasang rambu lalu lintas di persimpangan berbahaya",
        "Tolong tambahkan toilet umum yang bersih di area pasar",
        "Mohon sediakan bangku taman yang lebih banyak untuk warga",
        "Minta dibangun taman bermain yang layak untuk anak-anak",
        "jalan di sini memang perlu perbaikan sudah cukup lama",
        "pelayanan masih bisa ditingkatkan untuk hasil yang lebih baik",
        "fasilitas perlu dibenahi agar lebih layak digunakan warga",
        "kondisi drainase memerlukan perhatian khusus dari dinas terkait",
        "pengelolaan sampah perlu diperbaiki agar lebih teratur",
        "program ini sudah berjalan dan warga mulai merasakan manfaatnya",
        "petugas sudah berupaya memberikan pelayanan yang baik",
        "kondisi lingkungan terus mengalami perkembangan ke arah lebih baik",
        "fasilitas yang baru dipasang sudah bisa digunakan warga",
        "pelayanan berjalan normal sesuai jam operasional yang berlaku",
        "jalan di depan rumah belum diperbaiki sudah beberapa bulan",
        "petugas tidak datang sesuai jadwal yang sudah ditentukan",
        "lampu jalan di gang ini tidak menyala lagi sejak minggu lalu",
        "air PDAM tidak mengalir sudah dua hari ini",
        "sampah belum diangkut padahal jadwalnya kemarin",
        "antrean di kantor pelayanan cukup panjang tidak ada kejelasan",
        "fasilitas taman bermain kurang terawat beberapa rusak",
        "drainase tidak berfungsi optimal saat hujan deras",
        "pelayanan membutuhkan waktu lebih lama dari yang dijanjikan",
        "kondisi jalan perlu perhatian lebih dari pihak terkait",
        "sebaiknya ada jadwal rutin pemeliharaan jalan tiap bulan",
        "alangkah baiknya ada sistem pengaduan online yg mudah",
        "disaranin biar petugas kebersihan makin sering ke sini",
        "saran biar jam pelayanan kantor diperpanjangin sampe sore",
        "ada baiknya dibikin jalur khusus sepeda di jalan utama",
        "kayaknya perlu ada bank sampah di tiap kelurahan deh",
        "seharusnya ada pos kesehatan di tiap rt yang padat penduduk",
        "mohon dong segera pasang lampu jalan di kawasan gelap ini",
        "minta tolong buatin zebra cross di depan sekolah kami",
        "tlg tambahin armada bus rute ke perumahan kami dong",
        "harap sediain tempat sampah lebih banyak di taman ini",
        "kami butuh posyandu baru di kelurahan kami dong",
        "tlg bangun taman bermain buat anak di kelurahan ini",
        "warga berharap ada tindakan nyata dari pemda dong",
        "saya mau tanya prosedur ngurus ktp hilang gimana",
        "info jadwal angkut sampah di rt sini kapan ya",
        "gimana cara daftar beasiswa daerah buat anak saya",
        "kapan jadwal vaksin di puskesmas kita bulan ini",
        "ada info ga tentang program bedah rumah di sini",
        "cara ngurus surat pindah domisili gimana ya pak",
        "jadwal piket petugas kebersihan di sini kapan aja",
        "info biaya pasang sambungan baru pdam gimana ya",
        "syarat dapet bansos apa aja ya yang perlu disiapkan",
        "gimana cara komplain ke dinas soal jalan yang rusak",
        "mau tanya jam buka kantor pelayanan sini kapan ya",
        "ada ga info tentang jadwal razia pkl di sini",
        "cara daftar program kur buat usaha kecil gimana ya",
        "prosedur ngurus imb bangunan baru di sini gimana",
        *GENERATED_NETRAL,

    ],
    "labels": (
        ["negatif"] * 310 +
        ["positif"] * 300 +
        ["netral"]  * 300
    ),
}

# ================================================================
# DATASET TAMBAHAN — LAPORAN NYATA MASYARAKAT INDONESIA
# ================================================================
# Sumber  : dataset_Sheet1.csv (49 laporan nyata dari platform LAPOR!)
# Labeling: manual, berdasarkan isi teks
#
# Distribusi sentimen tambahan : {'negatif': 42, 'netral': 7}
# Distribusi intent tambahan   : {'keluhan': 32, 'permintaan': 12, 'darurat': 3, 'saran': 2}
#
# Data ini di-extend langsung ke SENTIMENT_DATA dan INTENT_DATA
# di bawah agar otomatis terbaca saat training.
# ================================================================

_REAL_TEXTS = [
    'Saya penerima bantuan PBI bulan mei 2026 tetapi sampai sekarang saya tidak merasa terima bantuan apapun bisa tolong beri saya sedikit penjelasan terkait masalah ini ?',
    'Tidak Bisa Cetak KTP di Kecamatan Baleendah Yth. Direktur Jenderal Dukcapil Kemendagri, Saya menyampaikan keberatan dan pengaduan terkait layanan pencetakan KTP-el di Kecamatan Baleendah, Kabupaten Bandung. Pada tanggal 2 Juni 2026 saya telah datang langsung ke lokasi dan telah memiliki barcode/antr',
    'Pengangkutan sampah tidak jalan Dear Dinas DLHK, saya mendapat informasi adanya problem pada TPA Jatiwaringin yang mengakibatkan sampah-sampah pada beberapa perumahan tidak bisa diangkut. Tolong dicarikan solusi secepatnya supaya sampah-sampah bisa segera diangkut.',
    'SK jafung IIIc saya belum turun SK jafung saya belum turun sampai sekarang, mohon izin ini biodata saya Nama : Hilim Qodriyah NIP: 198412192009022001 Instansi: Dinas pendidikan Unit kerja: SMAN 5 Tambun selatan Nomor SK IIIc: 823/Kep.2989-BKD/2016 Sudah 9 tahun saya IIIc, tidak bisa ke IIId kalau SK',
    'Jembatan Gantung rusak Jembatan gantung yang menjadi urat nadi penghubung antarwilayah kini berada dalam kondisi rusak dan memerlukan perhatian segera. Setiap hari, anak-anak harus mempertaruhkan keselamatan mereka saat melintasi jembatan untuk menuju sekolah. Di sisi lain, warga juga bergantung pad',
    'Perlakuan tidak wajar dan tidak bertanggung jawab Perlakuan tidak wajar, dan tidak bertanggung jawab dari dosen manajemen fakultas ekonomi dan bisnis universitas negeri Semarang bernama Andhi Wijayanto, S.E., M.M. kepada mahasiswa nya yang semester 5',
    'Pembakaran sampah di lingkungan rumah Mohon ditindak. Di lingkungan kami sering dilakukan pembakaran sampah oleh salah satu warga. Mengingat anak saya sendiri adalah penderita broncho pneumonia',
    'Kebutuhan Data Statistik Untuk Keperluan Pendidikan dan Penelitian Selamat siang Bapak/Ibu, Perkenalkan, nama saya Raihan Ahlan (NIM: 23225056), mahasiswa program Magister di Institut Teknologi Bandung (ITB). Saat ini, saya sedang melakukan penelitian tesis mengenai analisis kinerja pelaporan layana',
    'Pembakaran sampah Pembakaran sampah ilegal rutin untuk ambil besi dari pengusaha besi di jalan lestari curug, bojongsari depok dekat perumahan tamansari puribali. Sudah lapor RT, lurah dan babinsa tapi tidak ada action',
    'Pembakaran sampah Pembakaran sampah ilegal rutin untuk ambil besi dari pengusaha besi di jalan lestari curug, bojongsari depok dekat perumahan tamansari puribali. Sudah lapor RT, lurah dan babinsa tapi tidak ada action',
    'PENIPUAN BERKEDOK APLIKASI PPOB Saya Khalil Gibran Merdeka Mendepositokan uang saya senilai 500 ribu rupiah ke aplikasi kilopay dengan mentransfer sejumlah nilai 500.167 ke e wallet ovo atas nama dian novita(dikarenakan mengikuti aplikasi)Saya menunggu cukup lama sehingga saldo masuk senilai 1jt leb',
    'Gangguan Kamtibmas di Kampung Halaman, Dapat Dibilang ODGJ Cuman Gara Gara Masalah Listrik, Karena Cuman Masalah Listrik Mremen Mremen Mremen Terus Ingin Memiliki Rumah & Segala Perabotan Rumah Tangganya',
    'KTP Ditahan Oleh Pihak Secure Parking Untuk penahanan KTP yang dilakukan oleh pihak secure parking sangat vatal bagi saya dan saya mengajak ngobrol untuk serah terima dari pihak secure parking tidak disediakan dan saya ngeyel untuk mengambil KTP saya tidak diberi dan tidak dikasi surat untuk pengamb',
    'Proses ganti Rugi Jalan Tol (Rumah warga) di Maguwoharjo Depok Sleman Yogyakarta Assalamualaikum wr wb, mau lapor untuk keluhan ganti rugi tol solo yogya di daerah maguwoharjo depok sleman. Kami Warga Kradenan Maguwoharjo depok Sleman Yogyakarta, Saat ini kami masih menunggu proses ganti rugi tanah.',
    'Ingin Menjadi Tentara Di Russia Kepada Yth. Bapak Presiden Republik Indonesia Bapak Prabowo Subianto Dengan hormat, Perkenalkan, saya seorang pemuda Indonesia yang sejak kecil memiliki cita-cita untuk menjadi seorang prajurit dan mengabdikan diri kepada bangsa serta negara. Saya tumbuh dengan rasa k',
    'Koprasi Merah Putih Assalamualaikum Wb.Wb.. dengan tidak mengurangi rasa hormat saya terhadap Pemerintah Ri Sampai Propinsi. khususnya di jawabarat. Pengadun kami adalah.. Kenpa Kopari Merah putih dalam peroaes pembangunannya harus 20M x 30M. Dimana dalam penentuan standar ini sangat mengganggu masy',
    'Longsor Akses Jalan Blok C Perumahan Citaville Dramaga Belum Ditangani Sejak 2023 dan Membahayakan Warga Yth. Pemerintah Kabupaten Bogor, Kami warga Perumahan Citaville Dramaga, Desa Cihideung Udik, Kecamatan Ciampea, Kabupaten Bogor, menyampaikan pengaduan terkait longsor pada akses jalan lingkunga',
    'Permohonan pembangunan jembatan layang untuk akses jalan tani Kami meminta dengan hormat kepada pemerintah agar melihat dan meninjau serta memberikan solusi bagi kami masyarakat/ petani yang kesulitan mengakses jalan menuju lahan pertanian kami. 16 tahun kami berputar jalan dengan jarak tempuh 7 kil',
    'Penebangan Total Pohon Jati Perum Puri Bintara Regency RT 20 RW 02 Bekasi Barat Mohon segera di lakukan dari dinas pemda Kota Bekasi u/ di lakukan : " Penebangan total pohon jati di perum puri bintara regency Rt 20 Rw 02 Jl. Bintara Raya Bekasi Barat " Di karenakan daun pohon jati setiap hari bergug',
    'Keluhan Ketiadaan Sistem Tiket Online dan Ketidakpraktisan Sistem Inden Fisik H-7 KA Lintas Barru-Makassar Yth. Direktur Balai Pengelola Kereta Api (BPKA) Sulawesi Selatan / Kementerian Perhubungan, Saya ingin menyampaikan laporan pengaduan sekaligus desakan keras terkait sistem pemesanan tiket Kere',
    'Ada seseorang menggunakan data saya Dia menggunakan data saya seperti foto dan nama di sosial media seperti Tiktok dan Facebook, dan menyebarkan nomer saya dan membuat status tidak senonoh',
    'tolong dong tolonh jika ibu titi masih bekerja sambil bawa anak tolong tegur dong ini kantor desa bukan taman anak anak, saya sebagai warga desa laksana sangat tidak nyaman, tolong dong buat bapak bapak yang terhormat tolong tegur beliau',
    'Pertamax vs pertalite harga Pertamax dan pertalite ada yang janggal. pertalite harga dasar 16.000 perliter pertamak harga 12.900 perliter. kenapa pemerintah mensubsidi pertalite yang kualitasnya dibawah pertamax sebesar 6000/liter harusnya pemerintah mensubsidi Pertamax yang harganya jauh lebih rend',
    'Penyalahgunaan wewenang, Pengelapan Dana dan Mosi Tidak Percaya Kepada Pemerintah Provinsi Jawa Barat Khusus nya Bapak Gubernur Jawa Barat Kami warga teluk Pucung RT 004/001 Bekasi Utara, Melaporkan tindakan RT yang melakukan tindakan penyalahgunaan wewenang, pengelapan dana dari perusahan-perusahan',
    'Harm Speech Ada seorang pegawai P3K yang bernama Priskila Leksair yang bertugas di SMP 2 Sera, Kec Pulau Lakor, MBD. Beliau ini give an hate speech kepada salah satu tenaga guru di SDI werwawan dalam bentuk Voice Note through dm di WA. Tolong ditindak lanjuti dengan keras mengingat pegawai ini sudah',
    'Santitasi buruk akibat kotoran burung dara milik tetangga mengotori rumah Yth petugas/instansi terkait, Saya ingin melaporkan adanya gangguan serius ketertiban umum di lingkungan kami. Tetangga memelihara burung dara dalam jumlah banyak tanpa dikandangkan (dilepas bebas). Akibatnya, kotoran burung d',
    'Cabut Aturan Mutasi ASN Minimal 10 Tahun Dengan hormat, mohon kepada pihak terkait agar segera mencabut kebijakan mutasi ASN dengan masa kerja minimal 10 tahun. Kebijakan tersebut dinilai bertentangan dengan UU ASN di atasnya serta perlu disesuaikan dengan kondisi dan kebutuhan di lapangan. Banyak A',
    'Dugaan penyalahgunaan data dan dokumen pribadi Selamat pagi. Saya mau melaporkan di duga seseorang yang telah menyalahgunakan dokumen dan data pribadi saya. Kronologi nya, kemarin malam saya mengikuti list job pekerjaan pertanian Jepang lewat seseorang yang menyalurkan job. Dan saya pun tertarik unt',
    'Permohonan Penjelasan Resmi Mengenai Status Penggunaan Map Koperasi pada Pelayanan Pertanahan kabupaten mojoketo Saya mengajukan permohonan klarifikasi kepada Kementerian ATR/BPN terkait penggunaan map yang dijual oleh koperasi dalam pelayanan pertanahan di Kantor Pertanahan Kabupaten Mojokerto. Seb',
    'Pengaduan Tindakan Pemerasan dan Pinjaman Online Ilegal a.n. Modal Uang "Saya ingin melaporkan aplikasi pinjaman online bernama \'Modal Uang\' yang melakukan praktik ilegal. Saya tidak pernah mengajukan pinjaman di aplikasi tersebut, namun pada tanggal 31 mei 2026 04,45, secara sepihak masuk dana se',
    'Permohonan Peninjauan Operasional Kafe Biliar yang Mengganggu Lingkungan Permukiman Saya ingin menyampaikan keluhan terkait kebisingan yang berasal dari sebuah kafe biliar yang beroperasi di lingkungan tempat tinggal saya. Kafe tersebut memiliki area terbuka (outdoor) dengan sekitar 5 meja biliar ya',
    'Apartemen LRT City Tebet Mangkrak minta refund Saya korban mangkrak nya apartemen LRT City Tebet dari developer PT ADCP (grup adhi karya) yang hingga kini bangunan mangkrak tidak jadi dan sudah wanprestasi lama, sudah tidak sanggup untuk melanjutkan cicilan ke bank cimb karena biaya hidup jakarta ya',
    'Tiang mau ambruk Tiang tanda bus stop di Ayodhya Tangerang fondasinya berlubang, takutnya ambruk. Tiang itu juga tertutup pohon, ngga terlihat.',
    'Pengaduan Etika dan Keteladanan Pegawai Sekolah di Media Sosial wakasek SDN Pondok Labu 03 Kepada Yth. Dinas Pendidikan Pemerintah Provinsi DKI Jakarta Dengan hormat, Saya ingin menyampaikan pengaduan terkait perilaku seorang Wakil Kepala Sekolah Bidang Kesiswaan yang menurut saya kurang mencerminka',
    'Pengelolaan Sarana Olahraga Peminat olahraga di kabupaten garut semakin meningkat, begitu pula dengan pengunjung lapangan SOR kerkof, namun lapangan SOR kerkof tidak dikelola dengan baik. Seperti taman / alat kalistenik yang sudah tidak layak. Bahkan sering kali taman kalistenik tersebut tidak bisa ',
    'Tips Tata Cara Reschedule Tiket Agoda Untuk Reschedule Tiket Agoda paling mudah dilakukan melalui WhatsApp/Telpon resmi di +62882-1237-5663.. (24 jam). Siapkan kode booking (PNR) dan data penumpang, sampaikan permintaan perubahan jadwal, lalu ikuti instruksi petugas...',
    'tuduhan yang tidak valid yang dibuat oleh kejati sulut untuk ibu chyntia ingrid kalangit (bupati kabupaten kepulauan siau tagulandang biaro) kronologi singkat mama saya seorang bupati di sebuah kabupaten kepulauan siau tagulandang biaro (sitaro) yang berada di sulawesi utara. awal kejadian gunung ru',
    'Denda Dari Pak RT Ketua RT 002 RW 009 Kecamatan Waru Kabupaten Sidoarjo Jawa Timur mewajibkan warganya: 1. Membayar iuran RT 100.000 saat arisan PKK atau pengajian saja 2. Jika pembayaran iuran dilakukan diluar 2 waktu tersebut maka warga diwajibkan membayar denda sebesar100.000 3. Jika tidak melaku',
    'pencurian motor pada tanggal 25 mei 2026, sekitar jam 7 motor saya berjenis honda beat 2018 hitam PLAT D 2066 ABN hilang di daerah kota bandung ancol tengah di gor akas jaya, saya parkir di dalem tp pencurian tersebut berani masuk ke dalam...dan ternyata di hari yang sama di jam 4, 2 org pencuri yan',
    'Apa layanan Halo 𝗕𝘊𝐀 24 jam? Ini Dia nomor layanan 𝗕𝘊𝐀 𝐂all 𝐂enter 𝐂s 𝗕𝘊𝐀 Ya, layanan Halo 𝐁𝐂A melalui (1500888) 085121311152 tersedia 24 jam sehari, 7 hari seminggu untuk kebutuhan perbankan Anda. (dengan #Halo𝐁𝐂A bisa) free WhatsApp. 1500888. 6285121311152 untuk memulai chat dengan Customer Servic',
    'Kerugian Konsumen Saya Berlangganan Interner MyRepublic sejak 3 Oktober 2025, dengan value 50mbps up to 100mbps di 3bulan pertama dengan total biaya 277.500 (sudah termasuk ppn), namun hanya selang 2 hari ditanggal 5 Oktober saya sudah mendapatkan problem koneksi internet yang jelek, dan berlangsung',
    'Permohanan bantuan Pak/bu, saya ingin menyampaikan keluhan supaya pemerintah bisa membantu saya. Saya yatim piatu sudah 3 bulan kehilangan pekerjaan, sulit sekali memenuhi kebutuhan sehari hari. Dari kebutuhan pokok, kebutuhan biaya adik sekolah mau sma dan masih harus wajib bayar pajak juga. Tolong',
    'Arisan bodong yang merupakan Ibu Bhayangkari Polres Belitung Timur Saya sudah melapor terkait arisan bodong yang terima, tapi sampai sekarang proses ya lama sekali Sudah mau jalan 60 hari kalender Dari tanggal 7 April - 29 Mei 2026 Apakah karna dia ibu bhayangkari jadi proses ya bisa di kata kan per',
    'BAKAR SAMPAH LIAR Saya mau melaporkan ada penghuni di Perumahan Komplek Koperasi II (Cimanggis, Depok, Jawa Barat) yang suka membakar sampah dari jam 22.00 malam keatas (kadang bakar jam 02.00 dini hari). Saya tidak tahu persis dari mana asal asap ini berasal, tapi asap-nya selalu mengarah di blok r',
    'Laporan terkait Ketenagakerjaan Dear adm Kemnaker, Dengan ini saya ingin melaporkan terkait perusahaan yaitu PT Bumi Berkah Boga / Kopi Kenangan yang berlokasi di outlet Ruko Pasar Rebo. Dengan ini, saya mengalami jam kerja tidak sesuai dimana seharusnya saya max 20 hari kerja dalam sebulan namun sa',
    'Pinjol Kredito Dana Tidak Cair Tapi Status Sukses Pencairan Saya mengajukan pinjaman di aplikasi Kredito PT Fintek Digital Indonesia pada tanggal 26 Mei 2025 sebesar Rp235.000 dengan nomor pinjaman ACI202605262017363278402336. Status di aplikasi sudah "Sukses Pencairan" ke rekening BNI 2077093083. N',
    'Kelayakan jalan lintas sumatera Assalamualaikum warahmatullahi wabarakatuh, Kepada Yth. Bapak/Ibu, Dengan hormat, kami ingin menyampaikan keluh kesah serta aspirasi masyarakat Kabupaten Muara Enim, khususnya Kecamatan Lawang Kidul, Provinsi Sumatera Selatan. Selama beberapa tahun terakhir, masyaraka',
    'Kelayakan jalan lintas sumatera Assalamualaikum warahmatullahi wabarakatuh, Kepada Yth. Bapak/Ibu, Dengan hormat, kami ingin menyampaikan keluh kesah serta aspirasi masyarakat Kabupaten Muara Enim, khususnya Kecamatan Lawang Kidul, Provinsi Sumatera Selatan. Selama beberapa tahun terakhir, masyaraka',
    'Pekerja kabel PLN Mohon maaf sebelum ny pak/bu. Saya pekerja dari cirebon 10 orang. Dan saya d sini udh hampir mau 2 bulan . Dan saya udh 2 bulan ini blom ada kejelasan dari pt saya harus gimana dan saya minta gaji saya tapi blom di cair" kan sampai saat ini . Saya sudah nganggur hampir 1 bulan lebi',
]

_REAL_SENT_LABELS = [
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'netral',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'netral',
    'negatif',
    'negatif',
    'netral',
    'netral',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'netral',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'netral',
    'negatif',
    'negatif',
    'negatif',
    'netral',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
    'negatif',
]

_REAL_INTENT_LABELS = [
    'keluhan',
    'keluhan',
    'permintaan',
    'keluhan',
    'permintaan',
    'keluhan',
    'permintaan',
    'permintaan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'permintaan',
    'keluhan',
    'darurat',
    'permintaan',
    'permintaan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'saran',
    'keluhan',
    'permintaan',
    'keluhan',
    'keluhan',
    'keluhan',
    'darurat',
    'keluhan',
    'saran',
    'permintaan',
    'keluhan',
    'keluhan',
    'darurat',
    'permintaan',
    'keluhan',
    'permintaan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'keluhan',
    'permintaan',
]

# ── Extend ke dataset utama ───────────────────────────────────────
SENTIMENT_DATA["texts"].extend(_REAL_TEXTS)
SENTIMENT_DATA["labels"].extend(_REAL_SENT_LABELS)

INTENT_DATA["texts"].extend(_REAL_TEXTS)
INTENT_DATA["labels"].extend(_REAL_INTENT_LABELS)