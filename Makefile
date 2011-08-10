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

# define a mirror here if wanted
PYPI = http://pypi.python.org/simple

# uncomment if you want to block any external url fetching
# besides PyPI 
#PYPISTRICT = YES

# uncomment and provide a location of extra packages
#PYPIEXTRAS = http://localhost

PYPIOPTIONS = -i $(PYPI)

ifdef PYPISTRICT
	PYPIOPTIONS += -s
endif

ifdef PYPIEXTRAS
	PYPIOPTIONS += -e $(PYPIEXTRAS)
endif


.PHONY: all build test flake8

all:	build

build:
	$(VIRTUALENV) --no-site-packages --distribute .
	$(PYTHON) build.py $(PYPIOPTIONS) $(APPNAME) $(DEPS) 
	$(EZ) nose
	$(EZ) pylint
	$(EZ) coverage

test:
	$(NOSE) $(TESTS)

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
	@cd tmp && make build
	@cd tmp && $(COVERAGE) run --source=$(PKG) $(NOSE) $(PKG)/tests
	- cd tmp && $(COVERAGE) report --omit=$(PKG)/tests/*
	@rm -rf tmp
