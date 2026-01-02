.PHONY: install run test format lint

install:
	python -m pip install -U pip
	pip install -r requirements.txt

run:
	streamlit run app/Home.py

test:
	pytest

lint:
	ruff check .

format:
	ruff format .
