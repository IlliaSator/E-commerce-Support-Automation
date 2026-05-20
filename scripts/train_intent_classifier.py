from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DATA = ROOT / "data" / "seed" / "sample_messages.csv"
OUT = ROOT / "data" / "training" / "intent_classifier.joblib"


def load_data() -> tuple[list[str], list[str]]:
    texts: list[str] = []
    labels: list[str] = []
    with DATA.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            texts.append(row["message_text"])
            labels.append(row["intent"])
    return texts, labels


def main() -> None:
    texts, labels = load_data()
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(texts, labels)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT)
    print(f"Saved classifier to {OUT}")


if __name__ == "__main__":
    main()
