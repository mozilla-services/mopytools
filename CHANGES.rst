Changelog
---------

`
3.3 - 2012-06-29
================

- improve support for building git-hosted dependencies.
- error out if there are unpined dependencies in stage/prod reqs file.


3.2 - 2012-03-29
================

- make sure we can build without reqs files.

3.1 - 2012-03-26
================

- now allow internal dependencies to be without .spec

3.0 - 2012-03-23
================

- make sure we can use full urls with deps

2.9 - 2012-03-13
================

- pinned Distutils 2


2.8 - 2012-02-12
================

- skip lines that starts with '#' in requirement files
- added an option so we may exit the process immediatly
  when the exit code is not 0


2.7 - 2012-01-30
================

- tagging again - nothing new


2.6 - 2012-01-30
================

- make sure build_rpm checks the force option.


2.5 - 2012-01-30
================

- Broken release


2.4 - 2012-01-25
================

- sort release tags by version # instead of default (i.e. order of creation)

2.3 - 2012-01-17
================

- Fixed behavior on systems w/ hg diff tool installed
  (i.e. use 'hg diff' instead of 'hg di')
- Added support for TAG_PREFIX specified by an environment variable

2.2 - 2011-12-11
================

- activate the download cache on pypi2rpm

2.1 - 2011-12-11
================

- added the download cache option

2.0 - 2011-12-2
===============

- Make sure Git Submodules get updated

1.9 - 2011-11-30
================

- Raised the default timeout to 300s
- Make sure Pip uses the index/extras options

1.8 - 2011-11-24
================

- Make sure the req building occurs in a clean env,


1.7 - 2011-11-14
================

- Bug 700242 - add a verbose and timeout option


1.6 - 2011-11-03
================

- Bug 695232 - fixed the pinning


1.3 to 1.5 - 2011-10-06
=======================

- fixed small git-specific issues

1.2 - 2011-10-06
================

- Make the tool work with git.


1.1 - 2011-09-21
================

- use default and not tip when building

1.0 - 2011-09-09
================

- make sure we raise an error on bad number of arguments
- added a -r option to remove the destination dir for rpms


0.8 - 2011-08-19
================

- provide hgrc as a fallback


0.6 - 2011-08-16
================

- make sure the rpm trailing version is taken into account


0.5 - 2011-08-16
================

- added a buildrpm script
- new behavior for the buildapp script


0.4
===

- The build script now supports three options:

  -i: PyPI Simple index location (for mirroring)
  -e: extra location (for archives not present at PyPI)
  -s: flag to indicate that any URL that's not under PyPI or the extra
      location is disallowed during the fetching



