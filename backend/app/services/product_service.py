from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.models import Product


def search_products(db: Session, query: str, limit: int = 5) -> list[Product]:
    tokens = [token.strip().lower() for token in query.split() if token.strip()]
    if not tokens:
        return []
    filters = []
    for token in tokens:
        like = f"%{token}%"
        filters.append(Product.name.ilike(like))
        filters.append(Product.category.ilike(like))
        filters.append(Product.brand.ilike(like))
    products = db.query(Product).filter(or_(*filters)).limit(25).all()

    def score(product: Product) -> tuple[int, int]:
        haystack = " ".join(
            [
                product.name.lower(),
                product.category.lower(),
                (product.brand or "").lower(),
                " ".join(str(v).lower() for v in product.attributes.values()),
            ]
        )
        return (sum(1 for token in tokens if token in haystack), product.stock)

    return sorted(products, key=score, reverse=True)[:limit]
