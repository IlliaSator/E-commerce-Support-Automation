from sqlalchemy.orm import Session

from backend.app.models import Customer


def get_or_create_customer(
    db: Session,
    external_id: str | None,
    telegram_user_id: str | None = None,
    username: str | None = None,
    language: str | None = None,
) -> Customer:
    key = external_id or telegram_user_id or "anonymous"
    customer = db.query(Customer).filter(Customer.external_id == key).one_or_none()
    if customer:
        if telegram_user_id and not customer.telegram_user_id:
            customer.telegram_user_id = telegram_user_id
        if username and not customer.username:
            customer.username = username
        return customer

    customer = Customer(
        external_id=key,
        telegram_user_id=telegram_user_id,
        username=username,
        language=language,
    )
    db.add(customer)
    db.flush()
    return customer
