APPNAME = server-devtools
DEPS =
VIRTUALENV = virtualenv
PKG = mopytools
NOSE = bin/nosetests -s --with-xunit
TESTS = $(PKG)/tests
PYTHON = bin/python
EZ = bin/easy_install
COVEROPTS = --cover-html --cover-html-dir=html --with-coverage --cover-package=$(PKG)
COVERAGE = bin/coverage
PYLINT = bin/pylint
FLAKE8 = bin/flake8

.PHONY: all build test flake8

all:	build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	$(PYTHON) build.py $(APPNAME) $(DEPS)
	$(EZ) nose
	$(EZ) pylint
	$(EZ) coverage


test:
	rm -f coverage.xml
	- $(COVERAGE) run --source=$(PKG) $(NOSE) $(TESTS); $(COVERAGE) xml
	rm -f pylint.txt
	- $(PYLINT) -f parseable --rcfile=pylintrc $(PKG) > pylint.txt

flake8:
	@echo; rm -rf tmp
	@echo; mkdir tmp
	@echo "Testing $(REPO)"
	@echo; hg clone -q $(REPO) tmp
	- $(FLAKE8) tmp
