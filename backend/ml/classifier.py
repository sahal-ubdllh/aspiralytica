# backend/ml/classifier.py
# ================================================================
# INFERENCE ENGINE — Load model .pkl dan lakukan prediksi
# ================================================================
#
# File ini HANYA bertugas:
#   1. Load model .pkl yang sudah ditraining
#   2. Menerima teks input
#   3. Mengembalikan hasil prediksi
#
# File ini TIDAK berisi:
#   - Training data       → ada di ml/data.py
#   - Preprocessing       → ada di ml/preprocessor.py
#   - Keyword rules       → ada di ml/rules.py
#   - Training logic      → ada di ml/train.py
#
# Alur inference:
#   Input teks
#     ↓
#   detect_sarcasm()      → jika sarkasme: langsung keluhan + negatif
#     ↓
#   rule_intent()         → cek keyword rules dulu
#     ↓ (fallback)
#   ML model (pkl)        → jika rules tidak cocok
#     ↓
#   rule_sentiment()      → cek keyword rules dulu
#     ↓ (fallback)
#   ML model (pkl)        → jika rules tidak cocok
#     ↓
#   determine_priority()  → heuristik prioritas
#     ↓
#   Return hasil
# ================================================================

import os
import pickle
import logging

from ml.preprocessor import preprocess
from ml.rules import detect_sarcasm, rule_intent, rule_sentiment

logger = logging.getLogger(__name__)

# ── Path model .pkl ──────────────────────────────────────────────
_MODELS_DIR           = os.path.join(os.path.dirname(__file__), "models")
_SENTIMENT_MODEL_PATH = os.path.join(_MODELS_DIR, "sentiment_model.pkl")
_INTENT_MODEL_PATH    = os.path.join(_MODELS_DIR, "intent_model.pkl")


def _load_model(path: str, name: str):
    """
    Load model dari file .pkl.
    Jika file tidak ada, jalankan train.py terlebih dahulu.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model '{name}' tidak ditemukan di: {path}\n"
            f"Jalankan training dulu: python -m ml.train"
        )
    with open(path, "rb") as f:
        model = pickle.load(f)
    logger.info(f"Model '{name}' berhasil dimuat dari {path}")
    return model


def _determine_priority(sentiment: str, intent: str) -> str:
    """
    Heuristik penentuan prioritas laporan.

    Tinggi  : darurat, atau keluhan + negatif
    Sedang  : keluhan (non-negatif), permintaan
    Rendah  : saran, apresiasi, netral
    """
    if intent == "darurat":
        return "tinggi"
    if intent == "keluhan" and sentiment == "negatif":
        return "tinggi"
    if intent in ("keluhan", "permintaan"):
        return "sedang"
    return "rendah"


class AspiralyticaClassifier:
    """
    Classifier utama Aspiralytica.

    Menggunakan arsitektur Hybrid: Rule-Based + ML (Naive Bayes).
    Model dimuat dari file .pkl saat inisialisasi.
    """

    def __init__(self):
        self._sentiment_model = _load_model(_SENTIMENT_MODEL_PATH, "sentiment")
        self._intent_model    = _load_model(_INTENT_MODEL_PATH, "intent")
        logger.info("AspiralyticaClassifier siap digunakan.")

    def predict_intent(self, text: str) -> str:
        """
        Prediksi intent dengan hybrid approach.
        Rules dicek dulu, ML sebagai fallback.
        """
        # Rule-based
        intent_rule = rule_intent(text)
        if intent_rule:
            return intent_rule
        # ML fallback
        return self._intent_model.predict([preprocess(text)])[0]

    def predict_sentiment(self, text: str, intent: str = "") -> str:
        """
        Prediksi sentimen dengan hybrid approach.
        Rules dicek dulu, ML sebagai fallback.
        """
        # Rule-based
        sentiment_rule = rule_sentiment(text, intent)
        if sentiment_rule:
            return sentiment_rule
        # ML fallback
        return self._sentiment_model.predict([preprocess(text)])[0]

    def analyze(self, text: str) -> dict:
        """
        Analisis lengkap: intent + sentimen + prioritas + sarkasme.

        Args:
            text: teks laporan dari pengguna

        Returns:
            dict dengan keys:
              - sentiment  : "positif" | "negatif" | "netral"
              - intent     : "keluhan" | "permintaan" | "saran" |
                             "apresiasi" | "darurat"
              - priority   : "tinggi" | "sedang" | "rendah"
              - is_sarcasm : True | False
        """
        # ── Step 1: Deteksi sarkasme ─────────────────────────────
        if detect_sarcasm(text):
            return {
                "sentiment":  "negatif",
                "intent":     "keluhan",
                "priority":   "tinggi",
                "is_sarcasm": True,
            }

        # ── Step 2: Prediksi intent ──────────────────────────────
        intent = self.predict_intent(text)

        # ── Step 3: Prediksi sentimen (dengan konteks intent) ────
        sentiment = self.predict_sentiment(text, intent)

        # ── Step 4: Tentukan prioritas ───────────────────────────
        priority = _determine_priority(sentiment, intent)

        return {
            "sentiment":  sentiment,
            "intent":     intent,
            "priority":   priority,
            "is_sarcasm": False,
        }


# ── Singleton — dipakai oleh main.py ─────────────────────────────
# Jika model belum ada, akan raise FileNotFoundError dengan
# instruksi jelas cara menjalankan train.py
try:
    classifier = AspiralyticaClassifier()
except FileNotFoundError as e:
    logger.warning(str(e))
    classifier = None  # main.py harus cek ini sebelum pakai