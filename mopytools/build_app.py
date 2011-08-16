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

from mopytools.util import (timeout, get_options, step, get_channel,
                            update_cmd, is_meta_project, PYTHON, run, PIP,
                            REPO_ROOT, has_changes)
from mopytools.build import get_environ_info, updating_repo


@timeout(4.0)
def main():
    options, args = get_options()

    if len(args) > 0:
        deps = [dep.strip() for dep in args[0].split(',')]
    else:
        deps = []

    # check the provided values in the environ
    if 'LATEST_TAGS' in os.environ:
        raise ValueError("LATEST_TAGS is deprecated, use channels")

    # get the channel
    channel = get_channel(options)
    print("The current channel is %s." % channel)

    _buildapp(channel, deps, options.force)


@step('Building the app')
def _buildapp(channel, deps, force):
    # check the environ
    name, specific_tags = get_environ_info(deps)

    # updating the repo
    updating_repo(name, channel, specific_tags, force)

    # building internal deps first
    build_deps(deps, channel, specific_tags)

    # building the external deps now
    build_external_deps(channel)

    # if the current repo is a meta-repo, running tip on it
    if is_meta_project():
        specific_tags = False
        channel = "dev"

    # build the app now
    build_core_app()


@step('Now building the app itself')
def build_core_app():
    run('%s setup.py develop' % PYTHON)


@step("Getting %(dep)s")
def build_dep(dep=None, deps_dir=None, channel='prod', specific_tags=False):
    repo = REPO_ROOT + dep
    target = os.path.join(deps_dir, dep)
    if os.path.exists(target):
        os.chdir(target)
        run('hg pull')
    else:
        run('hg clone %s %s' % (repo, target))
        os.chdir(target)

    if has_changes():
        if channel != 'dev':
            print('the code was changed, aborting!')
            sys.exit(0)
        else:
            print('Warning: the code was changed/')

    cmd = update_cmd(dep, channel, specific_tags)
    run(cmd)
    run('%s setup.py develop' % PYTHON)


@step('Building Services dependencies')
def build_deps(deps, channel, specific_tags):
    """Will make sure dependencies are up-to-date"""
    location = os.getcwd()
    # do we want the latest tags ?
    try:
        deps_dir = os.path.abspath(os.path.join(location, 'deps'))
        if not os.path.exists(deps_dir):
            os.mkdir(deps_dir)

        for dep in deps:
            build_dep(dep=dep, deps_dir=deps_dir, channel=channel,
                      specific_tags=specific_tags)
    finally:
        os.chdir(location)


@step('Building External dependencies')
def build_external_deps(channel):
    # looking for a req file
    reqname = '%s-reqs.txt' % channel
    filename = os.path.join(os.path.dirname(__file__), reqname)
    if not os.path.exists(filename):
        return
    run('%s -r %s' % (PIP, filename))
