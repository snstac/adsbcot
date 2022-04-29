# ADSBCOT Makefile
#
# Source:: https://github.com/ampledata/adsbcot
# Author:: Greg Albrecht W2GMD <oss@undef.net>
# Copyright:: Copyright 2022 Greg Albrecht
# License:: Apache License, Version 2.0
#


.DEFAULT_GOAL := all


all: develop

install_requirements:
	pip install -r requirements_test.txt

develop:
	python setup.py develop

install_editable:
	pip install -e .

install_test:
	pip install -r requirements_test.txt

install:
	python setup.py install

uninstall:
	pip uninstall -y adsbcot

reinstall: uninstall install

clean:
	@rm -rf *.egg* build dist *.py[oc] */*.py[co] cover doctest_pypi.cfg \
		nosetests.xml pylint.log output.xml flake8.log tests.log \
		test-result.xml htmlcov fab.log .coverage __pycache__ \
		*/__pycache__

publish:
	python setup.py publish

pep8: 
	flake8 --max-complexity 12 --exit-zero --max-line-length 88 \
	--extend-ignore E203 *.py adsbcot/*.py

flake8: pep8

lint: 
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		-r n *.py adsbcot/*.py tests/*.py || exit 0

pylint: lint

test: lint pep8 pytest

checkmetadata:
	python setup.py check -s --restructuredtext

mypy:
	mypy --strict .

pytest:
	pytest --cov=adsbxcot

test: install_editable install_test pytest

black:
	black .