from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
import re

# =============================================
# TRAINING DATA — SENTIMENT
# =============================================
SENTIMENT_DATA = {
    "texts": [
        # ----- Negatif (20) -----
        "Jalan rusak parah di depan sekolah sudah lama",
        "Lampu jalan mati sudah seminggu sangat berbahaya",
        "Sampah menumpuk tidak diangkut berhari-hari baunya menyengat",
        "Air PDAM keruh tidak layak diminum sangat mengecewakan",
        "Pelayanan kantor sangat lambat dan tidak memuaskan",
        "Taman kota kotor jorok dan tidak terawat sama sekali",
        "Drainase tersumbat banjir setiap kali hujan turun",
        "Fasilitas kesehatan rusak dibiarkan tidak diperbaiki",
        "Trotoar berlubang parah membahayakan pejalan kaki",
        "Pelayanan buruk petugas tidak ramah mengecewakan sekali",
        "Saluran air mampet menimbulkan bau busuk tidak tertahankan",
        "Jembatan retak berbahaya dibiarkan tanpa perbaikan",
        "Kebakaran besar terjadi dan tidak ada bantuan datang",
        "Banjir parah merusak rumah warga sangat memprihatinkan",
        "Tanah longsor membahayakan warga situasi sangat mengkhawatirkan",
        "Kecelakaan parah tidak ada penanganan cepat sangat disayangkan",
        "Warga keracunan kondisi darurat tidak ada pertolongan datang",
        "Pohon tumbang menimpa rumah kondisi berbahaya memprihatinkan",
        "Halte bus rusak bocor tidak ada perbaikan sama sekali",
        "Kabel listrik menjuntai rendah sangat membahayakan warga",
        # ----- Positif (14) -----
        "Terima kasih jalan sudah diperbaiki dengan cepat dan baik",
        "Pelayanan sangat baik cepat dan memuaskan sekali",
        "Petugas ramah dan sangat membantu warga dengan sepenuh hati",
        "Terima kasih taman kota sudah bersih dan terawat indah",
        "Senang lampu jalan sudah dipasang wilayah jadi terang",
        "Pelayanan administrasi sangat memuaskan dan efisien",
        "Bagus sekali kinerja petugas kebersihan taman kota kita",
        "Apresiasi kepada petugas yang responsif dan profesional",
        "Luar biasa program pemerintah sangat membantu warga miskin",
        "Puskesmas pelayanannya meningkat pesat terima kasih banyak",
        "Petugas pemadam sangat cepat dan profesional hebat sekali",
        "Bangga dengan tim yang bekerja keras melayani masyarakat",
        "Salut respons pemerintah yang cepat menangani keluhan warga",
        "Senang taman bermain sudah diperbaiki anak-anak bisa bermain",
        # ----- Netral (20) -----
        "Kapan jadwal pengangkutan sampah di daerah sini",
        "Informasi jam pelayanan kantor kelurahan bagaimana",
        "Prosedur mengurus KTP di kantor kecamatan seperti apa",
        "Jadwal posyandu bulan ini kapan dan di mana",
        "Cara mendaftar bantuan sosial bagaimana caranya",
        "Syarat membuat surat keterangan domisili apa saja",
        "Jadwal pemadaman listrik bergilir di wilayah ini kapan",
        "Cara melaporkan kehilangan dokumen ke kantor mana",
        "Mohon segera dipasang lampu di jalan gelap ini",
        "Minta dibuatkan taman bermain untuk anak-anak di sini",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Sebaiknya ada petugas yang berpatroli setiap malam hari",
        "Alangkah baiknya pelayanan bisa dilakukan secara online",
        "Usul agar pasar ditata lebih rapi dan bersih teratur",
        "Tolong sediakan tempat sampah lebih banyak di taman ini",
        "Harap pasang rambu lalu lintas di persimpangan berbahaya ini",
        "Mohon ditambahkan fasilitas olahraga di taman kota",
        "Saran agar loket diperbanyak supaya antrian lebih cepat",
        "Disarankan agar jam kantor diperpanjang untuk pelayanan warga",
        "Sebaiknya dibuat sistem pengaduan online yang mudah diakses",
    ],
    "labels": (
        ["negatif"] * 20 +
        ["positif"] * 14 +
        ["netral"] * 20
    ),
}

# =============================================
# TRAINING DATA — INTENT
# =============================================
INTENT_DATA = {
    "texts": [
        # ===== KELUHAN (22) =====
        "Jalan rusak parah sudah lama tidak diperbaiki",
        "Sampah tidak diangkut berhari-hari baunya menyengat",
        "Lampu jalan mati sudah seminggu gelap berbahaya",
        "Air PDAM keruh tidak layak diminum warga mengeluh",
        "Drainase mampet banjir setiap kali hujan turun",
        "Fasilitas umum rusak dibiarkan tidak ada perbaikan",
        "Trotoar hancur berlubang bahaya buat pejalan kaki",
        "Taman kota jorok sampah berserakan tidak ada yang bersihin",
        "Pelayanan kantor lambat antre berjam-jam tidak ada kejelasan",
        "Jembatan retak berbahaya tidak segera diperbaiki",
        "Halte bus rusak atap bocor tidak ada perbaikan sama sekali",
        "Genangan air selalu ada di jalan ini setiap hujan",
        "Tempat sampah meluber mengotori lingkungan sekitar",
        "Saluran got tersumbat menimbulkan bau tidak sedap",
        "Kabel listrik menjuntai rendah berbahaya bagi warga",
        "Fasilitas taman bermain rusak berbahaya untuk anak-anak",
        "Penerangan jalan di gang kampung mati total sudah lama",
        "Pasar kumuh tidak ada pengelolaan kebersihan yang baik",
        "Papan nama jalan sudah hilang tidak ada penggantinya",
        "Pelayanan buruk petugas tidak mau membantu warga",
        "Pelayanan sangat lambat dan mengecewakan tidak karuan",
        "Petugas tidak ramah pelayanan sangat mengecewakan warga",
        # ===== PERMINTAAN (17) =====
        "Mohon dipasang lampu jalan baru di kawasan ini",
        "Minta dibuatkan zebra cross di depan sekolah dasar",
        "Harap tambahkan armada bus rute ke perumahan kami",
        "Tolong sediakan tempat sampah di taman kota",
        "Mohon bangun posyandu baru di kelurahan kami",
        "Minta perbaikan jalan yang berlubang di RT kami segera",
        "Harap pasang rambu lalu lintas di persimpangan berbahaya",
        "Tolong tambahkan toilet umum di area pasar",
        "Mohon sediakan bangku taman yang lebih banyak untuk warga",
        "Minta dibangun taman bermain untuk anak-anak di sini",
        "Harap segera pasang CCTV di area parkir yang rawan",
        "Tolong buatkan jalur sepeda yang aman di jalan utama",
        "Mohon tambahkan petugas keamanan di area ini malam hari",
        "Minta diadakan angkutan umum ke daerah terpencil kami",
        "Harap sediakan fasilitas difabel di kantor kelurahan",
        "Tolong segera perbaiki jembatan yang hampir roboh",
        "Mohon ditambahkan fasilitas olahraga di taman kota kami",
        # ===== SARAN (17) =====
        "Sebaiknya jadwal pengangkutan sampah diumumkan ke warga",
        "Alangkah baiknya ada taman baca di setiap kelurahan",
        "Saran agar loket pelayanan ditambah supaya tidak antre lama",
        "Lebih baik pelayanan online agar warga tidak perlu datang",
        "Disarankan agar petugas kebersihan berpatroli setiap hari",
        "Sebaiknya dibuat sistem pengaduan online yang mudah diakses",
        "Usul agar pasar ditata lebih rapi dan bersih teratur",
        "Sarankan agar jam operasional kantor diperpanjang hingga sore",
        "Sebaiknya ada sosialisasi program pemerintah ke masyarakat",
        "Alangkah lebih baik bila ada ruang terbuka hijau di sini",
        "Usul agar dibuat jalur evakuasi bencana yang jelas dan mudah",
        "Saran untuk menambah pelatihan kerja bagi warga muda",
        "Sebaiknya parkir liar ditertibkan secara rutin berkala",
        "Lebih baik bila ada bank sampah di setiap RT kelurahan",
        "Disarankan agar lampu lalu lintas diservis secara berkala",
        "Sebaiknya sistem antrian digitalisasi agar lebih efisien",
        "Usul agar ada bus sekolah gratis untuk siswa kurang mampu",
        # ===== APRESIASI (14) =====
        "Terima kasih jalan sudah diperbaiki dengan cepat dan baik",
        "Apresiasi kepada petugas yang sangat responsif dan ramah",
        "Bagus sekali pelayanan kantor kelurahan sekarang jauh membaik",
        "Salut dengan kinerja petugas kebersihan taman kota kita",
        "Terima kasih program bantuan sosial sangat membantu warga",
        "Senang sekali taman kota sudah bersih dan terawat rapi",
        "Petugas pemadam kebakaran sangat cepat dan profesional hebat",
        "Terima kasih lampu jalan sudah dipasang wilayah jadi terang",
        "Luar biasa kecepatan respons pemerintah menangani banjir",
        "Bangga dengan petugas yang bekerja keras melayani warga",
        "Pelayanan kesehatan di puskesmas meningkat pesat terima kasih",
        "Senang melihat taman bermain sudah diperbaiki anak-anak senang",
        "Salut pemerintah cepat tanggap menangani masalah warga",
        "Terima kasih fasilitas umum sudah diperbaiki dan terawat",
        # ===== DARURAT (14) =====
        "Kebakaran besar sedang terjadi tolong kirim pemadam sekarang",
        "Banjir parah menggenangi rumah warga butuh evakuasi segera",
        "Ada kecelakaan lalu lintas korban terluka butuh ambulans cepat",
        "Pohon besar tumbang menimpa rumah warga darurat perlu bantuan",
        "Tanah longsor menutup jalan evakuasi warga terisolir darurat",
        "Gempa merusak bangunan warga membutuhkan pertolongan segera",
        "Ada orang tenggelam di sungai tolong kirim tim penyelamat",
        "Kebocoran gas berbahaya di pemukiman segera ditangani darurat",
        "Korban jiwa akibat bencana perlu penanganan medis segera",
        "Jembatan ambruk warga terjebak tidak bisa menyeberang darurat",
        "Listrik konslet menyebabkan kebakaran segera bantu padamkan",
        "Warga keracunan massal butuh pertolongan medis segera cepat",
        "Ada kebakaran rumah warga perlu pertolongan segera cepat",
        "Kebakaran melanda pemukiman butuh bantuan segera darurat api",
    ],
    "labels": (
        ["keluhan"] * 22 +
        ["permintaan"] * 17 +
        ["saran"] * 17 +
        ["apresiasi"] * 14 +
        ["darurat"] * 14
    ),
}


# =============================================
# KEYWORD OVERRIDE — Fallback berbasis kata kunci kuat
# Ini mengatasi kelemahan Naive Bayes pada kalimat pendek/ambigu
# =============================================

# Jika ada kata kunci ini → paksa intent tertentu
INTENT_KEYWORDS = {
    "darurat": [
        "kebakaran", "terbakar", "api besar", "banjir bandang", "evakuasi",
        "ambulans", "tenggelam", "longsor", "gempa", "ledakan", "gas bocor",
        "keracunan massal", "korban jiwa", "darurat", "tolong segera",
    ],
    "apresiasi": [
        "terima kasih", "terimakasih", "makasih", "apresiasi", "salut",
        "bagus sekali", "hebat", "luar biasa", "bangga", "senang melihat",
        "memuaskan", "terbaik", "mantap",
    ],
    "saran": [
        "sebaiknya", "alangkah baiknya", "disarankan", "usul", "saran",
        "sarankan", "lebih baik bila", "seharusnya", "semestinya",
    ],
    "permintaan": [
        "mohon", "minta", "harap", "tolong", "dimohon", "kami butuh",
        "kami minta", "kami harap", "diminta", "diharapkan",
    ],
}

# Jika ada kata kunci ini → paksa sentiment tertentu
SENTIMENT_KEYWORDS = {
    "positif": [
        "terima kasih", "terimakasih", "makasih", "apresiasi", "salut",
        "bagus sekali", "hebat", "luar biasa", "bangga", "senang",
        "memuaskan", "mantap", "terbaik",
    ],
    "negatif": [
        "rusak", "mati", "bocor", "kotor", "jorok", "bau", "tidak berfungsi",
        "mengecewakan", "berbahaya", "bahaya", "mampet", "banjir", "longsor",
        "kebakaran", "kecelakaan", "terluka", "korban", "darurat",
    ],
}


# =============================================
# PREPROCESSING
# =============================================

def preprocess(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def keyword_override_intent(text: str) -> str | None:
    """
    Cek apakah teks mengandung kata kunci kuat.
    Urutan prioritas: darurat > apresiasi > saran > permintaan
    Kalau tidak ada keyword → return None (pakai ML)
    """
    text_lower = text.lower()
    priority_order = ["darurat", "apresiasi", "saran", "permintaan"]
    for intent in priority_order:
        for kw in INTENT_KEYWORDS[intent]:
            if kw in text_lower:
                return intent
    return None


def keyword_override_sentiment(text: str) -> str | None:
    """
    Cek kata kunci sentiment yang sangat kuat.
    positif dulu, lalu negatif.
    """
    text_lower = text.lower()
    for sentiment in ["positif", "negatif"]:
        for kw in SENTIMENT_KEYWORDS[sentiment]:
            if kw in text_lower:
                return sentiment
    return None


# =============================================
# MODEL PIPELINE
# =============================================

def build_pipeline(alpha: float = 0.3) -> Pipeline:
    return Pipeline([
        ('tfidf', TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )),
        ('clf', MultinomialNB(alpha=0.3)),
    ])


# =============================================
# CLASSIFIER
# =============================================

class AspiralyticaClassifier:
    def __init__(self):
        # Train sentiment model
        self.sentiment_model = build_pipeline()
        sent_texts = [preprocess(t) for t in SENTIMENT_DATA["texts"]]
        self.sentiment_model.fit(sent_texts, SENTIMENT_DATA["labels"])

        # Train intent model
        self.intent_model = build_pipeline()
        intent_texts = [preprocess(t) for t in INTENT_DATA["texts"]]
        self.intent_model.fit(intent_texts, INTENT_DATA["labels"])

    def predict_sentiment(self, text: str) -> str:
        # Coba keyword dulu
        kw = keyword_override_sentiment(text)
        if kw:
            return kw
        # Fallback ML
        return self.sentiment_model.predict([preprocess(text)])[0]

    def predict_intent(self, text: str) -> str:
        # Coba keyword dulu
        kw = keyword_override_intent(text)
        if kw:
            return kw
        # Fallback ML
        return self.intent_model.predict([preprocess(text)])[0]

    def determine_priority(self, sentiment: str, intent: str) -> str:
        if intent == "darurat":
            return "tinggi"
        if intent == "keluhan" and sentiment == "negatif":
            return "tinggi"
        if intent in ("keluhan", "permintaan"):
            return "sedang"
        return "rendah"

    def analyze(self, text: str) -> dict:
        sentiment = self.predict_sentiment(text)
        intent    = self.predict_intent(text)
        priority  = self.determine_priority(sentiment, intent)
        return {
            "sentiment": sentiment,
            "intent":    intent,
            "priority":  priority,
        }


# Singleton
classifier = AspiralyticaClassifier()