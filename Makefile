
setup: clean venv
	venv/bin/python3 setup.py install
	
venv:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip wheel

clean:
	rm -Rf build dist *.egg-info __pycache__ venv
