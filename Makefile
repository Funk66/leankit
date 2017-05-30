.PHONY: install test clean publish

install:
	if [ ! -d env ]; then virtualenv env; fi
	env/bin/pip install -r requirements.txt
	env/bin/python setup.py develop

test:
	nosetests --rednose

clean:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

publish:
	pip install wheel
	python setup.py sdist bdist_wheel upload
