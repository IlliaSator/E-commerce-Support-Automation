FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
RUN pip install --no-cache-dir -e /app/backend

COPY backend /app/backend
COPY data /app/data
COPY scripts /app/scripts

WORKDIR /app

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
