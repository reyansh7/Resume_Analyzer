from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


@dataclass
class Record:
    text: str
    label: str
    source: str


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


def build_pipeline() -> Pipeline:
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
                    multi_class="auto",
                ),
            ),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Train baseline resume category model from CSV + PDF data")
    parser.add_argument("--csv", default="Resume/Resume.csv", help="Path to Resume CSV file")
    parser.add_argument("--pdf-root", default="data", help="Path to root folder containing class subfolders with PDFs")
    parser.add_argument("--max-pdfs", type=int, default=None, help="Optional cap on number of PDFs to parse")
    parser.add_argument("--test-size", type=float, default=0.2, help="Validation split ratio")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument("--model-out", default="saved_models/resume_classifier.joblib", help="Model output path")
    parser.add_argument("--metrics-out", default="saved_models/resume_classifier_metrics.json", help="Metrics output path")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    csv_path = (project_root / args.csv).resolve()
    pdf_root = (project_root / args.pdf_root).resolve()

    csv_records = load_csv_records(csv_path)
    pdf_records = load_pdf_records(pdf_root, args.max_pdfs)
    all_records = csv_records + pdf_records

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

    pipeline = build_pipeline()
    pipeline.fit(train_x, train_y)

    predictions = pipeline.predict(test_x)
    accuracy = float(accuracy_score(test_y, predictions))
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
                "total_records": len(all_records),
                "random_state": args.random_state,
            },
        },
        model_out,
    )

    metrics_payload = {
        "accuracy": accuracy,
        "classification_report": report,
        "train_size": len(train_x),
        "test_size": len(test_x),
        "csv_records": len(csv_records),
        "pdf_records": len(pdf_records),
        "total_records": len(all_records),
    }
    metrics_out.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")

    print(f"Training complete. Accuracy: {accuracy:.4f}")
    print(f"CSV records used: {len(csv_records)}")
    print(f"PDF records used: {len(pdf_records)}")
    print(f"Model saved to: {model_out}")
    print(f"Metrics saved to: {metrics_out}")


if __name__ == "__main__":
    main()
