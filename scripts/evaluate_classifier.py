from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from scripts.train_intent_classifier import load_data


def main() -> None:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    texts, labels = load_data()
    train_x, test_x, train_y, test_y = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )
    model.fit(train_x, train_y)
    predicted = model.predict(test_x)
    report = classification_report(test_y, predicted, zero_division=0)
    print(report)
    print("Confusion matrix:")
    print(confusion_matrix(test_y, predicted, labels=sorted(set(labels))))

    out = ROOT / "data" / "training" / "classifier_evaluation.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
