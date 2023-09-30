all: clean venv setup

setup:
	venv/bin/python3 setup.py install

venv:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip wheel

clean:
	rm -Rf build dist *.egg-info __pycache__ venv *.gz .vscode .pytest_cache tests/__pycache__

.PHONY: all setup venv clean