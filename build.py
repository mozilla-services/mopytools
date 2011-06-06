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


REPO_ROOT = 'https://hg.mozilla.org/services/'
PYTHON = sys.executable
PYPI = 'http://pypi.python.org/simple'


def verify_tag(tag):
    if tag == 'tip' or tag.isdigit():
        return True
    sub = subprocess.Popen('hg tags', shell=True, stdout=subprocess.PIPE)
    tags = [tag_ for tag_ in
                [line.split()[0] for line in
                 sub.stdout.read().strip().split('\n')]
            if tag_.startswith('rpm-')]
    return tag in tags


def get_latest_tag():
    sub = subprocess.Popen('hg tags', shell=True, stdout=subprocess.PIPE)
    tags = [tag for tag in
                [line.split()[0] for line in
                 sub.stdout.read().strip().split('\n')]
            if tag.startswith('rpm-')]
    if len(tags) == 0:
        raise ValueError('Could not find a rpm tag')

    return tags[0]


def _run(command):
    print(command)
    os.system(command)


def _envname(name):
    return name.upper().replace('-', '_')


def _update_cmd(project, latest_tags=False):
    if latest_tags:
        return 'hg up -r "%s"' % get_latest_tag()
    else:

        # looking for an environ with a specific tag or rev
        rev = os.environ.get(_envname(project))
        if rev is not None:

            if not verify_tag(rev):
                print('Unknown tag or revision: %s' % rev)
                sys.exit(1)

            return 'hg up -r "%s"' % rev
        return 'hg up'


def build_app(name, latest_tags, deps):
    # building deps first
    build_deps(deps, latest_tags)

    # build the app now
    if not _has_spec():
        latest_tags = False

    _run(_update_cmd(name, latest_tags))
    _run('%s setup.py develop' % PYTHON)


def build_deps(deps, latest_tags):
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

            update_cmd = _update_cmd(dep, latest_tags)
            _run(update_cmd)
            _run('%s setup.py develop' % PYTHON)
    finally:
        os.chdir(location)


def _has_spec():
    specs = [file_ for file_ in os.listdir('.')
             if file_.endswith('.spec')]
    return len(specs)


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


@timeout(4.0)
def main():
    parser = OptionParser()
    parser.add_option("-i", "--index", dest="index",
                      help="Pypi index", default=PYPI)

    parser.add_option("-e", "--extras", dest="extras",
                      help="Extra location for packages",
                      default=None)

    parser.add_option("-s", "--strict-index", dest="strict",
                      action="store_true",
                      help="Prevent brwosing external websites",
                      default=False)

    options, args = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    project_name = args[0]

    if len(args) > 1:
        deps = [dep.strip() for dep in args[1].split(',')]
    else:
        deps = []

    # set pypi location
    _setup_pypi(options.index, options.extras, options.strict)

    # check the provided values in the environ
    latest_tags = 'LATEST_TAGS' in os.environ

    if not latest_tags:
        # if we have some tags in the environ, check that they are all defined
        projects = list(deps)

        # is the root a project itself or just a placeholder ?
        if _has_spec():
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
            sys.exit(1)

    build_app(project_name, latest_tags, deps)


if __name__ == '__main__':
    main()
