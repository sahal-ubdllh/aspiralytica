# backend/ml/train.py
# ================================================================
# TRAINING SCRIPT — Jalankan SEKALI untuk melatih & simpan model
# ================================================================
#
# Cara pakai:
#   cd backend
#   python -m ml.train
#
# Output:
#   ml/models/sentiment_model.pkl
#   ml/models/intent_model.pkl
#   ml/models/training_report.txt   ← laporan akurasi
#
# Kapan perlu dijalankan ulang?
#   - Setelah tambah/edit data training di ml/data.py
#   - Setelah ubah hyperparameter model
#   - Setelah pertama kali clone project ini
# ================================================================

import os
import pickle
import json
from datetime import datetime

from sklearn.naive_bayes import MultinomialNB
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
import numpy as np

from ml.data import INTENT_DATA, SENTIMENT_DATA
from ml.preprocessor import preprocess_batch

# ── Folder output untuk model ────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

SENTIMENT_MODEL_PATH = os.path.join(MODELS_DIR, "sentiment_model.pkl")
INTENT_MODEL_PATH    = os.path.join(MODELS_DIR, "intent_model.pkl")
REPORT_PATH          = os.path.join(MODELS_DIR, "training_report.txt")
METRICS_PATH         = os.path.join(MODELS_DIR, "metrics.json")


def build_pipeline(alpha: float = 0.3) -> Pipeline:
    """
    Membuat pipeline TF-IDF + Multinomial Naive Bayes.

    TF-IDF settings:
      ngram_range=(1,2)  → unigram + bigram
      sublinear_tf=True  → log normalization
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )),
        ("clf", MultinomialNB(alpha=alpha)),
    ])


def evaluate_model(pipeline: Pipeline, X: list, y: list, label: str, k: int = 10) -> dict:
    """
    Evaluasi model dengan k-Fold Cross Validation.

    Args:
        pipeline : sklearn Pipeline
        X        : list of preprocessed text
        y        : list of labels
        label    : nama model ('Sentimen' atau 'Intent')
        k        : jumlah fold (default 10)

    Returns:
        dict berisi semua metrik evaluasi
    """
    print(f"\n{'='*55}")
    print(f"  EVALUASI MODEL {label.upper()} ({k}-Fold CV)")
    print(f"{'='*55}")

    kfold  = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
    acc    = cross_val_score(pipeline, X, y, cv=kfold, scoring="accuracy")
    prec   = cross_val_score(pipeline, X, y, cv=kfold, scoring="precision_weighted")
    rec    = cross_val_score(pipeline, X, y, cv=kfold, scoring="recall_weighted")
    f1     = cross_val_score(pipeline, X, y, cv=kfold, scoring="f1_weighted")

    metrics = {
        "accuracy":  {"mean": float(acc.mean()),  "std": float(acc.std())},
        "precision": {"mean": float(prec.mean()), "std": float(prec.std())},
        "recall":    {"mean": float(rec.mean()),  "std": float(rec.std())},
        "f1_score":  {"mean": float(f1.mean()),   "std": float(f1.std())},
    }

    print(f"  Accuracy  : {acc.mean():.4f} ± {acc.std():.4f}")
    print(f"  Precision : {prec.mean():.4f} ± {prec.std():.4f}")
    print(f"  Recall    : {rec.mean():.4f} ± {rec.std():.4f}")
    print(f"  F1-Score  : {f1.mean():.4f} ± {f1.std():.4f}")

    # Train ulang dengan SEMUA data untuk classification report
    pipeline.fit(X, y)
    y_pred = pipeline.predict(X)

    print(f"\n  Classification Report (full training data):")
    report = classification_report(y, y_pred)
    print(report)

    return {**metrics, "classification_report": report}


def save_model(pipeline: Pipeline, path: str, label: str) -> None:
    """Simpan model ke file .pkl menggunakan pickle."""
    with open(path, "wb") as f:
        pickle.dump(pipeline, f)
    size_kb = os.path.getsize(path) / 1024
    print(f"  ✅ Model {label} disimpan → {path} ({size_kb:.1f} KB)")


def train():
    """
    Main training function.
    Melatih kedua model dan menyimpan hasilnya.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'#'*55}")
    print(f"  ASPIRALYTICA — TRAINING PIPELINE")
    print(f"  {timestamp}")
    print(f"{'#'*55}")

    all_metrics = {}

    # ── 1. SENTIMENT MODEL ───────────────────────────────────────
    print("\n[1/2] Memproses dataset sentimen...")
    X_sent = preprocess_batch(SENTIMENT_DATA["texts"])
    y_sent = SENTIMENT_DATA["labels"]
    print(f"  Total data: {len(X_sent)}")
    for label in set(y_sent):
        print(f"    {label}: {y_sent.count(label)}")

    pipe_sent = build_pipeline()
    sent_metrics = evaluate_model(pipe_sent, X_sent, y_sent, "Sentimen")
    save_model(pipe_sent, SENTIMENT_MODEL_PATH, "Sentimen")
    all_metrics["sentiment"] = sent_metrics

    # ── 2. INTENT MODEL ──────────────────────────────────────────
    print("\n[2/2] Memproses dataset intent...")
    X_intent = preprocess_batch(INTENT_DATA["texts"])
    y_intent = INTENT_DATA["labels"]
    print(f"  Total data: {len(X_intent)}")
    for label in set(y_intent):
        print(f"    {label}: {y_intent.count(label)}")

    pipe_intent = build_pipeline()
    intent_metrics = evaluate_model(pipe_intent, X_intent, y_intent, "Intent")
    save_model(pipe_intent, INTENT_MODEL_PATH, "Intent")
    all_metrics["intent"] = intent_metrics

    # ── 3. Simpan metrics ke JSON (untuk API /metrics) ───────────
    with open(METRICS_PATH, "w") as f:
        json.dump({
            "trained_at": timestamp,
            "sentiment": {
                k: v for k, v in all_metrics["sentiment"].items()
                if k != "classification_report"
            },
            "intent": {
                k: v for k, v in all_metrics["intent"].items()
                if k != "classification_report"
            },
        }, f, indent=2)
    print(f"\n  ✅ Metrics disimpan → {METRICS_PATH}")

    # ── 4. Simpan laporan teks ───────────────────────────────────
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(f"ASPIRALYTICA — TRAINING REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 55 + "\n\n")

        f.write("MODEL SENTIMEN\n")
        f.write("-" * 40 + "\n")
        f.write(f"Accuracy  : {all_metrics['sentiment']['accuracy']['mean']:.4f}"
                f" ± {all_metrics['sentiment']['accuracy']['std']:.4f}\n")
        f.write(f"F1-Score  : {all_metrics['sentiment']['f1_score']['mean']:.4f}"
                f" ± {all_metrics['sentiment']['f1_score']['std']:.4f}\n")
        f.write("\n" + all_metrics["sentiment"]["classification_report"])

        f.write("\nMODEL INTENT\n")
        f.write("-" * 40 + "\n")
        f.write(f"Accuracy  : {all_metrics['intent']['accuracy']['mean']:.4f}"
                f" ± {all_metrics['intent']['accuracy']['std']:.4f}\n")
        f.write(f"F1-Score  : {all_metrics['intent']['f1_score']['mean']:.4f}"
                f" ± {all_metrics['intent']['f1_score']['std']:.4f}\n")
        f.write("\n" + all_metrics["intent"]["classification_report"])

    print(f"  ✅ Laporan disimpan → {REPORT_PATH}")
    print(f"\n{'#'*55}")
    print(f"  TRAINING SELESAI — Semua model berhasil disimpan")
    print(f"{'#'*55}\n")


if __name__ == "__main__":
    train()