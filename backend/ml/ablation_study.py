"""
ablation_study.py
=================
Ablation Study — Aspiralytica Hybrid Classification System
Mengukur kontribusi masing-masing komponen:
  - Rule-Based Only      : hanya keyword matching + sarcasm detection
  - ML Only              : hanya TF-IDF + Multinomial Naive Bayes
  - Hybrid (Full System) : rule-based sebagai gate + ML fallback

Usage (dari folder backend/):
    python ml/ablation_study.py
    python ml/ablation_study.py --output ml/evaluation/ablation_results.json
    python ml/ablation_study.py --folds 10 --seed 42

Untuk menjalankan dari folder ml/ langsung:
    cd backend && python -m ml.ablation_study
"""

import argparse
import json
import sys
import os
import warnings
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
)

warnings.filterwarnings("ignore")

# ── Pastikan backend/ ada di sys.path ────────────────────────────
# Script bisa dijalankan dari backend/ atau dari backend/ml/
_HERE = Path(__file__).resolve().parent          # backend/ml/
_ROOT = _HERE.parent                             # backend/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

# ── Import komponen Aspiralytica ─────────────────────────────────
try:
    from ml.data import INTENT_DATA, SENTIMENT_DATA
    from ml.rules import rule_intent, rule_sentiment, detect_sarcasm
    from ml.preprocessor import preprocess
    print("[OK] Imported from ml.*")
except ImportError:
    try:
        from data import INTENT_DATA, SENTIMENT_DATA
        from rules import rule_intent, rule_sentiment, detect_sarcasm
        from preprocessor import preprocess
        print("[OK] Imported from local package")
    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        print("  Pastikan script dijalankan dari folder backend/")
        sys.exit(1)


# ================================================================
# VARIANT CLASSIFIERS
# ================================================================

class RuleOnlyClassifier:
    """
    Komponen A: Rule-Based Only.
    Hanya menggunakan keyword matching dan sarcasm detection.
    Tidak ada ML sama sekali.

    Untuk teks yang tidak ter-cover rule:
      - Intent  → "keluhan"   (majority class fallback)
      - Sentiment → "netral"  (safe fallback)
    """

    INTENT_FALLBACK   = "keluhan"
    SENTIMENT_FALLBACK = "netral"

    def fit(self, texts, labels):
        # Rule-based tidak perlu training; simpan task dari label
        unique = set(labels)
        self._is_sentiment = "positif" in unique or "negatif" in unique
        return self

    def predict(self, texts):
        results = []
        for raw_text in texts:
            text = preprocess(raw_text)

            # Sarcasm detection → paksa negatif/keluhan
            if detect_sarcasm(text):
                if self._is_sentiment:
                    results.append("negatif")
                else:
                    results.append("keluhan")
                continue

            if self._is_sentiment:
                # Dapatkan intent hint terlebih dahulu untuk rule_sentiment
                intent_hint = rule_intent(text) or ""
                pred = rule_sentiment(text, intent_hint)
                results.append(pred if pred is not None else self.SENTIMENT_FALLBACK)
            else:
                pred = rule_intent(text)
                results.append(pred if pred is not None else self.INTENT_FALLBACK)
        return results


class MLOnlyClassifier:
    """
    Komponen B: ML Only.
    TF-IDF + Multinomial Naive Bayes tanpa rule-based sama sekali.
    """

    def __init__(self):
        self._pipe = Pipeline([
            ("tfidf", TfidfVectorizer(
                ngram_range=(1, 2),
                sublinear_tf=True,
                min_df=1,
            )),
            ("clf", MultinomialNB(alpha=0.3)),
        ])

    def fit(self, texts, labels):
        processed = [preprocess(t) for t in texts]
        self._pipe.fit(processed, labels)
        return self

    def predict(self, texts):
        processed = [preprocess(t) for t in texts]
        return self._pipe.predict(processed).tolist()


class HybridClassifier:
    """
    Komponen C: Hybrid (Full System).
    Arsitektur:
      1. Sarcasm detection → langsung assign negatif / keluhan
      2. Rule-based keyword matching → assign jika ada match
      3. ML fallback → untuk semua yang tidak ter-cover rules
    """

    def __init__(self):
        self._ml = MLOnlyClassifier()

    def fit(self, texts, labels):
        unique = set(labels)
        self._is_sentiment = "positif" in unique or "negatif" in unique
        self._ml.fit(texts, labels)
        return self

    def predict(self, texts):
        results = []
        for raw_text in texts:
            text = preprocess(raw_text)

            # Layer 1: Sarcasm gate
            if detect_sarcasm(text):
                results.append("negatif" if self._is_sentiment else "keluhan")
                continue

            # Layer 2: Rule-based keyword
            if self._is_sentiment:
                intent_hint = rule_intent(text) or ""
                rule_pred = rule_sentiment(text, intent_hint)
            else:
                rule_pred = rule_intent(text)

            if rule_pred is not None:
                results.append(rule_pred)
                continue

            # Layer 3: ML fallback
            ml_pred = self._ml.predict([raw_text])[0]
            results.append(ml_pred)

        return results


class MLNoSarcasmClassifier:
    """
    Komponen D: ML Only + Sarcasm Detection (tanpa keyword rules).
    Isolasi kontribusi sarcasm detection secara spesifik.
    """

    def __init__(self):
        self._ml = MLOnlyClassifier()

    def fit(self, texts, labels):
        unique = set(labels)
        self._is_sentiment = "positif" in unique or "negatif" in unique
        self._ml.fit(texts, labels)
        return self

    def predict(self, texts):
        results = []
        for raw_text in texts:
            text = preprocess(raw_text)
            if detect_sarcasm(text):
                results.append("negatif" if self._is_sentiment else "keluhan")
                continue
            ml_pred = self._ml.predict([raw_text])[0]
            results.append(ml_pred)
        return results


# ================================================================
# ABLATION EVALUATION
# ================================================================

@dataclass
class FoldResult:
    accuracy:  float
    precision: float
    recall:    float
    f1:        float


@dataclass
class AblationResult:
    variant_name: str
    task: str
    folds: list = field(default_factory=list)
    accuracy_mean:  float = 0.0
    accuracy_std:   float = 0.0
    precision_mean: float = 0.0
    precision_std:  float = 0.0
    recall_mean:    float = 0.0
    recall_std:     float = 0.0
    f1_mean:        float = 0.0
    f1_std:         float = 0.0
    classification_report_last_fold: str = ""

    def compute_stats(self):
        self.accuracy_mean  = float(np.mean([f.accuracy  for f in self.folds]))
        self.accuracy_std   = float(np.std( [f.accuracy  for f in self.folds]))
        self.precision_mean = float(np.mean([f.precision for f in self.folds]))
        self.precision_std  = float(np.std( [f.precision for f in self.folds]))
        self.recall_mean    = float(np.mean([f.recall    for f in self.folds]))
        self.recall_std     = float(np.std( [f.recall    for f in self.folds]))
        self.f1_mean        = float(np.mean([f.f1        for f in self.folds]))
        self.f1_std         = float(np.std( [f.f1        for f in self.folds]))


def evaluate_variant(
    clf_class,
    texts: list[str],
    labels: list[str],
    task: str,
    variant_name: str,
    n_folds: int = 10,
    seed: int = 42,
) -> AblationResult:
    """
    Evaluasi satu variant classifier menggunakan Stratified K-Fold CV.
    """
    result = AblationResult(variant_name=variant_name, task=task)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
    unique_labels = sorted(set(labels))

    texts_arr  = np.array(texts,  dtype=object)
    labels_arr = np.array(labels, dtype=object)

    print(f"    {'─'*50}")
    print(f"    {variant_name}")

    all_y_true, all_y_pred = [], []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(texts_arr, labels_arr)):
        X_train, X_val = texts_arr[train_idx].tolist(), texts_arr[val_idx].tolist()
        y_train, y_val = labels_arr[train_idx].tolist(), labels_arr[val_idx].tolist()

        clf = clf_class()
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_val)

        acc  = accuracy_score(y_val, y_pred)
        prec = precision_score(y_val, y_pred, average="weighted", zero_division=0)
        rec  = recall_score(y_val, y_pred, average="weighted", zero_division=0)
        f1   = f1_score(y_val, y_pred, average="weighted", zero_division=0)

        result.folds.append(FoldResult(acc, prec, rec, f1))
        all_y_true.extend(y_val)
        all_y_pred.extend(y_pred)

        sys.stdout.write(f"\r    Fold {fold_idx+1}/{n_folds} — acc={acc:.4f} f1={f1:.4f}    ")
        sys.stdout.flush()

    print()  # newline after fold progress

    result.compute_stats()
    result.classification_report_last_fold = classification_report(
        all_y_true, all_y_pred,
        target_names=unique_labels,
        zero_division=0,
    )
    return result


# ================================================================
# RULE COVERAGE ANALYSIS
# ================================================================

def analyze_rule_coverage(texts: list[str], labels: list[str], task: str) -> dict:
    """
    Analisis seberapa banyak teks yang ter-cover rule-based
    vs harus di-fallback ke ML.
    """
    covered_correct = 0
    covered_wrong   = 0
    not_covered     = 0
    sarcasm_detected = 0

    is_sentiment = "positif" in labels or "negatif" in labels

    for text, true_label in zip(texts, labels):
        proc = preprocess(text)

        if detect_sarcasm(proc):
            sarcasm_detected += 1
            pred = "negatif" if is_sentiment else "keluhan"
            if pred == true_label:
                covered_correct += 1
            else:
                covered_wrong += 1
            continue

        if is_sentiment:
            hint = rule_intent(proc) or ""
            pred = rule_sentiment(proc, hint)
        else:
            pred = rule_intent(proc)

        if pred is None:
            not_covered += 1
        elif pred == true_label:
            covered_correct += 1
        else:
            covered_wrong += 1

    total = len(texts)
    covered = covered_correct + covered_wrong
    return {
        "total": total,
        "rule_covered": covered,
        "rule_coverage_pct": covered / total * 100,
        "rule_correct": covered_correct,
        "rule_precision_when_covered": covered_correct / covered * 100 if covered > 0 else 0,
        "ml_fallback": not_covered,
        "ml_fallback_pct": not_covered / total * 100,
        "sarcasm_detected": sarcasm_detected,
        "sarcasm_pct": sarcasm_detected / total * 100,
    }


# ================================================================
# REPORT PRINTING
# ================================================================

def print_ablation_table(results: list[AblationResult], task: str):
    """Cetak tabel perbandingan ablation study."""
    print(f"\n{'═'*80}")
    print(f"  ABLATION STUDY — {task.upper()}")
    print(f"{'═'*80}")
    hdr = f"  {'Variant':<35} {'Accuracy':>10} {'Precision':>11} {'Recall':>8} {'F1':>8}"
    print(hdr)
    print(f"  {'─'*35} {'─'*10} {'─'*11} {'─'*8} {'─'*8}")
    for r in results:
        print(
            f"  {r.variant_name:<35} "
            f"{r.accuracy_mean:.4f}±{r.accuracy_std:.4f}  "
            f"{r.precision_mean:.4f}±{r.precision_std:.4f}  "
            f"{r.recall_mean:.4f}  "
            f"{r.f1_mean:.4f}"
        )
    print(f"{'═'*80}")

    # Contribution delta vs ML Only
    ml_only = next((r for r in results if "ML Only" in r.variant_name), None)
    hybrid  = next((r for r in results if "Hybrid" in r.variant_name), None)
    if ml_only and hybrid:
        delta_f1 = hybrid.f1_mean - ml_only.f1_mean
        delta_acc = hybrid.accuracy_mean - ml_only.accuracy_mean
        print(f"\n  ΔF1 (Hybrid vs ML Only)      : {delta_f1:+.4f}")
        print(f"  ΔAccuracy (Hybrid vs ML Only): {delta_acc:+.4f}")


def print_coverage(coverage: dict, task: str):
    print(f"\n  RULE COVERAGE ANALYSIS — {task.upper()}")
    print(f"  {'─'*50}")
    print(f"  Total samples          : {coverage['total']}")
    print(f"  Rule-covered           : {coverage['rule_covered']} ({coverage['rule_coverage_pct']:.1f}%)")
    print(f"  Rule precision (covered): {coverage['rule_precision_when_covered']:.1f}%")
    print(f"  ML fallback            : {coverage['ml_fallback']} ({coverage['ml_fallback_pct']:.1f}%)")
    print(f"  Sarcasm detected       : {coverage['sarcasm_detected']} ({coverage['sarcasm_pct']:.1f}%)")


def save_results(
    sentiment_results: list[AblationResult],
    intent_results: list[AblationResult],
    sent_coverage: dict,
    intent_coverage: dict,
    output_path: str,
):
    """Simpan hasil ke JSON (format siap paper)."""

    def result_to_dict(r: AblationResult) -> dict:
        return {
            "variant": r.variant_name,
            "task": r.task,
            "accuracy":  {"mean": round(r.accuracy_mean,  4), "std": round(r.accuracy_std,  4)},
            "precision": {"mean": round(r.precision_mean, 4), "std": round(r.precision_std, 4)},
            "recall":    {"mean": round(r.recall_mean,    4), "std": round(r.recall_std,    4)},
            "f1":        {"mean": round(r.f1_mean,        4), "std": round(r.f1_std,        4)},
            "classification_report": r.classification_report_last_fold,
        }

    output = {
        "sentiment": {
            "results":  [result_to_dict(r) for r in sentiment_results],
            "coverage": sent_coverage,
        },
        "intent": {
            "results":  [result_to_dict(r) for r in intent_results],
            "coverage": intent_coverage,
        },
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n[OK] Results saved → {output_path}")


def save_paper_table(
    sentiment_results: list[AblationResult],
    intent_results: list[AblationResult],
    output_path: str,
):
    """Simpan ringkasan tabel siap-paste ke paper (tanpa classification report)."""
    rows = []
    for r in sentiment_results + intent_results:
        rows.append({
            "task":       r.task,
            "variant":    r.variant_name,
            "accuracy":   f"{r.accuracy_mean:.4f} ± {r.accuracy_std:.4f}",
            "precision":  f"{r.precision_mean:.4f} ± {r.precision_std:.4f}",
            "recall":     f"{r.recall_mean:.4f} ± {r.recall_std:.4f}",
            "f1":         f"{r.f1_mean:.4f} ± {r.f1_std:.4f}",
        })
    with open(output_path, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"[OK] Paper table saved → {output_path}")


# ================================================================
# MAIN
# ================================================================

VARIANTS = [
    ("Rule-Based Only",           RuleOnlyClassifier),
    ("ML Only (TF-IDF + MNB)",    MLOnlyClassifier),
    ("ML + Sarcasm Detection",    MLNoSarcasmClassifier),
    ("Hybrid (Full System)",      HybridClassifier),
]


def run_ablation(
    task: str,
    texts: list[str],
    labels: list[str],
    n_folds: int = 10,
    seed: int = 42,
) -> list[AblationResult]:
    print(f"\n{'═'*60}")
    print(f"  Running ablation — {task.upper()} ({len(texts)} samples, {n_folds}-fold CV)")
    print(f"{'═'*60}")
    results = []
    for name, clf_class in VARIANTS:
        r = evaluate_variant(clf_class, texts, labels, task, name, n_folds, seed)
        results.append(r)
        print(f"    → acc={r.accuracy_mean:.4f}±{r.accuracy_std:.4f}  "
              f"f1={r.f1_mean:.4f}±{r.f1_std:.4f}")
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Ablation Study — Aspiralytica Hybrid Classifier"
    )
    parser.add_argument("--folds",   type=int, default=10,  help="K for Stratified K-Fold (default: 10)")
    parser.add_argument("--seed",    type=int, default=42,  help="Random seed (default: 42)")
    parser.add_argument("--output",  type=str, default="ml/evaluation/ablation_results.json")
    parser.add_argument("--table",   type=str, default="ml/evaluation/ablation_table.json")
    parser.add_argument("--task",    type=str, default="both",
                        choices=["sentiment", "intent", "both"],
                        help="Task to run (default: both)")
    args = parser.parse_args()

    print("\n" + "═"*60)
    print("  ASPIRALYTICA — ABLATION STUDY")
    print(f"  Folds: {args.folds} | Seed: {args.seed}")
    print("═"*60)

    sentiment_results, intent_results = [], []
    sent_coverage, intent_coverage = {}, {}

    if args.task in ("sentiment", "both"):
        sent_texts  = SENTIMENT_DATA["texts"]
        sent_labels = SENTIMENT_DATA["labels"]
        print(f"\n[INFO] Sentiment dataset: {len(sent_texts)} samples, "
              f"classes: {sorted(set(sent_labels))}")
        sent_coverage     = analyze_rule_coverage(sent_texts, sent_labels, "sentiment")
        print_coverage(sent_coverage, "sentiment")
        sentiment_results = run_ablation("sentiment", sent_texts, sent_labels, args.folds, args.seed)
        print_ablation_table(sentiment_results, "sentiment")

    if args.task in ("intent", "both"):
        int_texts  = INTENT_DATA["texts"]
        int_labels = INTENT_DATA["labels"]
        print(f"\n[INFO] Intent dataset: {len(int_texts)} samples, "
              f"classes: {sorted(set(int_labels))}")
        intent_coverage = analyze_rule_coverage(int_texts, int_labels, "intent")
        print_coverage(intent_coverage, "intent")
        intent_results  = run_ablation("intent", int_texts, int_labels, args.folds, args.seed)
        print_ablation_table(intent_results, "intent")

    # ── Save ───────────────────────────────────────────────────────
    save_results(sentiment_results, intent_results,
                 sent_coverage, intent_coverage, args.output)
    save_paper_table(sentiment_results, intent_results, args.table)

    print("\n[DONE] Ablation study complete.")


if __name__ == "__main__":
    main()