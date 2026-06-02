# backend/ml/preprocessor.py
# ================================================================
# PREPROCESSING PIPELINE — Normalisasi + Cleaning
# ================================================================
# Urutan pipeline:
#   normalize() → preprocess()
#
# normalize()   : tangani bahasa informal (di normalizer.py)
# preprocess()  : cleaning akhir yang TIDAK terlalu agresif
#
# CHANGELOG v2 (revisi untuk dataset realistis):
#   - Pertahankan angka (1, 2, 3 dst) — informatif untuk NLP
#   - Pertahankan tanda baca penting: ! ? ,  (sinyal emosi/nada)
#   - Jangan hapus semua emoji — ganti ke token tekstual dulu
#   - Jangan formalisasi semua slang — normalizer hanya kerjakan
#     singkatan/variasi ejaan, bukan semua kata informal
#   - Hapus hanya karakter noise murni (karakter aneh, HTML tag)
#
# Dipanggil oleh: train.py dan classifier.py
# ================================================================

import re
from ml.normalizer import normalize

# ── Peta emoji → token teks ─────────────────────────────────────
# Emoji yang sering muncul di laporan masyarakat Indonesia.
# Dikonversi ke token agar bisa diproses TF-IDF tanpa dihapus.
_EMOJI_MAP = {
    "👍": " jempol ",
    "👎": " tidak_setuju ",
    "😡": " marah ",
    "😤": " kesal ",
    "😢": " sedih ",
    "😭": " menangis ",
    "🙏": " mohon ",
    "❌": " tidak ",
    "✅": " oke ",
    "⚠️": " peringatan ",
    "🔥": " kebakaran ",
    "💧": " air ",
    "🚨": " darurat ",
    "😱": " kaget ",
    "🤦": " kecewa ",
}


def _replace_emoji(text: str) -> str:
    """Ganti emoji dengan token teks yang setara."""
    for emoji, token in _EMOJI_MAP.items():
        text = text.replace(emoji, token)
    # Hapus sisa emoji / unicode non-ASCII yang tidak tercatat
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u0400-\u04FF]', ' ', text)
    return text


def preprocess(text: str) -> str:
    """
    Full preprocessing pipeline (versi tidak agresif):
      1. Ganti emoji → token teks
      2. Normalisasi singkatan/slang (via normalizer.py)
      3. Lowercase
      4. Pertahankan angka dan tanda baca penting (! ?)
      5. Hapus noise murni (tag HTML, karakter duplikat non-makna)
      6. Normalisasi spasi

    Yang TIDAK dilakukan (berbeda dari versi lama):
      - Tidak hapus semua angka
      - Tidak hapus semua tanda baca
      - Tidak ubah semua kata informal ke bentuk formal

    Args:
        text: teks mentah dari pengguna

    Returns:
        teks bersih yang masih mempertahankan nuansa emosi & numerik

    Contoh:
        >>> preprocess("udah 5 jam antre gak dilayani!!! 😡")
        'sudah 5 jam antre tidak dilayani! marah'

        >>> preprocess("jln rusak prh bgt gak ada yg benesin tlg!!!")
        'jalan rusak parah sekali tidak ada yang memperbaiki tolong!'
    """
    text = _replace_emoji(text)            # Step 1: emoji → token
    text = normalize(text)                 # Step 2: singkatan / slang
    text = text.lower()                    # Step 3: lowercase

    # Step 4: Hapus noise murni — tag HTML, URL
    text = re.sub(r'<[^>]+>', ' ', text)   # strip HTML tags
    text = re.sub(r'https?://\S+', ' ', text)  # strip URL

    # Step 5: Normalisasi tanda baca berulang
    # !!! → ! | ??? → ? | ... → (spasi) — pertahankan satu karakter
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    text = re.sub(r'\.{2,}', ' ', text)
    text = re.sub(r',{2,}', ',', text)

    # Step 6: Hapus karakter selain huruf, angka, spasi, dan ! ? , .
    # Pertahankan: a-z (huruf), 0-9 (angka), ! ? , . - (tanda penting)
    text = re.sub(r'[^a-z0-9\s!?,.\-]', ' ', text)

    # Step 7: Normalisasi spasi
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def preprocess_batch(texts: list[str]) -> list[str]:
    """
    Preprocessing untuk banyak teks sekaligus.
    Dipakai saat training model.
    """
    return [preprocess(t) for t in texts]