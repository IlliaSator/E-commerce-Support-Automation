from backend.app.models import Product
from sqlalchemy.orm import Session

STOP_WORDS = {"do", "you", "have", "with", "for", "the", "есть", "ли", "для"}


def search_products(db: Session, query: str, limit: int = 5) -> list[Product]:
    raw_tokens = [token.strip(" ?!.,").lower() for token in query.split() if token.strip()]
    tokens = [
        token
        for token in raw_tokens
        if token and token not in STOP_WORDS and (len(token) >= 3 or token.isdigit())
    ]
    if not tokens:
        return []
    products = db.query(Product).limit(500).all()

    def score(product: Product) -> tuple[int, int, int]:
        haystack = " ".join(
            [
                product.name.lower(),
                product.category.lower(),
                (product.brand or "").lower(),
                " ".join(str(v).lower() for v in product.attributes.values()),
            ]
        )
        token_hits = sum(1 for token in tokens if token in haystack)
        exact_name_bonus = 2 if query.lower().strip() in product.name.lower() else 0
        return (token_hits, exact_name_bonus, product.stock)

    scored = [(product, score(product)) for product in products]
    matched = [item for item in scored if item[1][0] > 0]
    return [product for product, _ in sorted(matched, key=lambda item: item[1], reverse=True)[:limit]]
