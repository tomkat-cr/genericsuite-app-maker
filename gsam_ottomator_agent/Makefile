# .DEFAULT_GOAL := local
# .PHONY: tests
SHELL := /bin/bash

help:
	cat Makefile

stop:
	bash ./run_agent.sh stop

install: stop
	bash ./run_agent.sh install

run:
	bash ./run_agent.sh run

logs:
	bash ./run_agent.sh logs

requirements:
	bash ./run_agent.sh requirements

restart: stop run
