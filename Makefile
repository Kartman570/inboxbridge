PYTHON ?= python3

test:
	$(PYTHON) -m unittest discover -s tests

lint:
	$(PYTHON) -m ruff check inboxbridge tests

coverage:
	$(PYTHON) -m coverage run --source=inboxbridge -m unittest discover -s tests
	$(PYTHON) -m coverage report -m
