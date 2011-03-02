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
	@$(VIRTUALENV) --no-site-packages --distribute . > /dev/null
	@$(PYTHON) build.py $(APPNAME) $(DEPS) > /dev/null
	@$(EZ) nose > /dev/null
	@rm -rf tmp
	@mkdir tmp
	@echo "Testing $(REPO)"
	@hg clone -q $(REPO) tmp
	- $(FLAKE8) tmp 
	@rm -rf tmp

coverage:
	@$(VIRTUALENV) --no-site-packages --distribute . > /dev/null
	@$(PYTHON) build.py $(APPNAME) $(DEPS) > /dev/null
	@$(EZ) nose > /dev/null
	@rm -rf tmp
	@mkdir tmp
	@echo "Coverage of $(REPO)"
	@hg clone -q $(REPO) tmp 
	cd tmp && make build > /dev/null  2> /dev/null
	cd tmp && $(COVERAGE) run --source=$(PKG) $(NOSE) $(PKG)/tests > /dev/null 2> /dev/null
	- cd tmp && $(COVERAGE) report --omit=$(PKG)/tests/*
	rm -rf tmp
