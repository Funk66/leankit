.PHONY: install test clean

install:
	if [ ! -d env ]; then python3 -m venv env; fi
	env/bin/python setup.py develop

test:
	python3 setup.py nosetests

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
