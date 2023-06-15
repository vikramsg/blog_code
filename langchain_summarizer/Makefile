CITY ?=

define REQUIRE
  $(if $(value $(1)),,$(error $(1) is required))
endef

.PHONY: install test lint check run 

help:
	@echo "install - install dependencies with poetry"
	@echo "lint - run linter and checks"
	@echo "summary - Summarizes a city page from Wikipedia. Only for gpt 3.5 and Pythia"

check:
	./static_checks.sh

lint:
	./linter.sh
	
install:
	poetry install --no-root
	poetry shell

summary: 
	poetry run python -m src.summarize