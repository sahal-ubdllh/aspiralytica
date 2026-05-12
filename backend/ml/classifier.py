from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
import re

# ================================================================
# ARSITEKTUR: FULL HYBRID (RULE + ML) + SARKASME DETECTION v2
# ================================================================
#
# Pipeline analisis:
#   1. Deteksi sarkasme → jika terdeteksi, paksa intent=keluhan + sentiment=negatif
#   2. Keyword rules intent  : darurat > apresiasi > keluhan > saran > permintaan
#   3. Keyword rules sentimen: negatif_kw > positif_kw > netral(saran/perm) > ML
#   4. ML Naive Bayes sebagai fallback terakhir
#
# ================================================================
# PERUBAHAN v2 — SARKASME DETECTION
# ================================================================
# Masalah v1 yang diperbaiki:
#   1. "Salut/Hebat/Kagum/Luar biasa..." (pujian eksplisit TANPA penguat)
#      + konteks negatif → sebelumnya lolos, kini tertangkap Layer 3
#   2. Variasi ejaan "antri" (v1 hanya punya "antre") → ditambahkan
#   3. Kontradiksi baru: "tanpa solusi", "tidak pernah disentuh",
#      "menggunung", "tidak dilayani", "tanpa kualitas", dll
#   4. "hebat" ditambahkan ke _SARC_POSITIF_TANPA_PENGUAT
#
# 4 Layer deteksi sarkasme:
#   Layer 1a: kata positif SANGAT KUAT (dgn penguat) + kontradiksi spesifik
#   Layer 1b: kata positif SANGAT KUAT (dgn penguat) + kata negatif apapun
#   Layer 2 : kata positif biasa + penguat (sekali/betul/dll) + konteks negatif
#   Layer 3 : pujian eksplisit (salut, kagum, hebat, dll) + konteks negatif

# ================================================================
# SARKASME DETECTION
# ================================================================

# Kata positif yang sering dipakai secara sarkastik dengan penguat
_SARC_POSITIF_KUAT = [
    "bangga sekali", "senang sekali", "luar biasa sekali", "bagus sekali",
    "hebat sekali", "keren sekali", "mantap sekali", "terima kasih sekali",
    "sungguh membanggakan", "sungguh luar biasa", "wah keren", "wah bagus",
    "wah hebat", "sangat bangga", "sangat kagum", "membanggakan sekali",
    "mengagumkan sekali", "bangga betul", "senang betul", "hebat betul",
    "bagus betul", "mantap betul", "keren betul", "luar biasa betul",
]

# Kontradiksi spesifik — hasil buruk setelah pujian
_SARC_KONTRADIKSI = [
    "langsung rusak", "langsung mati", "langsung mampet", "langsung berlubang",
    "langsung hancur", "langsung ambruk", "langsung bocor",
    "sampai harus antre", "sampai tidak pernah", "sampai tidak ada",
    "hingga harus antre", "hingga tidak pernah",
    "sudah membiarkan", "telah membiarkan",
    "membiarkan sampah", "membiarkan jalan", "membiarkan warga",
    "mudah rapuh", "cepat rusak", "asal jadi", "asal bangun",
    "tidak pernah datang", "tidak pernah hadir", "tidak pernah ada",
    "tidak pernah sampai", "tidak pernah diperbaiki",
    "kerja santai", "kerja lambat", "kerja asal",
    "dibiarkan antre", "dibiarkan begitu saja",
    # v2: tambahan kontradiksi
    "tidak pernah disentuh", "tidak pernah ditangani", "tidak pernah diperhatikan",
    "tidak pernah diselesaikan", "tidak pernah dikerjakan",
    "tanpa kualitas", "tanpa hasil", "tanpa solusi",
    "biarkan jalan rusak", "biarkan sampah", "biarkan warga",
    "tidak ada yang peduli", "tidak ada yang merespons",
    "puluhan tahun tidak",
]

# Kata positif dasar (untuk Layer 2 dengan penguat)
_SARC_KATA_POS = [
    "bangga", "senang", "terima kasih", "luar biasa", "bagus",
    "hebat", "keren", "mantap", "alhamdulillah", "mengagumkan",
]

# Konteks negatif (untuk Layer 2 & 3)
_SARC_KATA_NEG = [
    "rusak", "berlubang", "mampet", "mati", "bocor", "kotor",
    "menumpuk", "rapuh", "lubang", "tidak pernah", "dibiarkan",
    "antre", "antri",          # v2: tambah variasi ejaan
    "lambat", "buruk", "parah", "hancur",
    # v2: tambahan konteks negatif
    "menggunung", "tanpa kualitas", "tanpa solusi", "tanpa hasil",
    "tidak ada yang peduli", "tidak disentuh", "tidak ditangani",
    "biarkan jalan", "biarkan sampah", "makin parah", "tidak dilayani",
]

# Penguat yang menandai ekspresi berlebihan (ciri khas sarkasme)
_SARC_PENGUAT = [
    "sekali", "betul", "banget", "benar", "sungguh", "amat", "nian",
]

# v2 (BARU) Layer 3: pujian eksplisit tanpa perlu penguat
# Kata-kata ini sendiri cukup bernada tinggi sehingga
# jika muncul bersama konteks negatif → sangat mungkin sarkasme
_SARC_POSITIF_TANPA_PENGUAT = [
    "salut", "acungan jempol", "patut dipuji", "patut diacungi",
    "luar biasa", "kagum", "membanggakan", "mengagumkan", "menakjubkan",
    "hebat",
]


def detect_sarcasm(text: str) -> bool:
    """
    Mendeteksi sarkasme dalam teks bahasa Indonesia.
    Mengembalikan True jika kalimat terdeteksi sarkastik.

    4 layer deteksi:
      Layer 1a: kata positif kuat + kontradiksi spesifik
      Layer 1b: kata positif kuat + kata negatif apapun
      Layer 2 : kata positif biasa + penguat + konteks negatif
      Layer 3 : pujian eksplisit (salut, kagum, hebat, dll) + konteks negatif  [v2]
    """
    tl = text.lower()

    has_strong_pos = any(kw in tl for kw in _SARC_POSITIF_KUAT)
    has_contradict = any(kw in tl for kw in _SARC_KONTRADIKSI)
    has_any_neg    = any(kw in tl for kw in _SARC_KATA_NEG)

    # Layer 1a
    if has_strong_pos and has_contradict:
        return True
    # Layer 1b
    if has_strong_pos and has_any_neg:
        return True

    # Layer 2: kata positif biasa + penguat + konteks negatif
    has_penguat   = any(p in tl for p in _SARC_PENGUAT)
    has_basic_pos = any(kw in tl for kw in _SARC_KATA_POS)
    if has_penguat and has_basic_pos and has_any_neg:
        return True

    # Layer 3 (v2 BARU): pujian eksplisit + konteks negatif
    has_explicit_praise = any(kw in tl for kw in _SARC_POSITIF_TANPA_PENGUAT)
    if has_explicit_praise and has_any_neg:
        return True

    return False


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
    "memuaskan", "sangat memuaskan", "puas sekali", "sangat puas",
    "senang sekali", "bangga", "salut",
    "semakin membaik", "terus membaik", "terus meningkat",
    "membaik dari waktu", "jauh lebih baik", "jauh meningkat",
    "pelayanan baik", "pelayanan bagus", "pelayanan memuaskan",
    "pelayanan ramah", "pelayanan sangat baik", "sangat baik",
    "sangat membantu", "membantu sekali",
    "dipermudah", "dimudahkan",
]

KELUHAN_KEYWORDS = [
    "rusak parah", "rusak berat", "tidak diperbaiki", "tidak diangkut",
    "tidak mengalir", "tidak menyala", "tidak berfungsi", "tidak terawat",
    "tidak ada perbaikan", "tidak ada yang peduli", "tidak ada respons",
    "tidak ada tindakan", "tidak pernah diperbaiki", "tidak kunjung beres",
    "sudah lama rusak", "dibiarkan rusak", "dibiarkan begitu saja",
    "sangat mengecewakan", "sangat buruk", "sangat lambat",
    "tidak karuan", "tidak masuk akal", "tidak profesional",
    "parah sekali", "buruk sekali", "jorok sekali", "kotor sekali",
    "sangat kotor", "sangat disayangkan", "memprihatinkan",
    "tidak kondusif", "tidak layak", "tidak layak huni",
    "sudah capek", "sudah lelah", "lelah melaporkan", "capek melaporkan",
    "menyengat", "bau busuk", "bau sampah",
    "sudah berhari-hari", "sudah berminggu-minggu",
    "berbulan-bulan", "berkali-kali dilaporkan",
    "semakin parah", "semakin buruk", "makin parah",
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

SENT_NEGATIF_KW = [
    "rusak parah", "rusak berat", "sangat buruk", "sangat lambat",
    "sangat mengecewakan", "tidak berfungsi", "tidak diperbaiki",
    "tidak diangkut", "tidak mengalir", "tidak menyala", "tidak terawat",
    "bau busuk", "bau sampah", "menyengat", "jorok sekali", "kotor sekali",
    "buruk sekali", "parah sekali", "tidak karuan", "tidak masuk akal",
    "dibiarkan rusak", "tidak ada perbaikan", "sangat berbahaya",
    "memprihatinkan", "mengkhawatirkan", "sangat disayangkan",
    "sudah capek", "sudah lelah", "tidak kondusif", "tidak layak",
    "semakin parah", "semakin buruk", "makin parah",
    "tidak ada respons", "tidak kunjung beres",
    "insiden serius", "situasi kritis", "kondisi kritis",
    "butuh penanganan cepat", "gawat darurat", "nyawa terancam",
    "luka parah", "tidak sadarkan diri",
    "kebakaran", "banjir bandang", "tanah longsor", "gempa",
    "korban jiwa", "keracunan massal", "ambruk", "tenggelam",
]

SENT_POSITIF_KW = [
    "terima kasih", "terimakasih", "makasih",
    "bagus sekali", "sangat bagus", "luar biasa", "hebat sekali",
    "acungan jempol", "patut diapresiasi", "patut dipuji",
    "memuaskan", "sangat memuaskan", "puas sekali", "sangat puas",
    "senang sekali", "bangga", "salut", "mantap",
    "sangat membantu", "membantu sekali", "dipermudah", "dimudahkan",
    "pelayanan baik", "pelayanan bagus", "pelayanan memuaskan",
    "pelayanan ramah", "pelayanan sangat baik", "sangat baik",
    "semakin membaik", "terus membaik", "terus meningkat",
    "jauh lebih baik", "jauh meningkat", "membaik dari waktu",
]


# ================================================================
# TRAINING DATA — INTENT (155 + 10 sarkasme = 165 total)
# ================================================================

INTENT_DATA = {
    "texts": [
        # ===== KELUHAN (40) =====
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
        "Saluran got tersumbat menimbulkan bau tidak sedap di mana-mana",
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
        # ===== PERMINTAAN (30) =====
        "Mohon dipasang lampu jalan baru di kawasan gelap ini",
        "Minta dibuatkan zebra cross di depan sekolah dasar",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Tolong sediakan tempat sampah yang cukup di taman kota",
        "Mohon bangun posyandu baru di kelurahan kami segera",
        "Minta perbaikan jalan yang berlubang parah di RT kami",
        "Harap pasang rambu lalu lintas di persimpangan yang berbahaya",
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
        "Tolong pasang portal jalan untuk cegah kendaraan berat masuk",
        "Mohon tambahkan lampu sorot di area yang sering jadi TKP",
        "Minta dilakukan pengerukan saluran drainase yang sudah penuh",
        "Harap ada program penanaman pohon di sepanjang jalan ini",
        "Kami sangat membutuhkan ruang terbuka hijau di wilayah kami",
        "Tolong lakukan fogging nyamuk di wilayah kami yang rawan DBD",
        "Diharapkan ada program bersih-bersih lingkungan setiap minggu",
        # ===== SARAN (30) =====
        "Sebaiknya jadwal pengangkutan sampah diumumkan lebih awal",
        "Alangkah baiknya ada taman baca di setiap kelurahan kota",
        "Saran agar loket pelayanan ditambah supaya tidak antre lama",
        "Lebih baik pelayanan online agar warga tidak perlu datang",
        "Disarankan agar petugas kebersihan berpatroli dua kali sehari",
        "Sebaiknya dibuat sistem pengaduan online yang mudah diakses",
        "Usul agar pasar ditata lebih rapi dan bersih serta teratur",
        "Sarankan agar jam operasional kantor diperpanjang sampai sore",
        "Sebaiknya ada sosialisasi program pemerintah kepada masyarakat",
        "Alangkah lebih baik bila ada ruang terbuka hijau di sini",
        "Usul agar dibuat jalur evakuasi bencana yang jelas dan mudah",
        "Saran untuk menambah pelatihan kerja bagi warga usia muda",
        "Sebaiknya parkir liar ditertibkan secara rutin dan berkala",
        "Lebih baik bila ada bank sampah di setiap RT dan kelurahan",
        "Disarankan agar lampu lalu lintas diservis secara berkala",
        "Sistem pelayanan perlu dibenahi agar jauh lebih efisien",
        "Pengelolaan sampah bisa ditingkatkan dengan teknologi modern",
        "Sistem antrian digital dapat diterapkan di kantor kelurahan",
        "Database warga bisa didigitalisasi agar pelayanan lebih cepat",
        "Aplikasi pengaduan perlu dibenahi agar lebih mudah digunakan",
        "Ada baiknya peraturan parkir diperketat di area pusat kota",
        "Sebaiknya ada sanksi tegas bagi pembuang sampah sembarangan",
        "Hendaknya dibuat regulasi ketat untuk bangunan liar di sini",
        "Kiranya perlu ada evaluasi rutin kinerja petugas pelayanan",
        "Perlu ditingkatkan transparansi penggunaan anggaran daerah",
        "Perlu dibenahi sistem drainase agar tidak banjir setiap hujan",
        "Bisa ditingkatkan kualitas jalan dengan material yang lebih baik",
        "Dapat ditingkatkan jumlah CCTV di titik rawan kejahatan",
        "Seharusnya ada jalur pejalan kaki yang nyaman di setiap jalan",
        "Lebih baik bila lampu penerangan dipasang di seluruh gang",
        # ===== APRESIASI (30) =====
        "Terima kasih jalan sudah diperbaiki dengan cepat dan baik",
        "Apresiasi kepada petugas yang sangat responsif dan ramah",
        "Terima kasih program bantuan sosial sangat membantu warga",
        "Terima kasih lampu jalan sudah dipasang wilayah jadi terang",
        "Terima kasih saluran air sudah dibersihkan banjir berkurang",
        "Terima kasih taman kota sudah dirapikan menjadi sangat indah",
        "Terima kasih fasilitas posyandu sudah diperbaiki dan lengkap",
        "Bagus sekali pelayanan kantor kelurahan sekarang jauh membaik",
        "Salut dengan kinerja petugas kebersihan taman kota kita",
        "Senang sekali taman kota sudah bersih dan sangat terawat",
        "Petugas pemadam kebakaran sangat cepat dan profesional sekali",
        "Luar biasa kecepatan respons pemerintah menangani banjir",
        "Bangga dengan petugas yang bekerja keras melayani warga",
        "Pelayanan kesehatan di puskesmas meningkat pesat alhamdulillah",
        "Senang melihat taman bermain sudah diperbaiki anak-anak senang",
        "Pelayanan di desa sangat dipermudah warga sangat terbantu",
        "Pelayanan petugas bagus dan ramah warga merasa puas dan senang",
        "Sangat memuaskan pelayanan di kantor ini warga puas sekali",
        "Pelayanan sangat baik dan cepat warga tidak perlu antre lama",
        "Pelayanan pemerintah daerah semakin membaik dari waktu ke waktu",
        "Kinerja para petugas patut mendapat acungan jempol dari warga",
        "Responsivitas pemerintah dalam menangani masalah sangat bagus",
        "Kondisi lingkungan semakin membaik berkat kerja keras petugas",
        "Sangat memuaskan hasil perbaikan yang dilakukan pemerintah",
        "Program kerja bakti sangat membantu warga membersihkan lingkungan",
        "Petugas sigap dan profesional dalam menjalankan tugas harian",
        "Semua petugas ramah dan sangat membantu warga dengan baik",
        "Kebijakan pemerintah kali ini tepat sasaran dan bermanfaat",
        "Fasilitas sudah diperbaiki warga sangat senang dan berterima kasih",
        "Lingkungan bersih indah berkat kerja keras petugas kebersihan",
        # ===== DARURAT (25) =====
        "Kebakaran besar sedang terjadi tolong kirim pemadam sekarang",
        "Listrik konslet menyebabkan kebakaran segera bantu padamkan api",
        "Ada kebakaran di pemukiman padat segera butuh bantuan pemadam",
        "Kebakaran melanda gudang dekat perumahan warga tolong segera",
        "Banjir parah menggenangi rumah warga butuh evakuasi segera",
        "Banjir bandang menghantam desa warga perlu diselamatkan cepat",
        "Tanah longsor menutup jalan evakuasi warga terisolir darurat",
        "Longsor menimbun rumah warga butuh alat berat dan bantuan segera",
        "Ada kecelakaan lalu lintas korban terluka butuh ambulans cepat",
        "Ada insiden serius di jalan tol butuh penanganan cepat segera",
        "Korban kecelakaan luka parah tidak sadarkan diri tolong segera",
        "Banyak korban jiwa akibat bencana perlu penanganan medis cepat",
        "Gempa bumi merusak bangunan warga membutuhkan pertolongan segera",
        "Ada orang tenggelam di sungai tolong kirim tim penyelamat",
        "Jembatan ambruk warga terjebak tidak bisa menyeberang darurat",
        "Kebocoran gas berbahaya di pemukiman segera ditangani darurat",
        "Warga keracunan massal butuh pertolongan medis segera dan cepat",
        "Puluhan warga keracunan makanan kondisi gawat darurat butuh tim",
        "Situasi kritis warga membutuhkan pertolongan segera malam ini",
        "Ada insiden serius terjadi di wilayah kami segera bantu kami",
        "Kondisi darurat warga perlu bantuan segera dari pihak berwajib",
        "Pohon besar tumbang menimpa rumah warga darurat perlu bantuan",
        "Nyawa warga terancam akibat bencana butuh evakuasi segera cepat",
        "Gawat darurat ada korban tidak sadarkan diri perlu ambulans",
        "Kebanjiran parah merendam seluruh desa warga butuh dievakuasi",
    ],
    "labels": (
        ["keluhan"] * 40 + ["permintaan"] * 30 +
        ["saran"] * 30 + ["apresiasi"] * 30 + ["darurat"] * 25
    ),
}

# ================================================================
# TRAINING DATA — SENTIMEN (105 total)
# ================================================================

SENTIMENT_DATA = {
    "texts": [
        # NEGATIF (35)
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
        "Kecelakaan parah tidak ada penanganan cepat sangat disayangkan",
        "Warga keracunan kondisi darurat tidak ada pertolongan datang",
        "Pohon tumbang menimpa rumah kondisi berbahaya memprihatinkan",
        "Warga sudah capek melaporkan tapi tidak ada respons sama sekali",
        "Sudah lelah berkali-kali lapor tapi masalah tidak kunjung beres",
        "Kondisi ini sangat memprihatinkan dan tidak ada yang peduli",
        "Situasi sudah tidak kondusif sangat mengkhawatirkan warga",
        "Sangat disayangkan pemerintah tidak tanggap terhadap keluhan",
        "Kondisi jalan semakin parah makin buruk setiap harinya",
        "Pelayanan semakin buruk tidak ada perbaikan sama sekali",
        "Lingkungan semakin kotor tidak terawat tidak layak huni",
        "Kondisi pasar sangat memprihatinkan kotor dan tidak layak",
        "Tidak ada tindakan apapun dari pemerintah sangat mengecewakan",
        "Fasilitas tidak layak dan sangat membahayakan keselamatan warga",
        "Air tidak mengalir sudah tiga hari warga sangat kesulitan",
        "Pelayanan tidak profesional dan sangat tidak memuaskan sekali",
        "Lampu tidak menyala gelap berbahaya sudah berminggu-minggu",
        "Masalah ini makin parah tidak ada yang bertanggung jawab",
        # POSITIF (30)
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
        "Fasilitas sudah diperbaiki warga sangat senang dan berterima kasih",
        "Lingkungan bersih indah berkat kerja keras petugas kebersihan",
        # NETRAL (40)
        "Kapan jadwal pengangkutan sampah di daerah sini",
        "Informasi jam pelayanan kantor kelurahan bagaimana caranya",
        "Prosedur mengurus KTP di kantor kecamatan seperti apa",
        "Jadwal posyandu bulan ini kapan dan di mana lokasinya",
        "Cara mendaftar bantuan sosial bagaimana prosedurnya",
        "Syarat membuat surat keterangan domisili apa saja yang perlu",
        "Jadwal pemadaman listrik bergilir di wilayah ini kapan",
        "Cara melaporkan kehilangan dokumen harus ke kantor mana",
        "Prosedur perpanjangan SIM di samsat terdekat bagaimana",
        "Biaya pembuatan akta kelahiran berapa dan prosedurnya",
        "Mohon segera dipasang lampu di jalan gelap ini",
        "Minta dibuatkan taman bermain untuk anak-anak di sini",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Tolong sediakan tempat sampah lebih banyak di taman ini",
        "Harap pasang rambu lalu lintas di persimpangan ini",
        "Minta dibuatkan zebra cross di depan sekolah dasar",
        "Mohon dipasang lampu jalan baru di kawasan ini",
        "Tolong tambahkan toilet umum di area pasar tradisional",
        "Harap sediakan fasilitas difabel di kantor kelurahan",
        "Kami membutuhkan posyandu baru di kelurahan kami",
        "Tolong bangun taman bermain untuk anak di kelurahan ini",
        "Mohon tambahkan petugas keamanan di area ini malam hari",
        "Kami ingin ada perbaikan fasilitas di wilayah ini",
        "Warga berharap ada tindakan nyata dari pemerintah daerah",
        "Perlu ada penambahan fasilitas kesehatan yang layak di sini",
        "Sebaiknya ada petugas yang berpatroli setiap malam hari",
        "Alangkah baiknya pelayanan bisa dilakukan secara online",
        "Usul agar pasar ditata lebih rapi dan bersih teratur",
        "Sebaiknya pelayanan diperbaiki agar warga tidak antri lama",
        "Disarankan agar jam buka kantor diperpanjang hingga sore",
        "Sebaiknya dibuat sistem pengaduan online yang mudah diakses",
        "Usul agar dibuat jalur sepeda yang aman di jalan utama",
        "Lebih baik jika ada petugas keamanan di sini malam hari",
        "Sistem pelayanan perlu dibenahi agar lebih efisien bagi warga",
        "Pengelolaan sampah bisa ditingkatkan dengan teknologi modern",
        "Perlu ditingkatkan transparansi penggunaan anggaran daerah",
        "Bisa ditingkatkan kualitas jalan dengan material lebih baik",
        "Sebaiknya ada sanksi tegas bagi pembuang sampah sembarangan",
        "Disarankan agar lampu lalu lintas diservis secara berkala",
        "Ada baiknya peraturan parkir diperketat di area pusat kota",
    ],
    "labels": (
        ["negatif"] * 35 + ["positif"] * 30 + ["netral"] * 40
    ),
}


# ================================================================
# PREPROCESSING
# ================================================================

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


# ================================================================
# MODEL
# ================================================================

def build_pipeline() -> Pipeline:
    return Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ('clf', MultinomialNB(alpha=0.3)),
    ])


# ================================================================
# CLASSIFIER — FULL HYBRID + SARKASME v2
# ================================================================

class AspiralyticaClassifier:
    def __init__(self):
        self.sentiment_model = build_pipeline()
        self.sentiment_model.fit(
            [preprocess(t) for t in SENTIMENT_DATA["texts"]],
            SENTIMENT_DATA["labels"],
        )
        self.intent_model = build_pipeline()
        self.intent_model.fit(
            [preprocess(t) for t in INTENT_DATA["texts"]],
            INTENT_DATA["labels"],
        )

    def predict_intent(self, text: str) -> str:
        tl = text.lower()
        for kw in DARURAT_KEYWORDS:
            if kw in tl: return "darurat"
        for kw in APRESIASI_KEYWORDS:
            if kw in tl: return "apresiasi"
        for kw in KELUHAN_KEYWORDS:
            if kw in tl: return "keluhan"
        for kw in SARAN_KEYWORDS:
            if kw in tl: return "saran"
        for kw in PERMINTAAN_KEYWORDS:
            if kw in tl: return "permintaan"
        return self.intent_model.predict([preprocess(text)])[0]

    def predict_sentiment(self, text: str, intent: str = "") -> str:
        tl = text.lower()
        for kw in SENT_NEGATIF_KW:
            if kw in tl: return "negatif"
        for kw in SENT_POSITIF_KW:
            if kw in tl: return "positif"
        if intent in ("saran", "permintaan"):
            return "netral"
        if intent == "darurat":
            return "negatif"
        return self.sentiment_model.predict([preprocess(text)])[0]

    def determine_priority(self, sentiment: str, intent: str) -> str:
        if intent == "darurat":
            return "tinggi"
        if intent == "keluhan" and sentiment == "negatif":
            return "tinggi"
        if intent in ("keluhan", "permintaan"):
            return "sedang"
        return "rendah"

    def analyze(self, text: str) -> dict:
        # ── STEP 1: Deteksi sarkasme ──────────────────────────────────
        is_sarcasm = detect_sarcasm(text)

        if is_sarcasm:
            # Sarkasme = keluhan terselubung dengan sentimen negatif
            return {
                "sentiment":  "negatif",
                "intent":     "keluhan",
                "priority":   "tinggi",
                "is_sarcasm": True,
            }

        # ── STEP 2: Pipeline normal ───────────────────────────────────
        intent    = self.predict_intent(text)
        sentiment = self.predict_sentiment(text, intent)
        priority  = self.determine_priority(sentiment, intent)
        return {
            "sentiment":  sentiment,
            "intent":     intent,
            "priority":   priority,
            "is_sarcasm": False,
        }


# Singleton
classifier = AspiralyticaClassifier()