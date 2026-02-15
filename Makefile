.PHONY: install test cover

install:
	pipenv install --dev

test:
	pytest -v --cov=./switcher_client --cov-report xml --cov-config=.coveragerc

cover:
	coverage html