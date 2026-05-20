from __future__ import annotations

from datetime import date

import pytest
from backend.app.db.session import Base
from backend.app.models import KnowledgeArticle, Order, Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    db = TestingSession()
    db.add(
        Order(
            order_id="10042",
            customer_name="Alex Johnson",
            telegram_user_id="500042",
            email="alex@example.com",
            status="shipped",
            items=[{"name": "iPhone 15 Clear Case", "qty": 1, "price": 19.99}],
            total_amount=19.99,
            currency="USD",
            payment_status="paid",
            delivery_method="Standard",
            carrier="DHL",
            tracking_number="TG10042042",
            eta_date=date(2026, 5, 25),
        )
    )
    db.add(
        Product(
            product_id="P001",
            name="iPhone 15 Clear Case",
            category="phone cases",
            brand="TechGear",
            price=19.99,
            currency="USD",
            stock=12,
            attributes={"model": "iPhone 15", "color": "clear", "warranty": "6 months"},
            alternatives=["P003"],
        )
    )
    db.add(
        Product(
            product_id="P999",
            name="Wireless Headphones Demo",
            category="headphones",
            brand="DemoBrand",
            price=49.99,
            currency="USD",
            stock=0,
            attributes={"connection type": "Bluetooth", "warranty": "12 months"},
            alternatives=["P001"],
        )
    )
    articles = [
        ("en", "FAQ", "Delivery", "Standard delivery usually takes 2-5 business days."),
        ("en", "FAQ", "Payment", "TechGear Store accepts card payment and online links."),
        ("en", "FAQ", "Warranty", "Electronics have a 12 month warranty. Accessories have 6 months."),
        ("en", "FAQ", "Returns", "Returns are available within 14 days after receiving the order."),
        ("ru", "FAQ", "Доставка", "Стандартная доставка обычно занимает 2-5 рабочих дней."),
        ("ru", "FAQ", "Возврат", "Возврат возможен в течение 14 дней после получения заказа."),
    ]
    for lang, title, section, content in articles:
        db.add(
            KnowledgeArticle(
                source_file=f"test_{lang}.md",
                language=lang,
                title=title,
                section=section,
                content=content,
            )
        )
    db.commit()
    try:
        yield db
    finally:
        db.close()
