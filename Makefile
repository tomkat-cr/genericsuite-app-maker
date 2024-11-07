# .DEFAULT_GOAL := local
# .PHONY: tests
SHELL := /bin/bash

# General Commands
help:
	cat Makefile

create_venv:
	sh scripts/run_app.sh create_venv

install: 
	sh scripts/run_app.sh install

requirements:
	sh scripts/run_app.sh requirements

test: install
	pytest tests --junitxml=report.xml

# Development Commands
lint: install
	prospector

types: install
	mypy .

coverage: install
	coverage run -m unittest discover tests;
	coverage report

format: install
	yapf -i *.py **/*.py **/**/*.py

format_check: install
	yapf --diff *.py **/*.py **/**/*.py

pycodestyle: install
	pycodestyle

qa: lint types tests format_check pycodestyle

# Application Specific Commands
run:
	sh scripts/run_app.sh run
