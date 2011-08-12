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
import re
import subprocess
import socket
from urlparse import urlparse
from ConfigParser import ConfigParser
from distutils2.version import NormalizedVersion, IrrationalVersionError
from optparse import OptionParser

REPO_ROOT = 'https://hg.mozilla.org/services/'
PYTHON = sys.executable
PIP = os.path.join(os.path.dirname(PYTHON), 'pip')
PYPI = 'http://pypi.python.org/simple'
TAG_PREFIX = 'rpm-'
PYPI2RPM = os.path.join(os.path.dirname(PYTHON), 'pypi2rpm.py')


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
        print ('Could not find any rpm-* tag')
        sys.exit(0)

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

    print('Could not find a tag for channel %s' % channel)
    print('Make sure you have a %s-reqs.txt file' % channel)
    sys.exit(0)


def run(command):
    sb = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    stream_over = 0
    output = []
    while stream_over < 2:
        sys.stdout.write('.')
        sys.stdout.flush()
        out = sb.stdout.readline()
        if out.strip() == '':
            stream_over += 1
        else:
            output.append(out.strip())

        err = sb.stderr.readline()
        if err.strip() == '':
            stream_over += 1
        else:
            output.append(err.strip())

    code = sb.wait()
    if code != 0:
        print("%r failed with code %d" % (command, code))
        print('\n'.join(output))
        sys.exit(code)

    return code, '\n'.join(output)


def envname(name):
    return name.upper().replace('-', '_')


def has_changes():
    code, output = run('hg di')
    return output != ''


def update_cmd(project=None, channel="prod", specific_tag=False,
               force=False):
    if force:
        cmd = 'hg up -C'
    else:
        cmd = 'hg up -c'

    if not specific_tag:
        return '%s -r "%s"' % (cmd, get_channel_tag(channel))

    # looking for an environ with a specific tag or rev
    if project is not None:
        rev = os.environ.get(envname(project))
        if rev is not None:
            if not tag_exists(rev):
                print('Unknown tag or revision: %s' % rev)
                sys.exit(1)

            return '%s -r "%s"' % (cmd, rev)

    return cmd


_LEVEL = -1


def step(text):
    def _step(func):
        def __step(*args, **kw):
            global _LEVEL
            _LEVEL += 1
            fstep = step = _LEVEL * 2 * " "
            if _LEVEL > 0:
                fstep = '\n' + step
            sys.stdout.write(fstep + text % kw + ' ')
            sys.stdout.flush()
            try:
                res = func(*args, **kw)
                if _LEVEL > 0:
                    sys.stdout.write(step + '[ok]')
                else:
                    sys.stdout.write(step + '\n[done]')
                sys.stdout.flush()
                return res
            except:
                sys.stdout.write('[fail]')
                sys.stdout.flush()
                raise
            finally:
                _LEVEL -= 1
                if _LEVEL < 0:
                    print('')
        return __step
    return _step

_URL = re.compile('^Url: (.*?)$', re.M | re.DOTALL)


def is_meta_project():
    return get_spec_file() is None


def get_spec_file():
    for file_ in os.listdir(os.getcwd()):
        if os.path.splitext(file_)[-1] == '.spec':
            return os.path.join(os.getcwd(), file_)
    return None


def split_version(line):
    tokens = ['==', '>=', '<=', '>', '<', '!=']
    for token in tokens:
        if token in line:
            if token != '==':
                raise NotImplementedError(line)

            app, version = line.split(token, 1)
            return app.strip(), version.strip()
    return line.strip(), None


def get_project_name():
    if is_meta_project():
        return None
    spec_file = get_spec_file()
    if spec_file is not None:
        with open(spec_file) as f:
            data = f.read()
            name = _URL.findall(data)
            if len(name) == 1:
                return name[0].split('/')[-1]
    return None


def setup_pypi(pypi, extras=None, strict=False):
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


def get_options(extra_options=None):
    if extra_options is None:
        extra_options = []
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

    parser.add_option("-c", "--channel", dest="channel",
                      help="Channel to build",
                      default="last", type="choice",
                      choices=["prod", "dev", "stage", "last"])

    parser.add_option("-f", "--force", dest="force",
                      action="store_true", default=False,
                      help="Forces update")

    for optargs, optkw in extra_options:
        parser.add_option(*optargs, **optkw)

    options, args = parser.parse_args()

    # set pypi location
    setup_pypi(options.index, options.extras, options.strict)

    return options, args


def get_channel(options):
    channel = options.channel.lower()
    if channel == 'last':
        channel = get_last_channel()

    save_last_channel(channel)
    return channel


def save_last_channel(channel):
    with open('.channel', 'w') as f:
        f.write(channel)


def get_last_channel():
    if not os.path.exists('.channel'):
        return 'prod'
    with open('.channel') as f:
        return f.read()
