"""
benchmark_from_pkl.py
=====================
Benchmark efisiensi komputasi menggunakan model .pkl Aspiralytica yang sudah ada.

Script ini:
  1. Memuat pipeline sentiment/intent yang sudah ditraining (TF-IDF + MNB)
  2. Mengekstrak TF-IDF vectorizer yang sudah fitted
  3. Meretrain SVM, LR, RF pada data yang sama (menggunakan TF-IDF matrix yg sudah ada)
  4. Membenchmark seluruh pipeline end-to-end (raw text → prediction)

Usage:
    # Benchmark model sentiment
    python benchmark_from_pkl.py \
        --model models/sentiment_model.pkl \
        --data  data/training_texts.txt \
        --labels data/training_labels.txt \
        --task  sentiment

    # Benchmark model intent
    python benchmark_from_pkl.py \
        --model models/intent_model.pkl \
        --data  data/training_texts.txt \
        --labels data/training_labels.txt \
        --task  intent

    # Atau gunakan data inline (tanpa file data)
    python benchmark_from_pkl.py --model models/sentiment_model.pkl --infer-only
"""

import argparse
import gc
import json
import os
import pickle
import time
import tracemalloc
import warnings
from copy import deepcopy

import numpy as np
import psutil
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# TEKS INFERENSI REPRESENTATIF (disesuaikan dengan domain Aspiralytica)
# ──────────────────────────────────────────────────────────────────────────────
INFERENCE_TEXTS = {
    "short":  "jalan rusak tolong perbaiki",
    "medium": "jalan rusak parah sudah berbulan bulan tidak ada yang memperbaiki mohon segera ditangani",
    "long":   (
        "saya ingin melaporkan bahwa kondisi jalan di depan rumah saya di rw 03 "
        "kelurahan sukamaju sudah rusak parah selama lebih dari 6 bulan "
        "banyak lubang besar yang membahayakan pengendara motor dan sudah ada 2 korban "
        "jatuh mohon bapak ibu yang berwenang segera menindaklanjuti laporan ini "
        "karena kondisi semakin memburuk terutama saat musim hujan"
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def load_pkl(path: str):
    with open(path, "rb") as f:
        return pickle.load(f)


def get_size_kb(obj) -> float:
    return len(pickle.dumps(obj)) / 1024


def get_file_size_kb(path: str) -> float:
    return os.path.getsize(path) / 1024


def extract_tfidf(pipeline: Pipeline) -> TfidfVectorizer:
    """Ekstrak TF-IDF vectorizer yang sudah fitted dari pipeline."""
    if hasattr(pipeline, "named_steps"):
        for name, step in pipeline.named_steps.items():
            if isinstance(step, TfidfVectorizer):
                return step
    raise ValueError("Pipeline tidak mengandung TfidfVectorizer.")


def rebuild_pipelines_with_same_tfidf(
    original_pipeline: Pipeline,
    texts: list[str],
    labels: list[str],
) -> dict[str, Pipeline]:
    """
    Buat 4 pipeline baru dengan TF-IDF yang identik (sama vocabulary & IDF weights),
    lalu latih masing-masing classifier pada data yang sama.

    Ini memastikan perbandingan fairplay: satu-satunya perbedaan adalah classifier.
    """
    tfidf = extract_tfidf(original_pipeline)

    classifiers = {
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.3),
        "SVM (LinearSVC)":        LinearSVC(max_iter=2000, C=1.0),
        "Logistic Regression":    LogisticRegression(max_iter=1000, C=1.0),
        "Random Forest":          RandomForestClassifier(n_estimators=100, n_jobs=1),
    }

    pipelines = {}
    for name, clf in classifiers.items():
        # Deep copy TF-IDF agar setiap pipeline punya instance sendiri
        tfidf_copy = deepcopy(tfidf)
        pipe = Pipeline([("tfidf", tfidf_copy), ("clf", clf)])
        pipe.fit(texts, labels)
        print(f"  ✓ {name} (retrained)")
        pipelines[name] = pipe

    return pipelines


# ──────────────────────────────────────────────────────────────────────────────
# BENCHMARK FUNCTIONS (sama seperti benchmark_models.py)
# ──────────────────────────────────────────────────────────────────────────────

def bench_latency(model, text: str, n: int = 1000, warmup: int = 10) -> dict:
    for _ in range(warmup):
        model.predict([text])
    lats = np.empty(n, dtype=np.float64)
    for i in range(n):
        t0 = time.perf_counter()
        model.predict([text])
        lats[i] = (time.perf_counter() - t0) * 1000
    return {
        "mean_ms": float(np.mean(lats)),
        "std_ms":  float(np.std(lats)),
        "min_ms":  float(np.min(lats)),
        "max_ms":  float(np.max(lats)),
        "p50_ms":  float(np.percentile(lats, 50)),
        "p95_ms":  float(np.percentile(lats, 95)),
        "p99_ms":  float(np.percentile(lats, 99)),
    }


def bench_memory(model, text: str, n: int = 100) -> dict:
    gc.collect()
    peaks = []
    for _ in range(n):
        gc.collect()
        tracemalloc.start()
        model.predict([text])
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peaks.append(peak / 1024)
    return {
        "inference_peak_mean_kb": float(np.mean(peaks)),
        "inference_peak_max_kb":  float(np.max(peaks)),
        "model_size_kb":          get_size_kb(model),
        "model_size_mb":          get_size_kb(model) / 1024,
    }


def bench_cpu(model, text: str, burst: int = 200) -> dict:
    gc.collect()
    proc = psutil.Process()
    for _ in range(10): model.predict([text])
    cb = proc.cpu_times(); wb = time.perf_counter()
    for _ in range(burst): model.predict([text])
    wa = time.perf_counter(); ca = proc.cpu_times()
    wall = (wa - wb) * 1000
    cpu  = ((ca.user - cb.user) + (ca.system - cb.system)) * 1000
    return {
        "cpu_time_per_call_ms":  float(cpu / burst),
        "wall_time_per_call_ms": float(wall / burst),
        "cpu_efficiency_pct":    float(cpu / wall * 100) if wall > 0 else 0.0,
    }


def bench_throughput(model, texts: list[str], batch: int = 100) -> dict:
    gc.collect()
    t0 = time.perf_counter()
    model.predict(texts[:batch])
    elapsed = time.perf_counter() - t0
    return {
        "batch_size":       batch,
        "batch_elapsed_ms": elapsed * 1000,
        "throughput_rps":   float(batch / elapsed),
    }


# ──────────────────────────────────────────────────────────────────────────────
# PRINT & SAVE
# ──────────────────────────────────────────────────────────────────────────────

def print_table(results: dict, task: str) -> None:
    print(f"\n{'='*110}")
    print(f"  BENCHMARK RESULTS — {task.upper()}")
    print(f"{'='*110}")
    hdr = f"{'Model':<28} {'Mean':>8} {'Std':>7} {'P95':>7} {'P99':>7} {'Max':>7} {'Size(KB)':>10} {'PeakMem(KB)':>12} {'CPU(ms)':>9} {'RPS':>8}"
    print(hdr)
    print("-" * 110)
    for name, r in results.items():
        l, m, c, t = r["latency"], r["memory"], r["cpu"], r["throughput"]
        print(f"{name:<28} {l['mean_ms']:>8.4f} {l['std_ms']:>7.4f} {l['p95_ms']:>7.4f} "
              f"{l['p99_ms']:>7.4f} {l['max_ms']:>7.4f} {m['model_size_kb']:>10.1f} "
              f"{m['inference_peak_mean_kb']:>12.2f} {c['cpu_time_per_call_ms']:>9.4f} "
              f"{t['throughput_rps']:>8.1f}")
    print("=" * 110)

    # Speedup ratios
    mnb_mean = results.get("Multinomial Naive Bayes", {}).get("latency", {}).get("mean_ms")
    if mnb_mean:
        print("\n  LATENCY SPEEDUP RATIO (baseline = Multinomial Naive Bayes = 1.00x)")
        print("-" * 55)
        for name, r in results.items():
            ratio = r["latency"]["mean_ms"] / mnb_mean
            flag = " ← PROPOSED" if name == "Multinomial Naive Bayes" else ""
            print(f"  {name:<28} {ratio:>6.2f}x{flag}")
        print()


def save_json(data: dict, path: str) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[INFO] Saved → {path}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark Aspiralytica models from .pkl")
    parser.add_argument("--model",       required=True, help="Path ke .pkl pipeline (sentiment/intent)")
    parser.add_argument("--data",        default=None,  help="Path ke file teks training (.txt, satu teks per baris)")
    parser.add_argument("--labels",      default=None,  help="Path ke file label training (.txt, satu label per baris)")
    parser.add_argument("--task",        default="sentiment", choices=["sentiment","intent"], help="Jenis task")
    parser.add_argument("--infer-only",  action="store_true", help="Hanya benchmark model asli (tidak retrain alternatif)")
    parser.add_argument("--iterations",  type=int, default=1000)
    parser.add_argument("--warmup",      type=int, default=10)
    parser.add_argument("--text-length", default="medium", choices=["short","medium","long"])
    parser.add_argument("--output",      default="benchmark_results_pkl.json")
    args = parser.parse_args()

    print(f"\n{'═'*60}")
    print(f"  ASPIRALYTICA BENCHMARK — {args.task.upper()}")
    print(f"  Model: {args.model}")
    print(f"  Text length: {args.text_length}")
    print(f"{'═'*60}")

    # ── Load model ────────────────────────────────────────────────
    print(f"\n[INFO] Loading {args.model} ...")
    original_pipeline = load_pkl(args.model)
    file_size_kb = get_file_size_kb(args.model)
    print(f"[INFO] File size on disk: {file_size_kb:.1f} KB")

    inference_text = INFERENCE_TEXTS[args.text_length]

    # ── Mode: hanya benchmark model asli ──────────────────────────
    if args.infer_only:
        print("\n[INFO] --infer-only mode: benchmarking original pipeline only")
        models = {"Original Pipeline": original_pipeline}
    else:
        # ── Load data untuk retrain alternatif ────────────────────
        if args.data and args.labels:
            with open(args.data)   as f: texts  = [l.strip() for l in f if l.strip()]
            with open(args.labels) as f: labels = [l.strip() for l in f if l.strip()]
            assert len(texts) == len(labels), "Jumlah teks dan label tidak sama!"
            print(f"[INFO] Loaded {len(texts)} training samples")
        else:
            print("[WARN] --data / --labels tidak disediakan. Menggunakan data sintetis untuk retrain.")
            from benchmark_models import SAMPLE_TEXTS, SENTIMENT_LABELS, INTENT_LABELS
            texts  = SAMPLE_TEXTS * 50
            labels = (SENTIMENT_LABELS if args.task == "sentiment" else INTENT_LABELS) * 50

        print(f"\n[INFO] Rebuilding all pipelines with same TF-IDF ...")
        models = rebuild_pipelines_with_same_tfidf(original_pipeline, texts, labels)

    # ── Benchmark ─────────────────────────────────────────────────
    results = {}
    for name, model in models.items():
        print(f"\n[BENCH] {name}")
        lat  = bench_latency(model, inference_text, args.iterations, args.warmup)
        mem  = bench_memory(model, inference_text)
        cpu  = bench_cpu(model, inference_text)
        tput = bench_throughput(model, [inference_text] * 100)
        results[name] = {"latency": lat, "memory": mem, "cpu": cpu, "throughput": tput}
        print(f"  mean={lat['mean_ms']:.4f}ms | p95={lat['p95_ms']:.4f}ms | "
              f"size={mem['model_size_kb']:.1f}KB | rps={tput['throughput_rps']:.0f}")

    # ── Report ────────────────────────────────────────────────────
    print_table(results, args.task)

    # Tambahkan metadata
    output = {
        "meta": {
            "task": args.task,
            "model_file": args.model,
            "file_size_on_disk_kb": file_size_kb,
            "inference_text_length": args.text_length,
            "inference_text": inference_text,
            "iterations": args.iterations,
            "warmup": args.warmup,
        },
        "results": {
            name: {
                "latency_mean_ms":       round(r["latency"]["mean_ms"],   4),
                "latency_std_ms":        round(r["latency"]["std_ms"],    4),
                "latency_min_ms":        round(r["latency"]["min_ms"],    4),
                "latency_max_ms":        round(r["latency"]["max_ms"],    4),
                "latency_p95_ms":        round(r["latency"]["p95_ms"],    4),
                "latency_p99_ms":        round(r["latency"]["p99_ms"],    4),
                "model_size_kb":         round(r["memory"]["model_size_kb"], 2),
                "model_size_mb":         round(r["memory"]["model_size_mb"], 4),
                "inference_peak_mem_kb": round(r["memory"]["inference_peak_mean_kb"], 2),
                "cpu_time_per_call_ms":  round(r["cpu"]["cpu_time_per_call_ms"], 4),
                "cpu_efficiency_pct":    round(r["cpu"]["cpu_efficiency_pct"], 2),
                "throughput_rps":        round(r["throughput"]["throughput_rps"], 1),
            }
            for name, r in results.items()
        }
    }
    save_json(output, args.output)


if __name__ == "__main__":
    main()