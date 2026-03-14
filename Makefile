.PHONY: install lint test cover

install:
	pipenv install --dev

lint:
	pipenv run python -m pylint switcher_client

test:
	pytest -v --cov=./switcher_client --cov-report xml --cov-config=.coveragerc

cover:
	coverage html