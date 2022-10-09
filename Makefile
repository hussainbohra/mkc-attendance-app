.PHONY: build clean venv test

# Try python36 first, if not, default what whatever python3 is available
PYTHON:=$(shell command -v python36 2>/dev/null)
PYTHON:=$(if $(PYTHON), $(PYTHON), python3)
NAME:=$(shell basename `pwd`)

venv:
	@echo Generating python virtual env with $(PYTHON)
	test -d venv || $(PYTHON) -m venv venv
	. venv/bin/activate; pip install --upgrade pip
	. venv/bin/activate; pip install wheel
	. venv/bin/activate; pip install -r requirements.txt

python-build: venv
	. venv/bin/activate; cd attendance; python setup.py bdist_wheel --universal

clean:
	@rm -rf venv
	@rm -rf attendance/build
	@rm -rf attendance/dist
