# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Sync Server
#
# The Initial Developer of the Original Code is the Mozilla Foundation.
# Portions created by the Initial Developer are Copyright (C) 2010
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Tarek Ziade (tarek@mozilla.com)
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
import os
import sys
import shutil

from mopytools.util import (timeout, get_options, step, get_channel,
                            split_version, get_spec_file, run,
                            PYTHON, PYPI2RPM, PYPI, has_changes)
from mopytools.build import get_environ_info, updating_repo
from mopytools.build_app import main as build_app


@timeout(4.0)
def main():
    """Build RPMs using PyPI2RPM and a pip-style req list"""
    extra_options = [[("-d", "--dist-dir"),
                      {"dest": "dist_dir",
                       "help": "Distributions directory",
                       "default": None}],
                     [("-r", "--remove-dir"),
                      {"dest": "remove_dir",
                       "action": "store_true",
                       "default": False,
                       "help": "Delete the target directory if it exists."}]]

    options, args = get_options(extra_options)

    if options.dist_dir is None:
        options.dist_dir = os.path.join(os.getcwd(), 'rpms')

    if os.path.exists(options.dist_dir):
        if options.remove_dir:
            # we want to clean up the dir before we start
            print('Removing existing directory.')
            shutil.rmtree(options.dist_dir)
            os.mkdir(options.dist_dir)
    else:
        os.mkdir(options.dist_dir)

    if len(args) > 0:
        deps = [dep.strip() for dep in args[0].split(',')]
    else:
        deps = []

    # building the app first (this can be quick, just to refresh the channel in
    # case it's needed)
    build_app()

    # get the channel
    channel = get_channel(options)
    print('The current channel is %s.' % channel)
    _buildrpms(deps, channel, options)


@step('Building RPMS')
def _buildrpms(deps, channel, options):
    # check the environ
    name, specific_tags = get_environ_info(deps)

    # updating the repo
    updating_repo(name, channel, specific_tags, options.force)

    # building the internal req RPMS
    build_core_rpm(deps, channel, specific_tags, options)

    # building the internal req RPMS
    build_deps_rpms(deps, channel, specific_tags, options)

    # building the external deps now
    build_external_deps_rpms(channel, options)


def _build_rpm(channel, options):
    if has_changes() and channel != 'dev' and not options.force:
        print('the code was changed, aborting!')
        sys.exit(0)

    # removing any build dir
    if os.path.exists('build'):
        shutil.rmtree('build')

    # where's the spec file ?
    spec_file = get_spec_file()

    if spec_file is None:
        return

    cmd_options = {'spec': spec_file, 'dist': options.dist_dir}

    # now running the cmd
    cmd = ("--command-packages=pypi2rpm.command bdist_rpm2 "
           "--spec-file=%(spec)s --dist-dir=%(dist)s")

    run('%s setup.py %s' % (PYTHON, cmd % cmd_options))


@step("Building the project's RPM")
def build_core_rpm(deps, channel, specific_tags, options):
    _build_rpm(channel, options)


@step("Building %(dep)s")
def build_dep_rpm(dep='', deps_dir='deps', channel='prod', options=None):
    target = os.path.join(deps_dir, dep)
    if not os.path.exists(target):
        print('You need to build your deps first.')
    os.chdir(target)
    _build_rpm(channel, options)


@step('Building RPMS for internal deps')
def build_deps_rpms(deps, channel, specific_tags, options):
    # for each dep, we want to get the channel's version
    location = os.getcwd()
    try:
        deps_dir = os.path.abspath(os.path.join(location, 'deps'))
        if not os.path.exists(deps_dir):
            print('You need to build your deps first.')
            sys.exit(0)

        for dep in deps:
            build_dep_rpm(dep=dep, deps_dir=deps_dir, channel=channel,
                          options=options)
    finally:
        os.chdir(location)


@step("Building %(project)s at version %(version)s")
def build_rpm(project=None, dist_dir='rpms', version=None, index=PYPI,
              download_cache=None):
    options = {'dist_dir': dist_dir, 'index': index}
    if version is None:
        cmd = "--index=%(index)s --dist-dir=%(dist_dir)s"
    else:
        options['version'] = version
        cmd = ("--index=%(index)s --dist-dir=%(dist_dir)s "
               "--version=%(version)s")

    if download_cache is not None:
        cmd += ' --download-cache=%s' % download_cache

    run('%s %s %s' % (PYPI2RPM, cmd % options, project))


@step('Building RPMS for external deps')
def build_external_deps_rpms(channel, options):
    # let's build the external reqs RPMS
    req_file = os.path.join(os.getcwd(), '%s-reqs.txt' % channel)
    if not os.path.exists(req_file):
        print("Can't find the req file for the %s channel." % channel)
        sys.exit(0)

    # we have a requirement file, we can go ahead and feed pypi2rpm with it
    with open(req_file) as f:
        for line in f.readlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            project, version = split_version(line)
            build_rpm(project=project, dist_dir=options.dist_dir,
                      version=version, index=options.index,
                      download_cache=options.download_cache)
