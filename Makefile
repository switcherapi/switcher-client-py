.PHONY: install install-test test cover build

install:
	pip install -r requirements.txt

install-test:
	pip install -r tests/requirements.txt

test:
	pytest -v --cov=./switcher_client --cov-report xml

cover:
	coverage html

build:
	python3 -m build