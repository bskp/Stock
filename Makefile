VIRTUALENV="virtualenv"
virtualenv_dir="env"

setup: venv deps

venv:
	test -d $(virtualenv_dir) || ($(VIRTUALENV) $(virtualenv_dir) || true)
	. $(virtualenv_dir)/bin/activate

deps:
	pip install -Ur requirements.txt

keys:
	./src/application/generate_keys.py

