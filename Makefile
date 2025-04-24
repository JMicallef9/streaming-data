PYTHON_INTERPRETER = python
WD=$(shell pwd)
PYTHONPATH=${WD}
SHELL := /bin/bash
PIP:=pip

## Create python interpreter environment.
create-environment:
	@echo ">>> About to create environment."
	@echo ">>> check python3 version"
	( \
		$(PYTHON_INTERPRETER) --version; \
	)
	@echo ">>> Setting up VirtualEnv."
	( \
	    $(PIP) install -q virtualenv virtualenvwrapper; \
	    virtualenv venv --python=$(PYTHON_INTERPRETER); \
	)

# Define utility variable to help calling Python from the virtual environment
ACTIVATE_ENV := source venv/bin/activate

# Execute python related functionalities from within the project's environment
define execute_in_env
	$(ACTIVATE_ENV) && $1
endef

# Set Up
## Install bandit, flake8 and coverage
setupreq:
	$(call execute_in_env, $(PIP) install -r ./requirements.txt)

bandit:
	$(call execute_in_env, $(PIP) install bandit)

flake8:
	$(call execute_in_env, $(PIP) install flake8)

coverage:
	$(call execute_in_env, $(PIP) install coverage)


dev-setup: setupreq bandit flake8

## Run bandit
run-bandit:
	$(call execute_in_env, bandit -r ./src)

## Run flake8
run-flake8:
	$(call execute_in_env, flake8  ./src ./test)


## Run the unit tests
unit-test:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} coverage run --source=./src/ -m pytest -vv)
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} coverage report)

## Run all checks
run-checks: run-bandit run-flake8 unit-test