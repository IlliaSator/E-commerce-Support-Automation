from __future__ import annotations

import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db.session import SessionLocal, init_db
from backend.app.models import KnowledgeArticle, Order, Product, SLAPolicy

SEED_DIR = ROOT / "data" / "seed"


def _clear_table(db, model) -> None:
    db.query(model).delete()


def seed_orders(db) -> None:
    with (SEED_DIR / "orders.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            db.add(
                Order(
                    order_id=row["order_id"],
                    customer_name=row["customer_name"],
                    telegram_user_id=row["telegram_user_id"] or None,
                    email=row["email"] or None,
                    status=row["status"],
                    items=json.loads(row["items"]),
                    total_amount=float(row["total_amount"]),
                    currency=row["currency"],
                    payment_status=row["payment_status"],
                    delivery_method=row["delivery_method"],
                    carrier=row["carrier"] or None,
                    tracking_number=row["tracking_number"] or None,
                    eta_date=date.fromisoformat(row["eta_date"]) if row["eta_date"] else None,
                )
            )


def seed_products(db) -> None:
    with (SEED_DIR / "products.csv").open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            db.add(
                Product(
                    product_id=row["product_id"],
                    name=row["name"],
                    category=row["category"],
                    brand=row["brand"] or None,
                    price=float(row["price"]),
                    currency=row["currency"],
                    stock=int(row["stock"]),
                    attributes=json.loads(row["attributes"]),
                    alternatives=json.loads(row["alternatives"]),
                )
            )


def _language_from_filename(path: Path) -> str:
    return "ru" if path.stem.endswith("_ru") else "en"


def _chunks_from_markdown(path: Path) -> list[tuple[str, str]]:
    chunks: list[tuple[str, str]] = []
    title = path.stem
    current_section = title
    buffer: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            title = line.removeprefix("# ").strip()
        elif line.startswith("## "):
            if buffer:
                chunks.append((current_section, "\n".join(buffer).strip()))
                buffer = []
            current_section = line.removeprefix("## ").strip()
        elif line.strip():
            buffer.append(line.strip())
    if buffer:
        chunks.append((current_section, "\n".join(buffer).strip()))
    return [(title, section, content) for section, content in chunks]


def seed_knowledge(db) -> None:
    for path in sorted(SEED_DIR.glob("*.md")):
        language = _language_from_filename(path)
        for title, section, content in _chunks_from_markdown(path):
            db.add(
                KnowledgeArticle(
                    source_file=str(path.relative_to(ROOT)).replace("\\", "/"),
                    language=language,
                    title=title,
                    section=section,
                    content=content,
                )
            )


def seed_sla_policies(db) -> None:
    rows = [
        ("urgent", 15, False, "Urgent complaints require a manager within 15 minutes."),
        ("high", 120, False, "Return, refund, and human manager cases require a response within 2 hours."),
        ("normal", 480, True, "Normal support tickets require response within 8 business hours."),
        ("low", 1440, False, "Low priority tickets require response within 24 hours."),
    ]
    for priority, minutes, business, description in rows:
        db.add(
            SLAPolicy(
                priority=priority,
                response_minutes=minutes,
                business_hours_only=business,
                description=description,
            )
        )


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        for model in [SLAPolicy, KnowledgeArticle, Product, Order]:
            _clear_table(db, model)
        seed_orders(db)
        seed_products(db)
        seed_knowledge(db)
        seed_sla_policies(db)
        db.commit()
        print("Seeded orders, products, knowledge articles, and SLA policies.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
