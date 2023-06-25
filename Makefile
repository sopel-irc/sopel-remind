.PHONY: qa quality test coverages coverage_report coverage_html pylint pyroma

quality:
	isort sopel_remind
	flake8 sopel_remind
	isort tests
	flake8 tests/*
	mypy sopel_remind

test:
	coverage run -m pytest -v .

coverage_report:
	coverage report

coverage_html:
	coverage html

coverages: coverage_report coverage_html

pylint:
	pylint sopel_remind

pyroma:
	pyroma .

qa: quality test coverages pylint pyroma

.PHONY: develop build

develop:
	pip install -r requirements.txt
	python setup.py develop

build:
	rm -rf build/ dist/
	python -m build --sdist --wheel --outdir dist/ .
