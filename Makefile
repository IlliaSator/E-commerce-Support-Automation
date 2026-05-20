.PHONY: setup test lint train evaluate seed demo up down logs

setup:
	python -m pip install -e backend[dev]
	python -m pip install -e bot[dev]
	python -m pip install -e dashboard

test:
	pytest backend/tests bot/tests -q

lint:
	ruff check backend bot dashboard scripts

train:
	python scripts/train_intent_classifier.py

evaluate:
	python scripts/evaluate_classifier.py
	python scripts/evaluate_ai_system.py

seed:
	python scripts/seed_db.py

demo:
	python scripts/demo_conversation.py

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f
