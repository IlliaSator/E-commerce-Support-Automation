FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY bot/pyproject.toml /app/bot/pyproject.toml
RUN pip install --no-cache-dir -e /app/bot

COPY bot /app/bot

CMD ["python", "-m", "bot.app.main"]
