install-dev:
	pip install -e ".[all,dev]"
	pre-commit install

lint:
	pre-commit run --all-files

test:
	pytest -xvs tests/

check: lint test
