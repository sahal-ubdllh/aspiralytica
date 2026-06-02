"""
evaluate_sarcasm.py — Aspiralytica Sarcasm Detection Evaluator
Run: python ml/evaluate_sarcasm.py
     python ml/evaluate_sarcasm.py --mode evaluate --data ml/evaluation/sarcasm_gt.json
     python ml/evaluate_sarcasm.py --mode annotate --input texts.txt
     python ml/evaluate_sarcasm.py --mode analyze   --data ml/evaluation/sarcasm_gt.json
"""

import argparse, json, sys, os
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE)):
    if p not in sys.path: sys.path.insert(0, p)

try:
    from ml.rules import (
        detect_sarcasm,
        _SARC_POSITIF_KUAT, _SARC_KONTRADIKSI, _SARC_KONTRADIKSI_INFORMAL,
        _SARC_KATA_NEG, _SARC_KATA_POS, _SARC_PENGUAT,
        _SARC_POSITIF_TANPA_PENGUAT, _SARC_MODERN_PHRASES, _SARC_EMOJI_POS_TOKENS,
    )
    from ml.preprocessor import preprocess
except ImportError:
    from rules import (
        detect_sarcasm,
        _SARC_POSITIF_KUAT, _SARC_KONTRADIKSI, _SARC_KONTRADIKSI_INFORMAL,
        _SARC_KATA_NEG, _SARC_KATA_POS, _SARC_PENGUAT,
        _SARC_POSITIF_TANPA_PENGUAT, _SARC_MODERN_PHRASES, _SARC_EMOJI_POS_TOKENS,
    )
    from preprocessor import preprocess


# ── Layer-aware sarcasm detector ─────────────────────────────────
def detect_with_layer(text: str):
    tl = text.lower()
    strong_pos  = [k for k in _SARC_POSITIF_KUAT if k in tl]
    contradict  = [k for k in _SARC_KONTRADIKSI if k in tl] + \
                  [k for k in _SARC_KONTRADIKSI_INFORMAL if k in tl]
    any_neg     = [k for k in _SARC_KATA_NEG if k in tl]
    penguat     = [k for k in _SARC_PENGUAT if k in tl]
    basic_pos   = [k for k in _SARC_KATA_POS if k in tl]
    explicit    = [k for k in _SARC_POSITIF_TANPA_PENGUAT if k in tl]
    modern      = [k for k in _SARC_MODERN_PHRASES if k in tl]
    emoji       = [k for k in _SARC_EMOJI_POS_TOKENS if k in tl]

    ev = {
        "strong_positive": strong_pos, "contrastive": list(set(contradict)),
        "negative_context": any_neg[:5], "intensifier": penguat,
        "basic_positive": basic_pos, "explicit_praise": explicit,
        "modern_phrases": modern, "emoji_tokens": emoji,
    }

    if strong_pos and contradict:  return True, "1a", ev
    if strong_pos and any_neg:     return True, "1b", ev
    if penguat and basic_pos and any_neg: return True, "2",  ev
    if explicit and any_neg:       return True, "3",  ev
    if modern:                     return True, "4",  ev
    if emoji and any_neg:          return True, "5",  ev
    return False, None, ev


# ── Ground truth dataset ─────────────────────────────────────────
DEMO_GT = [
    # TRUE POSITIVES — Layer 1a
    {"text": "bagus banget pelayanannya, padahal antri 3 jam ga dilayani",             "label": 1, "category": "Layer1a"},
    {"text": "luar biasa sekali penanganannya, tapi nyatanya sampah masih menumpuk",   "label": 1, "category": "Layer1a"},
    {"text": "mantap sekali kerjanya, padahal jalan rusak dari tahun lalu",            "label": 1, "category": "Layer1a"},
    {"text": "wah keren smart city nya, tapi aplikasi error mulu",                     "label": 1, "category": "Layer1a"},
    {"text": "hebat betul petugasnya, padahal ga pernah dateng",                       "label": 1, "category": "Layer1a"},
    # Layer 1b
    {"text": "bagus banget nih programnya, jalan berlubang makin parah",               "label": 1, "category": "Layer1b"},
    {"text": "keren banget pelayanan publiknya, got mampet ga ada yang beresin",       "label": 1, "category": "Layer1b"},
    {"text": "sangat kagum dengan inovasi ini, lampu jalan mati terus",                "label": 1, "category": "Layer1b"},
    {"text": "top banget nih instansinya, sampah numpuk ga diangkut",                  "label": 1, "category": "Layer1b"},
    # Layer 2
    {"text": "senang sekali lihat kondisi kota, rusak parah dari kemarin",             "label": 1, "category": "Layer2"},
    {"text": "bangga banget sama pemerintah, jalan berlubang lagi",                    "label": 1, "category": "Layer2"},
    {"text": "mantap beneran petugasnya, ga ada tindakan sama sekali",                 "label": 1, "category": "Layer2"},
    # Layer 3
    {"text": "salut deh sama kinerja dinas, masih rusak juga sampai sekarang",        "label": 1, "category": "Layer3"},
    {"text": "acungan jempol buat responsnya, bocor parah ga diperbaiki",              "label": 1, "category": "Layer3"},
    {"text": "good job min, sampah menggunung ga diangkut berhari-hari",               "label": 1, "category": "Layer3"},
    {"text": "well done petugasnya, got mampet udah seminggu",                         "label": 1, "category": "Layer3"},
    # Layer 4
    {"text": "smart city tapi server down terus gimana sih",                           "label": 1, "category": "Layer4"},
    {"text": "kota pintar tapi lampu jalan pada mati semua",                           "label": 1, "category": "Layer4"},
    {"text": "program unggulan tapi ga bisa diakses sama sekali",                      "label": 1, "category": "Layer4"},
    {"text": "pelayanan prima tapi antri 5 jam ga kelar-kelar",                        "label": 1, "category": "Layer4"},
    {"text": "terima kasih sudah membiarkan jalan ini rusak bertahun-tahun",           "label": 1, "category": "Layer4"},
    # Layer 5
    {"text": "jempol buat petugasnya, jalan rusak ga diperbaiki juga",                 "label": 1, "category": "Layer5"},
    {"text": "oke banget nih, drainase mampet terus bikin banjir",                     "label": 1, "category": "Layer5"},
    # Edge cases
    {"text": "luar biasa ya antreannya, 6 jam belum juga dilayani",                    "label": 1, "category": "edge_exclamation"},
    {"text": "wah hebat betul kotanya, got mampet, jalan rusak, lampu mati semua",    "label": 1, "category": "edge_enumeration"},
    {"text": "terima kasih banyak atas perhatiannya yang luar biasa, bertahun dibiarkan", "label": 1, "category": "edge_extended"},
    # FALSE POSITIVE TRAPS — bukan sarkasme
    {"text": "pelayanan sudah membaik, meski jalan di RW 3 masih berlubang",           "label": 0, "category": "FP_trap_genuine_mixed"},
    {"text": "terima kasih sudah merespons, tapi mohon juga perhatikan drainase",      "label": 0, "category": "FP_trap_polite_request"},
    {"text": "bagus programnya, cuma perlu ditingkatkan lagi konsistensinya",          "label": 0, "category": "FP_trap_constructive"},
    {"text": "mantap pelayanannya sudah membaik dari bulan lalu",                      "label": 0, "category": "FP_trap_genuine_positive"},
    {"text": "alhamdulillah jalan sudah diperbaiki meski masih ada sedikit lubang",    "label": 0, "category": "FP_trap_relief"},
    {"text": "bangga sama perkembangan kota walau masih banyak yang perlu dibenahi",   "label": 0, "category": "FP_trap_constructive"},
    # TRUE NEGATIVES
    {"text": "jalan di depan rumah rusak parah sudah berbulan-bulan mohon diperbaiki", "label": 0, "category": "TN_complaint"},
    {"text": "terima kasih pelayanan puskesmas sangat ramah dan cepat",                "label": 0, "category": "TN_appreciation"},
    {"text": "mohon segera pasang lampu jalan di gang kelapa yang gelap",              "label": 0, "category": "TN_request"},
    {"text": "ada kebakaran di pasar tolong segera kirim bantuan",                     "label": 0, "category": "TN_emergency"},
    {"text": "sebaiknya ada jadwal rutin pemeliharaan jalan setiap bulan",             "label": 0, "category": "TN_suggestion"},
    {"text": "sampah belum diangkut sudah 5 hari tolong segera diangkut",             "label": 0, "category": "TN_complaint"},
    {"text": "air PDAM tidak mengalir sudah 3 hari ini sangat mengganggu",             "label": 0, "category": "TN_complaint"},
]


# ── Metrics ───────────────────────────────────────────────────────
def compute_metrics(dataset):
    y_true, y_pred, texts, cats = [], [], [], []
    for item in dataset:
        proc = preprocess(item["text"])
        pred = 1 if detect_sarcasm(proc) else 0
        y_true.append(item["label"]); y_pred.append(pred)
        texts.append(item["text"]); cats.append(item.get("category", "?"))

    tp = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 1)
    tn = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 0)
    fn = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 0)
    n  = len(y_true)

    prec_s  = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec_s   = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_s    = 2*prec_s*rec_s/(prec_s+rec_s) if (prec_s+rec_s) > 0 else 0
    prec_n  = tn / (tn + fn) if (tn + fn) > 0 else 0
    rec_n   = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1_n    = 2*prec_n*rec_n/(prec_n+rec_n) if (prec_n+rec_n) > 0 else 0
    acc     = (tp + tn) / n
    macro_f1    = (f1_s + f1_n) / 2
    n_s = sum(1 for y in y_true if y == 1)
    n_n = sum(1 for y in y_true if y == 0)
    weighted_f1 = (f1_s*n_s + f1_n*n_n) / n

    fp_cases, fn_cases = [], []
    layer_tp, layer_all = defaultdict(int), defaultdict(int)

    for yt, yp, txt, cat in zip(y_true, y_pred, texts, cats):
        proc = preprocess(txt)
        is_s, layer, ev = detect_with_layer(proc)
        if is_s and layer:
            layer_all[layer] += 1
            if yt == 1: layer_tp[layer] += 1
        if yt == 0 and yp == 1:
            fp_cases.append({"text": txt, "category": cat, "fired_layer": layer,
                             "pos_hits": ev.get("strong_positive", []) or ev.get("basic_positive", []),
                             "neg_hits": ev.get("negative_context", [])[:3]})
        elif yt == 1 and yp == 0:
            fn_cases.append({"text": txt, "category": cat})

    layer_prec = {l: round(layer_tp[l]/layer_all[l], 4) for l in layer_all if layer_all[l] > 0}

    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn, "n": n,
        "precision_sarcasm": round(prec_s, 4), "recall_sarcasm": round(rec_s, 4),
        "f1_sarcasm": round(f1_s, 4), "precision_nonsarcasm": round(prec_n, 4),
        "recall_nonsarcasm": round(rec_n, 4), "f1_nonsarcasm": round(f1_n, 4),
        "accuracy": round(acc, 4), "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "layer_distribution": dict(layer_all), "layer_precision": layer_prec,
        "fp_cases": fp_cases, "fn_cases": fn_cases,
    }


# ── Print report ─────────────────────────────────────────────────
def print_report(m):
    sep = "═" * 65
    print(f"\n{sep}")
    print("  SARCASM DETECTION — EVALUATION REPORT")
    print(sep)
    n_s = m["tp"] + m["fn"]; n_n = m["tn"] + m["fp"]
    print(f"\n  Dataset : {m['n']} samples ({n_s} sarcasm, {n_n} non-sarcasm)")
    print(f"\n  Confusion Matrix:")
    print(f"  {'':22} Pred SARCASM  Pred NON")
    print(f"  {'True SARCASM':22} {m['tp']:>12}  {m['fn']:>8}")
    print(f"  {'True NON-SARCASM':22} {m['fp']:>12}  {m['tn']:>8}")
    print(f"\n  {'─'*63}")
    print(f"  {'Class':<24} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Support':>8}")
    print(f"  {'─'*63}")
    print(f"  {'Sarcasm':<24} {m['precision_sarcasm']:>10.4f} {m['recall_sarcasm']:>8.4f} "
          f"{m['f1_sarcasm']:>8.4f} {n_s:>8}")
    print(f"  {'Non-Sarcasm':<24} {m['precision_nonsarcasm']:>10.4f} {m['recall_nonsarcasm']:>8.4f} "
          f"{m['f1_nonsarcasm']:>8.4f} {n_n:>8}")
    print(f"  {'─'*63}")
    print(f"  {'Accuracy':<24} {'':>10} {'':>8} {m['accuracy']:>8.4f} {m['n']:>8}")
    print(f"  {'Macro F1':<24} {'':>10} {'':>8} {m['macro_f1']:>8.4f}")
    print(f"  {'Weighted F1':<24} {'':>10} {'':>8} {m['weighted_f1']:>8.4f}")

    layer_names = {
        "1a": "Layer 1a: Strong pos + Contrastive marker",
        "1b": "Layer 1b: Strong pos + Any negative",
        "2":  "Layer 2:  Basic pos + Intensifier + Neg",
        "3":  "Layer 3:  Explicit praise + Negative",
        "4":  "Layer 4:  Modern sarcasm phrases",
        "5":  "Layer 5:  Emoji token + Negative",
    }
    print(f"\n  LAYER DISTRIBUTION & PRECISION")
    print(f"  {'─'*60}")
    for lyr, cnt in sorted(m["layer_distribution"].items()):
        prec = m["layer_precision"].get(lyr, 0)
        bar  = "█" * int(prec * 10)
        name = layer_names.get(lyr, f"Layer {lyr}")
        print(f"  {name:<44} fired={cnt:>2}  prec={prec:.2f}  {bar}")

    print(f"\n  FALSE POSITIVES ({len(m['fp_cases'])}): predicted sarcasm, actually not")
    for i, c in enumerate(m["fp_cases"], 1):
        print(f"  FP{i:02d} [{c['category']}] Layer={c['fired_layer']}")
        print(f"       {c['text'][:75]}")
        print(f"       pos_hits={c['pos_hits'][:2]}  neg_hits={c['neg_hits'][:2]}")

    print(f"\n  FALSE NEGATIVES ({len(m['fn_cases'])}): sarcasm not detected")
    for i, c in enumerate(m["fn_cases"], 1):
        print(f"  FN{i:02d} [{c['category']}]")
        print(f"       {c['text'][:75]}")
    print(f"\n{sep}\n")


# ── Annotation tool ───────────────────────────────────────────────
GUIDELINE = """
╔══════════════════════════════════════════════════════════════╗
║  PANDUAN ANOTASI SARKASME — ASPIRALYTICA                     ║
║  Domain: Laporan warga berbahasa Indonesia informal           ║
╠══════════════════════════════════════════════════════════════╣
║  LABEL 1 = SARKASME                                          ║
║  Penulis menggunakan ekspresi POSITIF permukaan untuk        ║
║  menyampaikan makna NEGATIF (kritik/keluhan terselubung).    ║
║                                                              ║
║  Uji: "Apakah penulis benar-benar memuji, atau mengkritik    ║
║       via pujian?"                                           ║
║                                                              ║
║  LABEL 0 = BUKAN SARKASME — termasuk:                        ║
║  - Keluhan murni (tanpa pujian)                              ║
║  - Apresiasi tulus (positif tanpa konteks negatif)           ║
║  - Pujian + permintaan/saran konstruktif                     ║
║  - Laporan evaluatif yang seimbang dan jujur                 ║
║                                                              ║
║  POLA SARKASME UMUM DI LAPORAN WARGA:                        ║
║  1. "bagus banget/keren banget" + padahal + masalah          ║
║  2. "smart city/kota pintar" + masalah teknis                ║
║  3. "terima kasih sudah membiarkan/mengabaikan..."           ║
║  4. Ekspresi positif kuat + enumerasi masalah                ║
║  5. "salut/good job/well done" + masalah yang tidak beres    ║
║                                                              ║
║  TEKAN: [1] Sarkasme | [0] Bukan sarkasme | [s] Skip | [q] Keluar ║
╚══════════════════════════════════════════════════════════════╝
"""

def interactive_annotate(candidates, output_path):
    print(GUIDELINE)
    results, skipped = [], []
    for idx, text in enumerate(candidates):
        proc = preprocess(text)
        is_s, layer, ev = detect_with_layer(proc)
        print(f"\n[{idx+1}/{len(candidates)}]")
        print(f"  Teks    : {text}")
        print(f"  Sys pred: {'SARKASME' if is_s else 'bukan'} (Layer {layer or '-'})")
        if is_s:
            pos = ev.get("strong_positive", []) or ev.get("basic_positive", [])
            neg = ev.get("negative_context", [])
            if pos: print(f"  Pos hits: {pos[:3]}")
            if neg: print(f"  Neg hits: {neg[:3]}")
        while True:
            ans = input("  Label → [1/0/s/q]: ").strip().lower()
            if ans in ("1","0","s","q"): break
        if ans == "q": print(f"Dihentikan di item {idx+1}."); break
        elif ans == "s": skipped.append(text); continue
        else:
            cat = input("  Kategori (Enter=skip): ").strip() or ("sarcasm" if ans=="1" else "non_sarcasm")
            note = input("  Catatan (Enter=skip): ").strip()
            results.append({"text": text, "label": int(ans), "category": cat,
                            "note": note, "sys_pred": int(is_s),
                            "sys_layer": layer, "agree": int(is_s) == int(ans)})
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    n_agree = sum(1 for r in results if r["agree"])
    print(f"\n[DONE] Annotated={len(results)} | Skipped={len(skipped)}")
    if results:
        print(f"       System-Annotator agreement: {n_agree}/{len(results)} "
              f"({n_agree/len(results)*100:.1f}%)")
    print(f"       Saved → {output_path}")


# ── Main ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",   default="demo",
                        choices=["demo","evaluate","analyze","annotate"])
    parser.add_argument("--data",   default=None)
    parser.add_argument("--input",  default=None)
    parser.add_argument("--output", default="ml/evaluation/sarcasm_eval_results.json")
    args = parser.parse_args()

    if args.mode in ("demo", "evaluate", "analyze"):
        dataset = DEMO_GT
        if args.mode != "demo":
            if not args.data: print("[ERROR] --data required"); sys.exit(1)
            with open(args.data, encoding="utf-8") as f: dataset = json.load(f)
        m = compute_metrics(dataset)
        print_report(m)
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        out = {k: v for k, v in m.items() if k not in ("fp_cases","fn_cases")}
        out["false_positives"] = m["fp_cases"]
        out["false_negatives"] = m["fn_cases"]
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        print(f"[OK] Saved → {args.output}")

    elif args.mode == "annotate":
        if not args.input: print("[ERROR] --input required"); sys.exit(1)
        with open(args.input, encoding="utf-8") as f: raw = f.read().strip()
        candidates = json.loads(raw) if raw.startswith("[") else \
                     [l.strip() for l in raw.split("\n") if l.strip()]
        if isinstance(candidates[0], dict): candidates = [c["text"] for c in candidates]
        interactive_annotate(candidates, args.output)

if __name__ == "__main__":
    main()