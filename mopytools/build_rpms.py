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
                            split_version)
from mopytools.build import get_environ_info, updating_repo
from pypi2rpm import main as pypi2rpm


@timeout(4.0)
def main():
    """Build RPMs using PyPI2RPM and a pip-style req list"""
    distargs = ("-d", "--dist-dir")
    distoptions = {"dest": "dist_dir",
                   "help": "Distributions directory",
                   "default": None}
    options, args = get_options([(distargs, distoptions)])

    if len(args) > 0:
        deps = [dep.strip() for dep in args[0].split(',')]
    else:
        deps = []

    # get the channel
    channel = get_channel(options)
    print('The current channel is %s.' % channel)
    _buildrpms(deps, channel, options)


@step('Building RPMS')
def _buildrpms(deps, channel, options):
    # check the environ
    name, specific_tags = get_environ_info(deps)

    # updating the repo
    updating_repo(name, channel, specific_tags)

    # building the internal req RPMS
    build_core_rpm(deps, channel, specific_tags)

    # building the internal req RPMS
    build_deps_rpms(deps, channel, specific_tags)

    # building the external deps now
    build_external_deps_rpms(channel, options)


@step("Building the project's RPM")
def build_core_rpm(deps, channel, specific_tags):
    pass


@step('Building RPMS for internal deps')
def build_deps_rpms(deps, channel, specific_tags):
    pass


@step("Building %(name)s")
def build_rpm(project, dist_dir, version, index, **kw):
    pypi2rpm(project, dist_dir, version, index)


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
            project, version = split_version(line)
            build_rpm(project, options.dist_dir, version, options.index,
                      name=project)
