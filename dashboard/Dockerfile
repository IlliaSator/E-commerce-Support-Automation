FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY dashboard/pyproject.toml /app/dashboard/pyproject.toml
RUN pip install --no-cache-dir -e /app/dashboard

COPY dashboard /app/dashboard

CMD ["streamlit", "run", "dashboard/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
