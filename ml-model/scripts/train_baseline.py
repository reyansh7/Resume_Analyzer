from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC


@dataclass
class Record:
    text: str
    label: str
    source: str


@dataclass
class CandidateResult:
    name: str
    cv_macro_f1: float
    cv_std: float


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def text_signature(text: str, token_limit: int = 220) -> str:
    normalized = normalize_text(text)
    tokens = re.findall(r"[a-z0-9+#./-]+", normalized)
    if not tokens:
        return ""

    token_freq: dict[str, int] = {}
    for token in tokens:
        token_freq[token] = token_freq.get(token, 0) + 1

    ranked_tokens = sorted(token_freq.items(), key=lambda item: (-item[1], item[0]))
    return " ".join(token for token, _ in ranked_tokens[:token_limit])


def load_csv_records(csv_path: Path) -> list[Record]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV dataset not found at: {csv_path}")

    dataframe = pd.read_csv(csv_path)
    required = {"Resume_str", "Category"}
    missing = required - set(dataframe.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    dataframe = dataframe.dropna(subset=["Resume_str", "Category"])
    dataframe["Resume_str"] = dataframe["Resume_str"].astype(str)
    dataframe["Category"] = dataframe["Category"].astype(str).str.strip().str.upper()

    records: list[Record] = []
    for _, row in dataframe.iterrows():
        text = row["Resume_str"].strip()
        label = row["Category"].strip()
        if text and label:
            records.append(Record(text=text, label=label, source="csv"))
    return records


def iter_pdf_files(data_root: Path) -> Iterable[tuple[Path, str]]:
    if not data_root.exists():
        return
    for category_dir in sorted(path for path in data_root.iterdir() if path.is_dir()):
        category = category_dir.name.strip().upper()
        for pdf_file in sorted(category_dir.glob("*.pdf")):
            yield pdf_file, category


def extract_pdf_text(pdf_path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        chunks: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                chunks.append(page_text)
        return "\n".join(chunks).strip()
    except Exception:
        return ""


def load_pdf_records(data_root: Path, max_pdfs: int | None) -> list[Record]:
    records: list[Record] = []
    count = 0
    for pdf_file, category in iter_pdf_files(data_root):
        if max_pdfs is not None and count >= max_pdfs:
            break
        text = extract_pdf_text(pdf_file)
        if text:
            records.append(Record(text=text, label=category, source="pdf"))
            count += 1
    return records


def clean_and_deduplicate_records(
    records: list[Record],
    min_text_chars: int,
    near_duplicate_mode: str,
) -> tuple[list[Record], dict[str, int]]:
    stats = {
        "removed_too_short": 0,
        "removed_exact_duplicates": 0,
        "removed_conflicting_labels": 0,
        "removed_near_duplicates": 0,
    }

    filtered: list[Record] = []
    for record in records:
        normalized = normalize_text(record.text)
        if len(normalized) < min_text_chars:
            stats["removed_too_short"] += 1
            continue
        filtered.append(Record(text=normalized, label=record.label.strip().upper(), source=record.source))

    exact_map: dict[str, list[Record]] = {}
    for record in filtered:
        exact_map.setdefault(record.text, []).append(record)

    deduped: list[Record] = []
    for text_key, bucket in exact_map.items():
        labels = {item.label for item in bucket}
        if len(labels) > 1:
            stats["removed_conflicting_labels"] += len(bucket)
            continue
        kept = bucket[0]
        deduped.append(Record(text=text_key, label=kept.label, source=kept.source))
        if len(bucket) > 1:
            stats["removed_exact_duplicates"] += len(bucket) - 1

    if near_duplicate_mode == "off":
        return deduped, stats

    by_label: dict[str, list[Record]] = {}
    for record in deduped:
        by_label.setdefault(record.label, []).append(record)

    near_deduped: list[Record] = []
    for label, bucket in by_label.items():
        seen_signatures: set[str] = set()
        for record in bucket:
            signature = text_signature(record.text)
            if not signature:
                continue
            if signature in seen_signatures:
                stats["removed_near_duplicates"] += 1
                continue
            seen_signatures.add(signature)
            near_deduped.append(Record(text=record.text, label=label, source=record.source))

    return near_deduped, stats


def get_label_counts(records: list[Record]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.label] = counts.get(record.label, 0) + 1
    return counts


def balance_records(
    records: list[Record],
    strategy: str,
    random_state: int,
    target_per_class: int | None,
) -> tuple[list[Record], dict[str, int]]:
    counts = get_label_counts(records)
    if not counts:
        return records, {"target_per_class": 0}

    if strategy == "none":
        return records, {"target_per_class": 0}

    if target_per_class is None:
        sorted_counts = sorted(counts.values())
        median_index = len(sorted_counts) // 2
        target_per_class = sorted_counts[median_index]

    rng = random.Random(random_state)
    by_label: dict[str, list[Record]] = {}
    for record in records:
        by_label.setdefault(record.label, []).append(record)

    balanced: list[Record] = []
    for label in sorted(by_label):
        bucket = by_label[label]
        bucket_copy = bucket[:]
        rng.shuffle(bucket_copy)

        if strategy == "downsample":
            keep_n = min(len(bucket_copy), target_per_class)
            balanced.extend(bucket_copy[:keep_n])
            continue

        if strategy == "upsample":
            if len(bucket_copy) >= target_per_class:
                balanced.extend(bucket_copy)
            else:
                balanced.extend(bucket_copy)
                needed = target_per_class - len(bucket_copy)
                balanced.extend(rng.choices(bucket_copy, k=needed))
            continue

        keep_n = target_per_class
        if len(bucket_copy) > keep_n:
            balanced.extend(bucket_copy[:keep_n])
        elif len(bucket_copy) < keep_n:
            balanced.extend(bucket_copy)
            needed = keep_n - len(bucket_copy)
            balanced.extend(rng.choices(bucket_copy, k=needed))
        else:
            balanced.extend(bucket_copy)

    return balanced, {"target_per_class": target_per_class}


def build_baseline_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=120_000,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    n_jobs=None,
                ),
            ),
        ]
    )


def build_search_candidates(random_state: int) -> list[tuple[str, Pipeline]]:
    candidates: list[tuple[str, Pipeline]] = []

    word_vectorizers = [
        (
            "word_12",
            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                analyzer="word",
                ngram_range=(1, 2),
                min_df=2,
                max_features=180_000,
                sublinear_tf=True,
            ),
        ),
        (
            "word_13",
            TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                analyzer="word",
                ngram_range=(1, 3),
                min_df=2,
                max_features=220_000,
                sublinear_tf=True,
            ),
        ),
    ]

    char_vectorizers = [
        (
            "char_35",
            TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=2,
                max_features=250_000,
                sublinear_tf=True,
            ),
        ),
        (
            "char_46",
            TfidfVectorizer(
                lowercase=True,
                analyzer="char_wb",
                ngram_range=(4, 6),
                min_df=2,
                max_features=250_000,
                sublinear_tf=True,
            ),
        ),
    ]

    c_values = [0.5, 1.0, 2.0]

    for vec_name, vectorizer in word_vectorizers + char_vectorizers:
        for c_value in c_values:
            candidates.append(
                (
                    f"linear_svc__{vec_name}__c{c_value}",
                    Pipeline(
                        steps=[
                            ("tfidf", vectorizer),
                            (
                                "clf",
                                LinearSVC(
                                    C=c_value,
                                    class_weight="balanced",
                                    random_state=random_state,
                                    max_iter=7000,
                                ),
                            ),
                        ]
                    ),
                )
            )

    union_pairs = [
        ("word12_char35", word_vectorizers[0][1], char_vectorizers[0][1]),
        ("word13_char46", word_vectorizers[1][1], char_vectorizers[1][1]),
    ]

    for pair_name, word_vectorizer, char_vectorizer in union_pairs:
        for c_value in c_values:
            candidates.append(
                (
                    f"linear_svc__{pair_name}__c{c_value}",
                    Pipeline(
                        steps=[
                            (
                                "features",
                                FeatureUnion(
                                    transformer_list=[
                                        ("word", word_vectorizer),
                                        ("char", char_vectorizer),
                                    ]
                                ),
                            ),
                            (
                                "clf",
                                LinearSVC(
                                    C=c_value,
                                    class_weight="balanced",
                                    random_state=random_state,
                                    max_iter=7000,
                                ),
                            ),
                        ]
                    ),
                )
            )

    return candidates


def select_best_pipeline(
    train_x: list[str],
    train_y: list[str],
    random_state: int,
    cv_folds: int,
    max_candidates: int,
) -> tuple[Pipeline, str, list[CandidateResult]]:
    candidates = build_search_candidates(random_state)
    if max_candidates > 0:
        candidates = candidates[:max_candidates]

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)

    best_pipeline: Pipeline | None = None
    best_name = ""
    best_score = float("-inf")
    search_results: list[CandidateResult] = []

    for name, candidate_pipeline in candidates:
        scores = cross_val_score(
            candidate_pipeline,
            train_x,
            train_y,
            scoring="f1_macro",
            cv=cv,
            n_jobs=1,
        )
        mean_score = float(scores.mean())
        std_score = float(scores.std())
        search_results.append(CandidateResult(name=name, cv_macro_f1=mean_score, cv_std=std_score))

        if mean_score > best_score:
            best_score = mean_score
            best_name = name
            best_pipeline = candidate_pipeline

    if best_pipeline is None:
        raise RuntimeError("No model candidates were evaluated.")

    search_results.sort(key=lambda result: result.cv_macro_f1, reverse=True)
    return best_pipeline, best_name, search_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline resume category model from CSV + PDF data")
    parser.add_argument("--csv", default="Resume/Resume.csv", help="Path to Resume CSV file")
    parser.add_argument("--pdf-root", default="data", help="Path to root folder containing class subfolders with PDFs")
    parser.add_argument("--max-pdfs", type=int, default=None, help="Optional cap on number of PDFs to parse")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--model-search",
        choices=["off", "linear-svc"],
        default="linear-svc",
        help="Classifier selection strategy run on cleaned/balanced training set",
    )
    parser.add_argument(
        "--cv-folds",
        type=int,
        default=3,
        help="Number of CV folds used during model search",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=12,
        help="Maximum number of classifier candidates to evaluate in model search",
    )
    parser.add_argument(
        "--balance-strategy",
        choices=["none", "downsample", "upsample", "hybrid"],
        default="hybrid",
        help="Class balancing strategy applied before train/test split",
    )
    parser.add_argument(
        "--target-per-class",
        type=int,
        default=None,
        help="Optional class target count for balancing. Defaults to median class size.",
    )
    parser.add_argument(
        "--min-text-chars",
        type=int,
        default=120,
        help="Minimum normalized text length to keep a sample",
    )
    parser.add_argument(
        "--near-duplicate-mode",
        choices=["off", "signature"],
        default="signature",
        help="Near-duplicate filtering mode applied within each class",
    )
    parser.add_argument("--model-out", default="saved_models/resume_classifier.joblib", help="Model output path")
    parser.add_argument("--metrics-out", default="saved_models/resume_classifier_metrics.json", help="Metrics output path")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    csv_path = (project_root / args.csv).resolve()
    pdf_root = (project_root / args.pdf_root).resolve()

    csv_records = load_csv_records(csv_path)
    pdf_records = load_pdf_records(pdf_root, args.max_pdfs)
    all_records_raw = csv_records + pdf_records

    all_records_clean, clean_stats = clean_and_deduplicate_records(
        all_records_raw,
        min_text_chars=args.min_text_chars,
        near_duplicate_mode=args.near_duplicate_mode,
    )
    all_records, balance_meta = balance_records(
        all_records_clean,
        strategy=args.balance_strategy,
        random_state=args.random_state,
        target_per_class=args.target_per_class,
    )

    if len(all_records) < 100:
        raise ValueError(
            f"Not enough training records. Found {len(all_records)} total records from CSV+PDF sources."
        )

    texts = [record.text for record in all_records]
    labels = [record.label for record in all_records]

    train_x, test_x, train_y, test_y = train_test_split(
        texts,
        labels,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=labels,
    )

    selected_model_name = "baseline_logreg"
    search_results: list[CandidateResult] = []

    if args.model_search == "linear-svc":
        pipeline, selected_model_name, search_results = select_best_pipeline(
            train_x=train_x,
            train_y=train_y,
            random_state=args.random_state,
            cv_folds=args.cv_folds,
            max_candidates=args.max_candidates,
        )
    else:
        pipeline = build_baseline_pipeline()

    pipeline.fit(train_x, train_y)

    predictions = pipeline.predict(test_x)
    accuracy = float(accuracy_score(test_y, predictions))
    balanced_accuracy = float(balanced_accuracy_score(test_y, predictions))
    macro_f1 = float(f1_score(test_y, predictions, average="macro", zero_division=0))
    report = classification_report(test_y, predictions, output_dict=True, zero_division=0)

    model_out = (project_root / args.model_out).resolve()
    metrics_out = (project_root / args.metrics_out).resolve()
    model_out.parent.mkdir(parents=True, exist_ok=True)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "pipeline": pipeline,
            "labels": sorted(set(labels)),
            "metadata": {
                "train_size": len(train_x),
                "test_size": len(test_x),
                "csv_records": len(csv_records),
                "pdf_records": len(pdf_records),
                "raw_total_records": len(all_records_raw),
                "clean_total_records": len(all_records_clean),
                "balanced_total_records": len(all_records),
                "random_state": args.random_state,
                "test_size_ratio": args.test_size,
                "stratified_split": True,
                "balance_strategy": args.balance_strategy,
                "target_per_class": balance_meta["target_per_class"],
                "min_text_chars": args.min_text_chars,
                "near_duplicate_mode": args.near_duplicate_mode,
                "model_search": args.model_search,
                "selected_model": selected_model_name,
                "cv_folds": args.cv_folds,
                "max_candidates": args.max_candidates,
                "search_results": [
                    {
                        "name": result.name,
                        "cv_macro_f1": result.cv_macro_f1,
                        "cv_std": result.cv_std,
                    }
                    for result in search_results
                ],
                "cleaning": clean_stats,
            },
        },
        model_out,
    )

    metrics_payload = {
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "macro_f1": macro_f1,
        "classification_report": report,
        "train_size": len(train_x),
        "test_size": len(test_x),
        "csv_records": len(csv_records),
        "pdf_records": len(pdf_records),
        "raw_total_records": len(all_records_raw),
        "clean_total_records": len(all_records_clean),
        "balanced_total_records": len(all_records),
        "random_state": args.random_state,
        "test_size_ratio": args.test_size,
        "stratified_split": True,
        "balance_strategy": args.balance_strategy,
        "target_per_class": balance_meta["target_per_class"],
        "min_text_chars": args.min_text_chars,
        "near_duplicate_mode": args.near_duplicate_mode,
        "model_search": args.model_search,
        "selected_model": selected_model_name,
        "cv_folds": args.cv_folds,
        "max_candidates": args.max_candidates,
        "search_results": [
            {
                "name": result.name,
                "cv_macro_f1": result.cv_macro_f1,
                "cv_std": result.cv_std,
            }
            for result in search_results
        ],
        "cleaning": clean_stats,
        "class_counts_before": get_label_counts(all_records_clean),
        "class_counts_after": get_label_counts(all_records),
    }
    metrics_out.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    print(f"Training complete. Accuracy: {accuracy:.4f}")
    print(f"Balanced accuracy: {balanced_accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"CSV records used: {len(csv_records)}")
    print(f"PDF records used: {len(pdf_records)}")
    print(f"Raw records: {len(all_records_raw)}")
    print(f"After cleaning: {len(all_records_clean)}")
    print(f"After balancing: {len(all_records)}")
    print(f"Selected model: {selected_model_name}")
    if search_results:
        top_result = search_results[0]
        print(f"Best CV macro F1: {top_result.cv_macro_f1:.4f} (+/- {top_result.cv_std:.4f})")
    print(f"Model saved to: {model_out}")
    print(f"Metrics saved to: {metrics_out}")


if __name__ == "__main__":
    main()
