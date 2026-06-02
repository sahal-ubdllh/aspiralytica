"""
benchmark_models.py
===================
Computational Efficiency Benchmark — Aspiralytica ML Backend
Mengukur: inference latency, model file size, memory usage, CPU usage
untuk MNB, SVM, Logistic Regression, dan Random Forest.

Usage:
    python benchmark_models.py --sentiment-model models/sentiment_model.pkl \
                               --intent-model   models/intent_model.pkl \
                               --test-data      data/test_texts.txt \
                               --iterations     1000 \
                               --warmup         10 \
                               --output         benchmark_results.json

    # Atau tanpa model (akan generate dummy model dari dataset sintetis):
    python benchmark_models.py --demo
"""

import argparse
import gc
import json
import os
import pickle
import sys
import time
import tracemalloc
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import psutil
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────────────────────
# SYNTHETIC DATASET (dipakai saat --demo atau saat model belum ada)
# ──────────────────────────────────────────────────────────────────────────────

SAMPLE_TEXTS = [
    "jalan di depan rumah saya rusak parah sudah berbulan bulan tidak diperbaiki",
    "terima kasih pelayanan puskesmas sangat baik dan ramah",
    "tolong segera perbaiki lampu jalan yang mati di gang kelapa",
    "ada kebakaran di dekat pasar mohon bantuan segera",
    "saran saya agar jadwal pengangkutan sampah lebih teratur",
    "pelayanan kelurahan sangat lambat antri berjam jam tidak dilayani",
    "petugas kebersihan sangat rajin dan lingkungan jadi bersih",
    "mohon diperhatikan drainase yang tersumbat di jalan mawar rw 3",
    "banjir setinggi lutut masuk ke rumah warga tolong segera tangani darurat",
    "program posyandu sangat membantu warga kurang mampu terima kasih",
    "truk sampah tidak datang sudah 5 hari menumpuk bau sekali",
    "usul agar ada taman bermain untuk anak anak di kelurahan kami",
    "petugas sangat tidak sopan dan tidak mau membantu warga",
    "ada pohon tumbang menghalangi jalan utama tolong segera dibersihkan",
    "air pdam tidak mengalir sudah 3 hari tolong diperbaiki segera",
    "kegiatan kerja bakti minggu ini sangat meriah dan bermanfaat",
    "lampu merah di persimpangan jalan rusak berbahaya sekali",
    "terima kasih sudah memperbaiki jalan berlubang di depan sekolah",
    "tempat pembuangan sampah liar membuat lingkungan kotor dan bau",
    "minta tolong pasang cctv di area parkir yang sering terjadi pencurian",
]

SENTIMENT_LABELS = [
    "negatif", "positif", "netral", "darurat", "netral",
    "negatif", "positif", "netral", "negatif", "positif",
    "negatif", "netral", "negatif", "netral", "negatif",
    "positif", "negatif", "positif", "negatif", "netral",
]

INTENT_LABELS = [
    "keluhan", "apresiasi", "permintaan", "darurat", "saran",
    "keluhan", "apresiasi", "permintaan", "darurat", "apresiasi",
    "keluhan", "saran", "keluhan", "permintaan", "keluhan",
    "apresiasi", "keluhan", "apresiasi", "keluhan", "permintaan",
]

# Teks inferensi tunggal yang representatif untuk benchmark
INFERENCE_TEXT = (
    "jalan rusak parah sudah berbulan bulan tidak ada yang memperbaiki "
    "mohon segera ditangani karena membahayakan pengguna jalan"
)


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def build_pipeline(classifier) -> Pipeline:
    """Buat scikit-learn Pipeline: TF-IDF → Classifier."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )),
        ("clf", classifier),
    ])


def train_demo_models() -> dict[str, Pipeline]:
    """
    Latih empat model pada dataset sintetis.
    Dipakai saat --demo atau saat file .pkl tidak tersedia.
    """
    print("[INFO] Training demo models on synthetic dataset ...")

    # Perbanyak dataset sintetis agar model tidak trivial
    texts  = SAMPLE_TEXTS * 50
    labels = SENTIMENT_LABELS * 50

    models = {
        "Multinomial Naive Bayes": build_pipeline(MultinomialNB(alpha=0.3)),
        "SVM (LinearSVC)":        build_pipeline(LinearSVC(max_iter=2000, C=1.0)),
        "Logistic Regression":    build_pipeline(LogisticRegression(max_iter=1000, C=1.0)),
        "Random Forest":          build_pipeline(RandomForestClassifier(n_estimators=100, n_jobs=1)),
    }

    for name, pipe in models.items():
        pipe.fit(texts, labels)
        print(f"  ✓ {name}")

    return models


def load_model(path: str) -> Any:
    with open(path, "rb") as f:
        return pickle.load(f)


def get_model_size_kb(path: str) -> float:
    """Ukuran file .pkl dalam KB."""
    return os.path.getsize(path) / 1024


def get_model_size_kb_from_object(model: Any) -> float:
    """Serialize model ke buffer dan ukur ukurannya (KB)."""
    buf = pickle.dumps(model)
    return len(buf) / 1024


# ──────────────────────────────────────────────────────────────────────────────
# LATENCY BENCHMARK
# ──────────────────────────────────────────────────────────────────────────────

def benchmark_latency(
    model: Any,
    text: str,
    iterations: int = 1000,
    warmup: int = 10,
) -> dict:
    """
    Ukur inference latency (ms) untuk satu teks.

    Returns:
        dict: mean, std, min, max, p50, p95, p99 (semua dalam ms)
    """
    # Warm-up: pastikan model sudah di-cache CPU/OS, JIT warm
    for _ in range(warmup):
        model.predict([text])

    # Pengukuran
    latencies = np.empty(iterations, dtype=np.float64)
    for i in range(iterations):
        t0 = time.perf_counter()
        model.predict([text])
        t1 = time.perf_counter()
        latencies[i] = (t1 - t0) * 1000  # konversi ke ms

    return {
        "mean_ms":  float(np.mean(latencies)),
        "std_ms":   float(np.std(latencies)),
        "min_ms":   float(np.min(latencies)),
        "max_ms":   float(np.max(latencies)),
        "p50_ms":   float(np.percentile(latencies, 50)),
        "p95_ms":   float(np.percentile(latencies, 95)),
        "p99_ms":   float(np.percentile(latencies, 99)),
        "iterations": iterations,
        "warmup":   warmup,
        "raw_latencies_ms": latencies.tolist(),  # simpan untuk analisis lanjutan
    }


# ──────────────────────────────────────────────────────────────────────────────
# MEMORY BENCHMARK
# ──────────────────────────────────────────────────────────────────────────────

def benchmark_memory(model: Any, text: str, iterations: int = 100) -> dict:
    """
    Ukur alokasi memori saat inference menggunakan tracemalloc.

    Mengukur peak memory allocation per-inference call (bukan RSS proses).
    Diulang `iterations` kali; dilaporkan mean dan peak.

    Returns:
        dict: mean_kb, peak_kb, model_size_kb
    """
    gc.collect()
    peak_allocations = []

    for _ in range(iterations):
        gc.collect()
        tracemalloc.start()
        model.predict([text])
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_allocations.append(peak / 1024)  # bytes → KB

    # Ukuran model dalam memori
    model_size_kb = get_model_size_kb_from_object(model)

    return {
        "inference_peak_mean_kb": float(np.mean(peak_allocations)),
        "inference_peak_max_kb":  float(np.max(peak_allocations)),
        "inference_peak_std_kb":  float(np.std(peak_allocations)),
        "model_size_kb":          model_size_kb,
        "model_size_mb":          model_size_kb / 1024,
        "iterations":             iterations,
    }


# ──────────────────────────────────────────────────────────────────────────────
# CPU BENCHMARK
# ──────────────────────────────────────────────────────────────────────────────

def benchmark_cpu(model: Any, text: str, burst: int = 200) -> dict:
    """
    Estimasi CPU utilization saat inference burst.

    Strategi: jalankan `burst` inferensi dalam satu blok,
    catat CPU time sebelum dan sesudah, hitung CPU time per call.

    Returns:
        dict: cpu_time_per_call_ms, wall_time_per_call_ms, cpu_efficiency_pct
    """
    gc.collect()
    proc = psutil.Process()

    # Warm-up
    for _ in range(10):
        model.predict([text])

    cpu_before  = proc.cpu_times()
    wall_before = time.perf_counter()

    for _ in range(burst):
        model.predict([text])

    wall_after = time.perf_counter()
    cpu_after  = proc.cpu_times()

    wall_total_ms = (wall_after - wall_before) * 1000
    cpu_total_ms  = (
        (cpu_after.user - cpu_before.user) +
        (cpu_after.system - cpu_before.system)
    ) * 1000

    wall_per_call = wall_total_ms / burst
    cpu_per_call  = cpu_total_ms  / burst

    # CPU efficiency: berapa persen wall-time yang betul-betul CPU time
    cpu_efficiency = (cpu_total_ms / wall_total_ms * 100) if wall_total_ms > 0 else 0.0

    return {
        "cpu_time_per_call_ms":  float(cpu_per_call),
        "wall_time_per_call_ms": float(wall_per_call),
        "cpu_efficiency_pct":    float(cpu_efficiency),
        "burst_iterations":      burst,
        "total_wall_ms":         float(wall_total_ms),
        "total_cpu_ms":          float(cpu_total_ms),
    }


# ──────────────────────────────────────────────────────────────────────────────
# THROUGHPUT BENCHMARK
# ──────────────────────────────────────────────────────────────────────────────

def benchmark_throughput(model: Any, texts: list[str], batch_size: int = 100) -> dict:
    """
    Ukur throughput (requests per second) untuk batch inference.
    Relevan untuk estimasi kapasitas server.
    """
    gc.collect()
    t0 = time.perf_counter()
    model.predict(texts[:batch_size])
    t1 = time.perf_counter()
    elapsed = t1 - t0
    rps = batch_size / elapsed if elapsed > 0 else float("inf")

    return {
        "batch_size":       batch_size,
        "batch_elapsed_ms": elapsed * 1000,
        "throughput_rps":   float(rps),
    }


# ──────────────────────────────────────────────────────────────────────────────
# REPORT
# ──────────────────────────────────────────────────────────────────────────────

def print_report(results: dict) -> None:
    """Cetak laporan benchmark ke stdout dalam format tabel."""
    header = f"{'Model':<28} {'Mean(ms)':>9} {'Std':>7} {'Min':>7} {'Max':>7} {'P95':>7} {'P99':>7} {'Size(KB)':>10} {'PeakMem(KB)':>13} {'CPU(ms)':>9} {'RPS':>8}"
    print("\n" + "=" * len(header))
    print("  ASPIRALYTICA — COMPUTATIONAL EFFICIENCY BENCHMARK")
    print("=" * len(header))
    print(header)
    print("-" * len(header))

    for model_name, r in results.items():
        lat  = r["latency"]
        mem  = r["memory"]
        cpu  = r["cpu"]
        tput = r["throughput"]
        print(
            f"{model_name:<28} "
            f"{lat['mean_ms']:>9.4f} "
            f"{lat['std_ms']:>7.4f} "
            f"{lat['min_ms']:>7.4f} "
            f"{lat['max_ms']:>7.4f} "
            f"{lat['p95_ms']:>7.4f} "
            f"{lat['p99_ms']:>7.4f} "
            f"{mem['model_size_kb']:>10.1f} "
            f"{mem['inference_peak_mean_kb']:>13.2f} "
            f"{cpu['cpu_time_per_call_ms']:>9.4f} "
            f"{tput['throughput_rps']:>8.1f}"
        )
    print("=" * len(header))

    # Speedup ratio vs MNB
    print("\n  SPEEDUP RATIO (relative to Multinomial Naive Bayes)")
    print("-" * 55)
    mnb_mean = results.get("Multinomial Naive Bayes", {}).get("latency", {}).get("mean_ms", None)
    if mnb_mean:
        for name, r in results.items():
            ratio = r["latency"]["mean_ms"] / mnb_mean
            bar = "█" * int(ratio * 10)
            print(f"  {name:<28} {ratio:>6.2f}x  {bar}")
    print()


def save_report(results: dict, output_path: str) -> None:
    """Simpan hasil lengkap (termasuk raw latencies) ke JSON."""
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"[INFO] Full results saved to: {output_path}")


def save_paper_table(results: dict, output_path: str) -> None:
    """
    Simpan ringkasan dalam format siap-paste ke LaTeX / tabel Word.
    Tidak menyertakan raw_latencies untuk ukuran file yang ringkas.
    """
    summary = {}
    for name, r in results.items():
        summary[name] = {
            "latency_mean_ms":        round(r["latency"]["mean_ms"], 4),
            "latency_std_ms":         round(r["latency"]["std_ms"], 4),
            "latency_min_ms":         round(r["latency"]["min_ms"], 4),
            "latency_max_ms":         round(r["latency"]["max_ms"], 4),
            "latency_p95_ms":         round(r["latency"]["p95_ms"], 4),
            "latency_p99_ms":         round(r["latency"]["p99_ms"], 4),
            "model_size_kb":          round(r["memory"]["model_size_kb"], 2),
            "model_size_mb":          round(r["memory"]["model_size_mb"], 4),
            "inference_peak_mem_kb":  round(r["memory"]["inference_peak_mean_kb"], 2),
            "cpu_time_per_call_ms":   round(r["cpu"]["cpu_time_per_call_ms"], 4),
            "cpu_efficiency_pct":     round(r["cpu"]["cpu_efficiency_pct"], 2),
            "throughput_rps":         round(r["throughput"]["throughput_rps"], 1),
        }
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[INFO] Paper-ready summary saved to: {output_path}")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def run_benchmark(
    models: dict[str, Any],
    inference_text: str,
    iterations: int = 1000,
    warmup: int = 10,
    mem_iterations: int = 100,
    cpu_burst: int = 200,
    throughput_batch: int = 100,
) -> dict:
    """Jalankan semua benchmark untuk semua model."""
    results = {}

    for name, model in models.items():
        print(f"\n[BENCH] {name}")

        print(f"  ↳ Latency ({iterations} iterations, {warmup} warmup) ...")
        lat = benchmark_latency(model, inference_text, iterations, warmup)
        print(f"      mean={lat['mean_ms']:.4f}ms  p95={lat['p95_ms']:.4f}ms  p99={lat['p99_ms']:.4f}ms")

        print(f"  ↳ Memory ({mem_iterations} iterations) ...")
        mem = benchmark_memory(model, inference_text, mem_iterations)
        print(f"      model_size={mem['model_size_kb']:.1f}KB  peak_alloc={mem['inference_peak_mean_kb']:.2f}KB")

        print(f"  ↳ CPU ({cpu_burst} burst iterations) ...")
        cpu = benchmark_cpu(model, inference_text, cpu_burst)
        print(f"      cpu_per_call={cpu['cpu_time_per_call_ms']:.4f}ms  efficiency={cpu['cpu_efficiency_pct']:.1f}%")

        print(f"  ↳ Throughput (batch={throughput_batch}) ...")
        tput = benchmark_throughput(
            model,
            [inference_text] * throughput_batch,
            throughput_batch,
        )
        print(f"      {tput['throughput_rps']:.1f} req/s")

        results[name] = {
            "latency":    lat,
            "memory":     mem,
            "cpu":        cpu,
            "throughput": tput,
        }

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark MNB vs SVM vs LR vs RF — Aspiralytica",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--demo",            action="store_true",
                        help="Jalankan dengan model sintetis (tidak perlu file .pkl)")
    parser.add_argument("--sentiment-model", type=str, default=None,
                        help="Path ke .pkl pipeline sentiment")
    parser.add_argument("--intent-model",    type=str, default=None,
                        help="Path ke .pkl pipeline intent")
    parser.add_argument("--test-text",       type=str,
                        default=INFERENCE_TEXT,
                        help="Teks tunggal untuk benchmark latency/memory/CPU")
    parser.add_argument("--iterations",      type=int, default=1000,
                        help="Jumlah iterasi latency benchmark (default: 1000)")
    parser.add_argument("--warmup",          type=int, default=10,
                        help="Jumlah warm-up requests (default: 10)")
    parser.add_argument("--output",          type=str,
                        default="benchmark_results.json",
                        help="Path output JSON lengkap")
    parser.add_argument("--output-summary",  type=str,
                        default="benchmark_summary.json",
                        help="Path output JSON ringkasan untuk paper")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  ASPIRALYTICA — COMPUTATIONAL EFFICIENCY BENCHMARK")
    print(f"  Inference text: \"{args.test_text[:60]}...\"")
    print(f"  Iterations: {args.iterations} | Warmup: {args.warmup}")
    print("═" * 60)

    # ── Muat atau latih model ─────────────────────────────────────
    if args.demo:
        models = train_demo_models()
    elif args.sentiment_model:
        # Mode: bandingkan model dari file (hanya sentiment atau intent)
        base_model = load_model(args.sentiment_model)
        # Asumsi file adalah Pipeline; kita retrain alternatif
        # dengan TF-IDF yang sama untuk perbandingan adil
        print("[INFO] Loading sentiment model pipeline ...")

        # Ekstrak vocabulary dari TF-IDF yang sudah ditraining
        tfidf_vocab = base_model.named_steps["tfidf"].vocabulary_
        idf          = base_model.named_steps["tfidf"].idf_

        # Buat vectorizer baru dengan vocab yang sama
        from sklearn.feature_extraction.text import TfidfVectorizer as TV

        def make_tfidf_fixed():
            v = TV(ngram_range=(1,2), sublinear_tf=True, vocabulary=tfidf_vocab)
            v.idf_ = idf
            return v

        print("[WARN] Multi-model comparison from single pkl not supported in this mode.")
        print("       Using --demo mode instead.")
        models = train_demo_models()
    else:
        print("[INFO] No model file specified. Using --demo mode.")
        models = train_demo_models()

    # ── Jalankan benchmark ────────────────────────────────────────
    results = run_benchmark(
        models=models,
        inference_text=args.test_text,
        iterations=args.iterations,
        warmup=args.warmup,
    )

    # ── Laporan ───────────────────────────────────────────────────
    print_report(results)

    # Hapus raw latencies sebelum save ringkasan (file terlalu besar)
    save_paper_table(results, args.output_summary)

    # Simpan lengkap (dengan raw) ke output utama
    save_report(results, args.output)


if __name__ == "__main__":
    main()