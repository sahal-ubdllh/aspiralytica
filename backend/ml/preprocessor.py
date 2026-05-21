# backend/ml/preprocessor.py
# ================================================================
# PREPROCESSING PIPELINE — Normalisasi + Cleaning
# ================================================================
# Urutan pipeline:
#   normalize() → preprocess()
#
# normalize()   : tangani bahasa informal (di normalizer.py)
# preprocess()  : cleaning akhir (lowercase, hapus non-huruf)
#
# Dipanggil oleh: train.py dan classifier.py
# ================================================================

import re
from ml.normalizer import normalize


def preprocess(text: str) -> str:
    """
    Full preprocessing pipeline:
      1. Normalisasi teks informal (via normalizer.py)
      2. Lowercase & hapus karakter non-huruf (final clean)

    Args:
        text: teks mentah dari pengguna

    Returns:
        teks bersih siap masuk TF-IDF vectorizer

    Contoh:
        >>> preprocess("jln rusak prh bgt gak ada yg benesin tlg!!!")
        'jalan rusak parah sekali tidak ada yang benar tolong'
    """
    text = normalize(text)           # Step 1: tangani bahasa informal
    text = text.lower()              # Step 2: pastikan lowercase
    text = re.sub(r'[^a-z\s]', ' ', text)  # Step 3: hapus non-huruf
    text = re.sub(r'\s+', ' ', text).strip()  # Step 4: normalisasi spasi
    return text


def preprocess_batch(texts: list[str]) -> list[str]:
    """
    Preprocessing untuk banyak teks sekaligus.
    Dipakai saat training model.
    """
    return [preprocess(t) for t in texts]