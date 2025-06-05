.PHONY: install test cover build

install:
	pipenv install --dev

test:
	pytest -v --cov=./switcher_client --cov-report xml

cover:
	coverage html

build:
	python3 -m build