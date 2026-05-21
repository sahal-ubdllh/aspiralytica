# backend/ml/evaluate.py
# ================================================================
# MODEL EVALUATION — Complete for Thesis / SINTA Paper
# ================================================================
# Produces:
#   1. Confusion Matrix (PNG image)
#   2. Classification Report (per-class table)
#   3. K-Fold Cross Validation (10-fold)
#   4. Model Comparison (NB vs SVM vs DT vs RF vs LR)
#   5. Learning Curve
#   6. Full Report (.txt and .json)
#
# Usage:
#   cd backend
#   python -m ml.evaluate
#
# Output saved to: ml/evaluation/
# ================================================================

import os
import json
import warnings
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (no GUI required)
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    learning_curve,
    train_test_split,
)
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    ConfusionMatrixDisplay,
)

from ml.data import INTENT_DATA, SENTIMENT_DATA
from ml.preprocessor import preprocess_batch

from ml.data import INTENT_DATA, SENTIMENT_DATA

print("SENTIMENT TEXTS :", len(SENTIMENT_DATA["texts"]))
print("SENTIMENT LABELS:", len(SENTIMENT_DATA["labels"]))

print("INTENT TEXTS :", len(INTENT_DATA["texts"]))
print("INTENT LABELS:", len(INTENT_DATA["labels"]))

warnings.filterwarnings("ignore")

# ── Output directory ─────────────────────────────────────────────
EVAL_DIR = os.path.join(os.path.dirname(__file__), "evaluation")
os.makedirs(EVAL_DIR, exist_ok=True)

# ── Consistent colors for plots ──────────────────────────────────
COLORS = {
    "primary":  "#7C3AED",
    "success":  "#10B981",
    "warning":  "#F59E0B",
    "danger":   "#EF4444",
    "info":     "#3B82F6",
    "gray":     "#6B7280",
}


# ================================================================
# HELPER: Build Pipelines
# ================================================================

def make_nb_pipeline(alpha: float = 0.3) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf",   MultinomialNB(alpha=alpha)),
    ])

def make_svm_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf",   LinearSVC(C=1.0, max_iter=2000)),
    ])

def make_dt_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf",   DecisionTreeClassifier(random_state=42)),
    ])

def make_rf_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf",   RandomForestClassifier(n_estimators=100, random_state=42)),
    ])

def make_lr_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
        ("clf",   LogisticRegression(max_iter=1000, random_state=42)),
    ])


# ================================================================
# 1. CONFUSION MATRIX
# ================================================================

def plot_confusion_matrix(
    y_true: list,
    y_pred: list,
    title: str,
    filename: str,
    label_map: dict = None,
) -> None:
    """
    Generate and save a confusion matrix as a PNG image.
    Useful for thesis / paper reports.

    label_map: optional dict mapping raw data labels → display labels
               e.g. {"positif": "positive", "negatif": "negative"}
               If None, raw labels are used as-is.
    """
    # Use the actual labels that exist in the data
    raw_labels = sorted(set(y_true))

    cm = confusion_matrix(y_true, y_pred, labels=raw_labels)

    # Translate labels for display if a mapping is provided
    display_labels = [label_map.get(l, l) for l in raw_labels] if label_map else raw_labels

    fig, ax = plt.subplots(figsize=(max(6, len(raw_labels) * 1.5), max(5, len(raw_labels) * 1.2)))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=display_labels)
    disp.plot(
        ax=ax,
        cmap="Purples",
        colorbar=True,
        xticks_rotation=30,
    )
    ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
    plt.tight_layout()

    path = os.path.join(EVAL_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Confusion matrix saved → {path}")


# ================================================================
# 2. K-FOLD CROSS VALIDATION
# ================================================================

def cross_validate_model(
    pipeline: Pipeline,
    X: list,
    y: list,
    model_name: str,
    k: int = 10,
) -> dict:
    """
    Evaluate a model using Stratified K-Fold Cross Validation.

    Returns a dict containing all metrics per fold.
    """
    kfold = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)

    acc  = cross_val_score(pipeline, X, y, cv=kfold, scoring="accuracy")
    prec = cross_val_score(pipeline, X, y, cv=kfold, scoring="precision_weighted")
    rec  = cross_val_score(pipeline, X, y, cv=kfold, scoring="recall_weighted")
    f1   = cross_val_score(pipeline, X, y, cv=kfold, scoring="f1_weighted")

    result = {
        "model":     model_name,
        "accuracy":  {"mean": round(float(acc.mean()), 4),  "std": round(float(acc.std()), 4),  "all": acc.tolist()},
        "precision": {"mean": round(float(prec.mean()), 4), "std": round(float(prec.std()), 4), "all": prec.tolist()},
        "recall":    {"mean": round(float(rec.mean()), 4),  "std": round(float(rec.std()), 4),  "all": rec.tolist()},
        "f1_score":  {"mean": round(float(f1.mean()), 4),   "std": round(float(f1.std()), 4),   "all": f1.tolist()},
    }

    print(f"\n  Model: {model_name} ({k}-Fold CV)")
    print(f"  Accuracy  : {acc.mean():.4f} ± {acc.std():.4f}")
    print(f"  Precision : {prec.mean():.4f} ± {prec.std():.4f}")
    print(f"  Recall    : {rec.mean():.4f} ± {rec.std():.4f}")
    print(f"  F1-Score  : {f1.mean():.4f} ± {f1.std():.4f}")

    return result


# ================================================================
# 3. MODEL COMPARISON (BASELINE)
# ================================================================

def compare_models(
    X: list,
    y: list,
    dataset_name: str,
    k: int = 10,
) -> list[dict]:
    """
    Compare Naive Bayes vs SVM vs Decision Tree vs Random Forest vs LR.
    Produces a comparison table and bar chart.
    """
    models = [
        ("Naive Bayes (Proposed)", make_nb_pipeline()),
        ("SVM",                   make_svm_pipeline()),
        ("Decision Tree",         make_dt_pipeline()),
        ("Random Forest",         make_rf_pipeline()),
        ("Logistic Regression",   make_lr_pipeline()),
    ]

    print(f"\n{'─'*55}")
    print(f"  MODEL COMPARISON — {dataset_name}")
    print(f"{'─'*55}")

    results = []
    for name, pipeline in models:
        r = cross_validate_model(pipeline, X, y, name, k=k)
        results.append(r)

    # ── Plot bar chart comparison ────────────────────────────────
    model_names = [r["model"].replace(" (Proposed)", "\n(Proposed)") for r in results]
    metrics_plot = {
        "Accuracy":  [r["accuracy"]["mean"]  for r in results],
        "Precision": [r["precision"]["mean"] for r in results],
        "Recall":    [r["recall"]["mean"]    for r in results],
        "F1-Score":  [r["f1_score"]["mean"]  for r in results],
    }
    metric_colors = [COLORS["primary"], COLORS["success"], COLORS["warning"], COLORS["danger"]]

    x     = np.arange(len(model_names))
    width = 0.18
    fig, ax = plt.subplots(figsize=(13, 6))

    for i, (metric, values) in enumerate(metrics_plot.items()):
        bars = ax.bar(
            x + i * width, values, width,
            label=metric,
            color=metric_colors[i],
            alpha=0.85,
        )
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{val:.3f}",
                ha="center", va="bottom", fontsize=7.5,
            )

    ax.set_xlabel("Model", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_title(
        f"Classification Model Comparison — {dataset_name}",
        fontsize=13, fontweight="bold",
    )
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(model_names, fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    fname = f"comparison_{dataset_name.lower()}.png"
    path  = os.path.join(EVAL_DIR, fname)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  📊 Comparison chart saved → {path}")

    return results


# ================================================================
# 4. LEARNING CURVE
# ================================================================

def plot_learning_curve(
    pipeline: Pipeline,
    X: list,
    y: list,
    title: str,
    filename: str,
    k: int = 5,
) -> None:
    """
    Generate a learning curve to demonstrate the model is not overfitting.
    Useful for papers — shows performance as training data size increases.
    """
    X_arr = np.array(X)
    y_arr = np.array(y)

    train_sizes, train_scores, val_scores = learning_curve(
        pipeline, X_arr, y_arr,
        cv=StratifiedKFold(n_splits=k, shuffle=True, random_state=42),
        scoring="f1_weighted",
        train_sizes=np.linspace(0.1, 1.0, 10),
        n_jobs=-1,
    )

    train_mean = train_scores.mean(axis=1)
    train_std  = train_scores.std(axis=1)
    val_mean   = val_scores.mean(axis=1)
    val_std    = val_scores.std(axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(train_sizes, train_mean, "o-", color=COLORS["primary"], label="Training Score")
    ax.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.15, color=COLORS["primary"])
    ax.plot(train_sizes, val_mean, "s-", color=COLORS["success"], label="Validation Score")
    ax.fill_between(train_sizes, val_mean - val_std, val_mean + val_std, alpha=0.15, color=COLORS["success"])

    ax.set_xlabel("Number of Training Samples", fontsize=11)
    ax.set_ylabel("F1-Score (weighted)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(alpha=0.3)
    ax.set_ylim(0, 1.1)
    plt.tight_layout()

    path = os.path.join(EVAL_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Learning curve saved → {path}")


# ================================================================
# 5. DATASET DISTRIBUTION
# ================================================================

def plot_dataset_distribution(
    labels: list,
    title: str,
    filename: str,
) -> None:
    """
    Pie chart of dataset class distribution.
    Useful for the methodology / dataset section of a paper.
    """
    unique, counts = np.unique(labels, return_counts=True)
    colors_list = [
        COLORS["primary"], COLORS["success"], COLORS["warning"],
        COLORS["danger"], COLORS["info"], COLORS["gray"],
    ][:len(unique)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Pie chart
    wedges, texts, autotexts = ax1.pie(
        counts, labels=unique, autopct="%1.1f%%",
        colors=colors_list, startangle=90,
        pctdistance=0.82,
    )
    for t in autotexts:
        t.set_fontsize(10)
    ax1.set_title(f"{title} Distribution", fontsize=12, fontweight="bold")

    # Bar chart
    bars = ax2.barh(unique, counts, color=colors_list, alpha=0.85)
    for bar, count in zip(bars, counts):
        ax2.text(
            bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{count} ({count/sum(counts)*100:.1f}%)",
            va="center", fontsize=10,
        )
    ax2.set_xlabel("Number of Samples", fontsize=11)
    ax2.set_title(f"Sample Count per Class — {title}", fontsize=12, fontweight="bold")
    ax2.grid(axis="x", alpha=0.3)
    plt.tight_layout()

    path = os.path.join(EVAL_DIR, filename)
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Dataset distribution saved → {path}")


# ================================================================
# 6. DETAILED CLASSIFICATION REPORT
# ================================================================

def full_classification_report(
    pipeline: Pipeline,
    X: list,
    y: list,
    dataset_name: str,
    label_map: dict = None,
    test_size: float = 0.2,
) -> str:
    """
    Split data 80:20, train, then generate a full classification report.

    label_map: optional dict mapping raw data labels -> English display names
               e.g. {"positif": "positive"}. If None, raw labels are used.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=42
    )
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    raw_labels     = sorted(set(y))
    display_labels = [label_map.get(l, l) for l in raw_labels] if label_map else raw_labels

    report = classification_report(
        y_test, y_pred,
        labels=raw_labels,
        target_names=display_labels,
        digits=4,
    )
    acc = accuracy_score(y_test, y_pred)

    print(f"\n  Classification Report — {dataset_name} (80:20 split)")
    print(f"  Accuracy: {acc:.4f}")
    print(report)

    return report


# ================================================================
# MAIN — Run all evaluations
# ================================================================

def evaluate():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'#'*55}")
    print(f"  ASPIRALYTICA — FULL EVALUATION")
    print(f"  {timestamp}")
    print(f"{'#'*55}")

    all_results = {"generated_at": timestamp}

    # ── Prepare data ─────────────────────────────────────────────
    print("\n[•] Processing datasets...")
    X_sent   = preprocess_batch(SENTIMENT_DATA["texts"])
    y_sent   = SENTIMENT_DATA["labels"]
    X_intent = preprocess_batch(INTENT_DATA["texts"])
    y_intent = INTENT_DATA["labels"]

    # Label maps: raw data value -> English display name
    sent_label_map = {
        "positif":  "positive",
        "negatif":  "negative",
        "netral":   "neutral",
    }
    intent_label_map = {
        "keluhan":    "complaint",
        "permintaan": "request",
        "saran":      "suggestion",
        "apresiasi":  "appreciation",
        "darurat":    "emergency",
    }

    print(f"  Sentiment Dataset : {len(X_sent)} samples")
    print(f"  Intent Dataset    : {len(X_intent)} samples")

    # ── 1. Dataset distribution ──────────────────────────────────
    print("\n[1/6] Dataset Distribution...")
    plot_dataset_distribution(y_sent,   "Sentiment", "dist_sentiment.png")
    plot_dataset_distribution(y_intent, "Intent",    "dist_intent.png")

    # ── 2. K-Fold Cross Validation (main model: Naive Bayes) ─────
    print("\n[2/6] K-Fold Cross Validation (Naive Bayes)...")
    nb_sent_cv   = cross_validate_model(make_nb_pipeline(), X_sent,   y_sent,   "Naive Bayes Sentiment")
    nb_intent_cv = cross_validate_model(make_nb_pipeline(), X_intent, y_intent, "Naive Bayes Intent")
    all_results["kfold_naive_bayes"] = {
        "sentiment": nb_sent_cv,
        "intent":    nb_intent_cv,
    }

    # ── 3. Confusion Matrix ──────────────────────────────────────
    print("\n[3/6] Confusion Matrix...")
    # Train on all data for confusion matrix
    pipe_sent = make_nb_pipeline()
    pipe_sent.fit(X_sent, y_sent)
    plot_confusion_matrix(
        y_sent, pipe_sent.predict(X_sent),
        "Confusion Matrix — Sentiment Classification (Naive Bayes)",
        "cm_sentiment.png",
        label_map=sent_label_map,
    )

    pipe_intent = make_nb_pipeline()
    pipe_intent.fit(X_intent, y_intent)
    plot_confusion_matrix(
        y_intent, pipe_intent.predict(X_intent),
        "Confusion Matrix — Intent Classification (Naive Bayes)",
        "cm_intent.png",
        label_map=intent_label_map,
    )

    # ── 4. Classification Report (80:20 split) ───────────────────
    print("\n[4/6] Classification Report (80:20 split)...")
    report_sent   = full_classification_report(
        make_nb_pipeline(), X_sent,   y_sent,   "Sentiment", label_map=sent_label_map
    )
    report_intent = full_classification_report(
        make_nb_pipeline(), X_intent, y_intent, "Intent",    label_map=intent_label_map
    )

    # ── 5. Model comparison ──────────────────────────────────────
    print("\n[5/6] Model Comparison...")
    comp_sent   = compare_models(X_sent,   y_sent,   "Sentiment")
    comp_intent = compare_models(X_intent, y_intent, "Intent")
    all_results["model_comparison"] = {
        "sentiment": comp_sent,
        "intent":    comp_intent,
    }

    # ── 6. Learning Curve ────────────────────────────────────────
    print("\n[6/6] Learning Curve...")
    plot_learning_curve(
        make_nb_pipeline(), X_sent, y_sent,
        "Learning Curve — Sentiment Classification",
        "learning_curve_sentiment.png",
    )
    plot_learning_curve(
        make_nb_pipeline(), X_intent, y_intent,
        "Learning Curve — Intent Classification",
        "learning_curve_intent.png",
    )

    # ── Save all results to JSON ─────────────────────────────────
    json_path = os.path.join(EVAL_DIR, "evaluation_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n  ✅ JSON evaluation results → {json_path}")

    # ── Save text report ─────────────────────────────────────────
    report_path = os.path.join(EVAL_DIR, "evaluation_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"ASPIRALYTICA — EVALUATION REPORT\n")
        f.write(f"Generated: {timestamp}\n")
        f.write("=" * 55 + "\n\n")

        f.write("[ NAIVE BAYES MODEL — SENTIMENT ]\n")
        f.write(f"10-Fold CV Accuracy : {nb_sent_cv['accuracy']['mean']:.4f} ± {nb_sent_cv['accuracy']['std']:.4f}\n")
        f.write(f"10-Fold CV F1-Score : {nb_sent_cv['f1_score']['mean']:.4f} ± {nb_sent_cv['f1_score']['std']:.4f}\n")
        f.write("\nClassification Report (80:20 split):\n")
        f.write(report_sent)

        f.write("\n[ NAIVE BAYES MODEL — INTENT ]\n")
        f.write(f"10-Fold CV Accuracy : {nb_intent_cv['accuracy']['mean']:.4f} ± {nb_intent_cv['accuracy']['std']:.4f}\n")
        f.write(f"10-Fold CV F1-Score : {nb_intent_cv['f1_score']['mean']:.4f} ± {nb_intent_cv['f1_score']['std']:.4f}\n")
        f.write("\nClassification Report (80:20 split):\n")
        f.write(report_intent)

        f.write("\n[ MODEL COMPARISON — SENTIMENT ]\n")
        f.write(f"{'Model':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}\n")
        f.write("-" * 70 + "\n")
        for r in comp_sent:
            f.write(
                f"{r['model']:<30} "
                f"{r['accuracy']['mean']:>10.4f} "
                f"{r['precision']['mean']:>10.4f} "
                f"{r['recall']['mean']:>10.4f} "
                f"{r['f1_score']['mean']:>10.4f}\n"
            )

        f.write("\n[ MODEL COMPARISON — INTENT ]\n")
        f.write(f"{'Model':<30} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}\n")
        f.write("-" * 70 + "\n")
        for r in comp_intent:
            f.write(
                f"{r['model']:<30} "
                f"{r['accuracy']['mean']:>10.4f} "
                f"{r['precision']['mean']:>10.4f} "
                f"{r['recall']['mean']:>10.4f} "
                f"{r['f1_score']['mean']:>10.4f}\n"
            )

    print(f"  ✅ Text report → {report_path}")
    print(f"\n{'#'*55}")
    print(f"  EVALUATION COMPLETE")
    print(f"  Output saved to: {EVAL_DIR}/")
    print(f"{'#'*55}\n")

    # ── Output summary ───────────────────────────────────────────
    print("  📁 Generated files:")
    for fname in sorted(os.listdir(EVAL_DIR)):
        fsize = os.path.getsize(os.path.join(EVAL_DIR, fname))
        print(f"     {fname:<40} {fsize/1024:>6.1f} KB")


if __name__ == "__main__":
    evaluate()