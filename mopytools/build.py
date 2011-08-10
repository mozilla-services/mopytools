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
import subprocess
from optparse import OptionParser
from ConfigParser import ConfigParser
import socket
from urlparse import urlparse

from pypi2rpm import main as pypi2rpm
from distutils2.version import NormalizedVersion, IrrationalVersionError


REPO_ROOT = 'https://hg.mozilla.org/services/'
PYTHON = sys.executable
PYPI = 'http://pypi.python.org/simple'
TAG_PREFIX = 'rpm-'


def _get_tags(prefix=TAG_PREFIX):
    sub = subprocess.Popen('hg tags', shell=True, stdout=subprocess.PIPE)
    return [tag_ for tag_ in
                [line.split()[0] for line in
                 sub.stdout.read().strip().split('\n')]
            if tag_.startswith(TAG_PREFIX)]


def tag_exists(tag):
    if tag == 'tip' or tag.isdigit():
        return True
    return tag in _get_tags()


def get_channel_tag(channel):
    if channel == 'dev':
        return 'tip'

    tags = _get_tags()

    if len(tags) == 0:
        raise ValueError('Could not find any rpm- tag')

    # looking for the latest channel tag
    #
    # - prod tags are final tags
    # - stage tags is the latest rc tags that is
    #   after the latest prod tag if any, or prod tag
    def is_prod(tag):
        try:
            return NormalizedVersion(version).is_final
        except IrrationalVersionError:
            return False

    def is_stage_or_prod(tag):
        try:
            NormalizedVersion(version)
            return True
        except IrrationalVersionError:
            return False

    if channel == "prod":
        selector = is_prod
    else:
        selector = is_stage_or_prod

    for tag in tags:
        version = tag[len(TAG_PREFIX):]
        if selector(version):
            return tag

    raise ValueError('Could not find a tag for channel %s' % channel)


def _run(command):
    print(command)
    subprocess.check_call(command.split())


def _envname(name):
    return name.upper().replace('-', '_')


def _update_cmd(project, channel="prod", specific_tag=False):
    if not specific_tag:
        return 'hg up -r "%s"' % get_channel_tag(channel)

    # looking for an environ with a specific tag or rev
    rev = os.environ.get(_envname(project))
    if rev is not None:
        if not tag_exists(rev):
            print('Unknown tag or revision: %s' % rev)
            sys.exit(1)

        return 'hg up -r "%s"' % rev
    return 'hg up'


def build_app(name, channel, deps, specific_tags):
    # building deps first
    build_deps(deps, channel, specific_tags)

    # if the current repo is a meta-repo, running tip on it
    if is_meta_project():
        specific_tags = False
        channel = "dev"

    # build the app now
    _run(_update_cmd(name, channel, specific_tags))
    _run('%s setup.py develop' % PYTHON)


def build_deps(deps, channel, specific_tags):
    """Will make sure dependencies are up-to-date"""
    location = os.getcwd()
    # do we want the latest tags ?
    try:
        deps_dir = os.path.abspath(os.path.join(location, 'deps'))
        if not os.path.exists(deps_dir):
            os.mkdir(deps_dir)

        for dep in deps:
            repo = REPO_ROOT + dep
            target = os.path.join(deps_dir, dep)
            if os.path.exists(target):
                os.chdir(target)
                _run('hg pull')
            else:
                _run('hg clone %s %s' % (repo, target))
                os.chdir(target)

            update_cmd = _update_cmd(dep, channel, specific_tags)
            _run(update_cmd)
            _run('%s setup.py develop' % PYTHON)
    finally:
        os.chdir(location)


def is_meta_project():
    for file_ in os.listdir('.'):
        if os.path.splitext(file_)[-1] == '.spec':
            return False
    return True


def _setup_pypi(pypi, extras=None, strict=False):
    # setup distutils.cfg
    import distutils
    location = os.path.dirname(distutils.__file__)
    cfg = os.path.join(location, 'distutils.cfg')
    if os.path.exists(cfg):
        os.remove(cfg)

    parser = ConfigParser()
    parser.read(cfg)

    if 'easy_install' not in parser.sections():
        parser.add_section('easy_install')

    parser.set('easy_install', 'index_url', pypi)
    allowed_hosts = [urlparse(pypi)[1]]

    if extras:
        parser.set('easy_install', 'find_links', extras)
        allowed_hosts.append(urlparse(extras)[1])

    if strict:
        parser.set('easy_install', 'allow_hosts', ','.join(allowed_hosts))

    with open(cfg, 'w') as cfg:
        parser.write(cfg)


def timeout(duration):
    def _timeout(func):
        def __timeout(*args, **kw):
            old = socket.getdefaulttimeout()
            socket.setdefaulttimeout(duration)
            try:
                return func(*args, **kw)
            finally:
                socket.setdefaulttimeout(old)
        return __timeout
    return _timeout


def _get_options(extra_options):
    parser = OptionParser()
    parser.add_option("-i", "--index", dest="index",
                      help="Pypi index", default=PYPI)

    parser.add_option("-e", "--extras", dest="extras",
                      help="Extra location for packages",
                      default=None)

    parser.add_option("-s", "--strict-index", dest="strict",
                      action="store_true",
                      help="Prevent browsing external websites",
                      default=False)

    parser.add_options("-c", "--channel", dest="channel",
                       help="Channel to build",
                       default="prod", type="choice",
                       choices=["prod", "dev", "stage"])

    for optargs, optkw in extra_options:
        parser.add_option(*optargs, **optkw)

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    # set pypi location
    _setup_pypi(options.index, options.extras, options.strict)

    return options, args


@timeout(4.0)
def buildapp():
    options, args = _get_options()
    project_name = args[0]

    if len(args) > 1:
        deps = [dep.strip() for dep in args[1].split(',')]
    else:
        deps = []

    # check the provided values in the environ
    #latest_tags = 'LATEST_TAGS' in os.environ
    if 'LATEST_TAGS' in os.environ:
        raise ValueError("LATEST_TAGS is deprecated, use channels")

    # get the channel
    channel = options.channel.lower()

    # if we have some tags in the environ, check that they are all defined
    projects = list(deps)

    # is the root a project itself or just a placeholder ?
    if not is_meta_project():
        projects.append(project_name)

    tags = {}
    missing = 0
    for project in projects:
        tag = _envname(project)
        if tag in os.environ:
            tags[tag] = os.environ[tag]
        else:
            tags[tag] = 'Not provided'
            missing += 1

    # we want all tag or no tag
    if missing > 0 and missing < len(projects):
        print("You did not specify all tags: ")
        for project, tag in tags.items():
            print('    %s: %s' % (project, tag))

        print("Also, consider using channels")
        sys.exit(1)

    specific_tags = missing == len(projects)
    build_app(project_name, channel, deps, specific_tags)


@timeout(4.0)
def buildrpms():
    """Build RPMs using PyPI2RPM and a pip-style req list"""
    def _split(line):
        tokens = ['==', '>=', '<=', '>', '<', '!=']
        for token in tokens:
            if token in line:
                if token != '==':
                    raise NotImplementedError(line)

                app, version = line.split(token, 1)
                return app.strip(), version.strip()
        return line.strip(), None

    distargs = ("-d", "--dist-dir")
    distoptions = {"dest": "dist_dir",
                   "help": "Distributions directory",
                   "default": None}
    options, args = _get_options([(distargs, distoptions)])
    req_file = args[0]
    # we have a requirement file, we can go ahead and feed pypi2rpm with it
    with open(req_file) as f:
        for line in f.readlines():
            project, version = _split(line)
            print("Building RPM for %s" % project)
            pypi2rpm(project, options.dist_dir, version, options.index)


if __name__ == '__main__':
    buildapp()
